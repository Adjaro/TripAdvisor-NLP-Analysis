import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import MarkerCluster
import branca.colormap as cm
from manager import read_restaurant, read_location, get_db
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data
def load_data(_db) -> pd.DataFrame:
    """Load and merge restaurant data with caching"""
    try:
        return pd.merge(
            read_restaurant(db=_db),
            read_location(db=_db),
            on='id_location'
        )
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame()

def makefiltre(df: pd.DataFrame, colonne: str) -> List[str]:
    """Create filter options from column data"""
    try:
        return sorted(list(set([
            item.strip() 
            for items in df[colonne].dropna() 
            for item in items.split(',')
        ])))
    except Exception as e:
        logger.error(f"Error creating filter for {colonne}: {e}")
        return []

def updateDf(df: pd.DataFrame, colonne: str, filtres: List[str]) -> pd.DataFrame:
    """Apply filters to dataframe"""
    if not filtres:
        return df
    return df[df[colonne].str.contains('|'.join(filtres), na=False)]

def create_map(restaurants: pd.DataFrame) -> folium.Map:
    """Create Folium map with restaurant markers"""
    try:
        map_center = [
            restaurants["latitude"].mean(),
            restaurants["longitude"].mean()
        ]
        
        m = folium.Map(location=map_center, zoom_start=13)
        marker_cluster = MarkerCluster().add_to(m)
        
        colormap = cm.LinearColormap(
            colors=['red', 'orange', 'yellow', 'green'],
            vmin=restaurants['note_globale'].min(),
            vmax=restaurants['note_globale'].max()
        )
        
        for _, rest in restaurants.iterrows():
            html = f"""
                <div style='min-width:200px'>
                    <h4>{rest['nom']}</h4>
                    <p>Note: {rest['note_globale']:.1f}/5</p>
                    <p>{rest['adresse']}</p>
                </div>
            """
            
            folium.Marker(
                location=[rest["latitude"], rest["longitude"]],
                popup=folium.Popup(html, max_width=300),
                tooltip=rest["nom"],
                icon=folium.Icon(
                    color=colormap(rest['note_globale']),
                    icon="utensils",
                    prefix="fa"
                )
            ).add_to(marker_cluster)
        
        colormap.add_to(m)
        colormap.caption = 'Note moyenne'
        return m
        
    except Exception as e:
        logger.error(f"Error creating map: {e}")
        return None

def show_restaurant_details(restaurant: pd.Series):
    """Display restaurant details card"""
    st.markdown(
        f"""
        <div style='
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        '>
            <h2>{restaurant['nom']}</h2>
            <div style='display: flex; align-items: center; gap: 10px; margin: 10px 0;'>
                <span style='font-size: 1.2em'>⭐ {restaurant['note_globale']:.1f}/5</span>
            </div>
            <p>📍 {restaurant['adresse']}</p>
            <hr>
            <p><strong>Cuisines:</strong> {restaurant['type_cuisines']}</p>
            <p><strong>Services:</strong> {restaurant['fonctionnalites']}</p>
            <p><strong>Infos pratiques:</strong> {restaurant['infos_pratiques']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def show():
    st.title("📍 Carte des Restaurants")
    
    try:
        with st.spinner("Chargement des données..."):
            db = next(get_db())
            restaurants = load_data(db)
            
            if restaurants.empty:
                st.error("Aucune donnée disponible.")
                return
            
            # Filters
            st.subheader("🔎 Filtres")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cuisine_filters = st.multiselect(
                    'Cuisine 🍳',
                    makefiltre(restaurants, 'type_cuisines')
                )
                
            with col2:
                repas_filters = st.multiselect(
                    'Repas 🍽️',
                    makefiltre(restaurants, 'repas')
                )
                
            with col3:
                fonctionnalites_filters = st.multiselect(
                    'Services ⚙️',
                    makefiltre(restaurants, 'fonctionnalites')
                )
                
            with col4:
                note_min = st.slider(
                    'Note minimale ⭐',
                    min_value=0.0,
                    max_value=5.0,
                    value=0.0,
                    step=0.5
                )
            
            # Apply filters
            filtered_restaurants = restaurants.copy()
            filtered_restaurants = updateDf(filtered_restaurants, 'type_cuisines', cuisine_filters)
            filtered_restaurants = updateDf(filtered_restaurants, 'repas', repas_filters)
            filtered_restaurants = updateDf(filtered_restaurants, 'fonctionnalites', fonctionnalites_filters)
            filtered_restaurants = filtered_restaurants[filtered_restaurants['note_globale'] >= note_min]
            
            # Results count
            st.markdown(f"### {len(filtered_restaurants)} restaurants trouvés")
            
            # Map and details layout
            map_col, details_col = st.columns([5, 4], gap="small")
            
            with map_col:
                if filtered_restaurants.empty:
                    st.warning("Aucun restaurant ne correspond aux filtres.")
                else:
                    folium_map = create_map(filtered_restaurants)
                    if folium_map:
                        map_data = st_folium(
                            folium_map,
                            width=900,
                            height=600,
                            returned_objects=["last_clicked"]
                        )
                        
                        if map_data and map_data.get("last_clicked"):
                            clicked = map_data["last_clicked"]
                            selected = filtered_restaurants[
                                (filtered_restaurants["latitude"] == clicked["lat"]) &
                                (filtered_restaurants["longitude"] == clicked["lng"])
                            ]
                            
                            if not selected.empty:
                                with details_col:
                                    show_restaurant_details(selected.iloc[0])
                            
            if "last_clicked" not in st.session_state:
                with details_col:
                    st.info("👆 Cliquez sur un restaurant pour voir les détails")
                    
    except Exception as e:
        logger.error(f"Error in show(): {e}")
        st.error("Une erreur est survenue lors du chargement des données.")
    finally:
        if 'db' in locals():
            db.close()
