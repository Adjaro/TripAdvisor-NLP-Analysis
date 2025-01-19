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
def load_css():
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .title-container {
            background: #F0F2F6;
            padding: 2rem;
            border-radius: 10px;
            color: linear-gradient(to right, #1e3c72, #2a5298);
            margin-bottom: 2rem;
        }
        .feature-card {
            background: #F0F2F6;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        .team-card {
            text-align: justify;
            background: #F0F2F6;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stat-card {
            background: #F0F2F6;
            padding: 1rem;
            border-radius: 8px;
            text-align: justify;
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data(_db) -> pd.DataFrame:
    """Load and merge restaurant data with caching"""
    try:
        restaurants = read_restaurant(db=_db)
        locations = read_location(db=_db)
        return pd.merge(restaurants, locations, on='id_location')
    except Exception as e:
        logger.error(f"Data loading error: {e}")
        return pd.DataFrame()

def create_map(restaurants: pd.DataFrame) -> folium.Map:
    """Create Folium map with restaurant markers"""
    try:
        map_center = [restaurants["latitude"].mean(), restaurants["longitude"].mean()]
        m = folium.Map(location=map_center, zoom_start=13)
        # cluster = MarkerCluster().add_to(m)
        
        for _, rest in restaurants.iterrows():
            folium.Marker(
                location=[rest["latitude"], rest["longitude"]],
                popup=rest["nom"],
                icon=folium.Icon(color="red", icon="cutlery", prefix="fa"),
                tooltip=rest["nom"]
            ).add_to(m)
        
        return m
    except Exception as e:
        logger.error(f"Map creation error: {e}")
        return None

def show():
    # st.title("📍 Carte des Restaurants")
    load_css()

    # Hero Section
    st.markdown("""
        <div class='title-container'>
            <h1>📍 Carte des Restaurants</h1>
        </div>
    """, unsafe_allow_html=True)
    try:
        # Load data
        with st.spinner("Chargement des données..."):
            db = next(get_db())
            restaurants = load_data(db)
            
            if restaurants.empty:
                st.error("Aucune donnée disponible")
                return

        # Filters section
        # st.subheader("🔎 Filtres")
        col1, col2, col3, col4 = st.columns(4)
        
        filters = {
            'type_cuisines': col1.multiselect(
                'Cuisine 🍳',
                options=sorted(set(item.strip() for items in restaurants['type_cuisines'].dropna() for item in items.split(',')))
            ),
            'repas': col2.multiselect(
                'Repas 🍽️',
                options=sorted(set(item.strip() for items in restaurants['repas'].dropna() for item in items.split(',')))
            ),
            'fonctionnalites': col3.multiselect(
                'Services ⚙️',
                options=sorted(set(item.strip() for items in restaurants['fonctionnalites'].dropna() for item in items.split(',')))
            ),
            'note_min': col4.slider(
                'Note minimale ⭐',
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.5
            )
        }

        # Apply filters
        filtered_restaurants = restaurants.copy()
        for key, value in filters.items():
            if value and key != 'note_min':
                filtered_restaurants = filtered_restaurants[
                    filtered_restaurants[key].str.contains('|'.join(value), na=False)
                ]
            elif key == 'note_min' and value > 0:
                filtered_restaurants = filtered_restaurants[
                    filtered_restaurants['note_globale'] >= value
                ]

        st.markdown(f"### 📊 {len(filtered_restaurants)} restaurants trouvés")

        # Layout: Details left, Map right
        details_col, map_col = st.columns([1, 2])

        # Map section
        with map_col:
            if filtered_restaurants.empty:
                st.warning("Aucun restaurant ne correspond aux filtres")
            else:
                map = create_map(filtered_restaurants)
                if map:
                    map_data = st_folium(
                        map,
                        height=600,
                        width="100%",
                        key="map",
                        returned_objects=["last_clicked", "last_object_clicked"]
                    )

        # Details section
        with details_col:
            try:
                if map_data and "last_object_clicked" in map_data:
                    clicked = map_data["last_object_clicked"]
                    if clicked:
                        restaurant = filtered_restaurants[
                            (filtered_restaurants["latitude"].round(6) == round(clicked["lat"], 6)) &
                            (filtered_restaurants["longitude"].round(6) == round(clicked["lng"], 6))
                        ].iloc[0]
                        
                        st.markdown(f"""
                            <div style='
                                background-color: white; 
                                padding: 20px; 
                                border-radius: 10px; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                height: 600px;
                                overflow-y: auto;
                            '>
                                <h2 style='color: #1E1E1E;'>{restaurant['nom']}</h2>
                                <p><strong>⭐ Note:</strong> {restaurant['note_globale']}/5</p>
                                <p>📍 {restaurant['adresse']}</p>
                                <hr>
                                <p><strong>🍳 Cuisine:</strong> {restaurant['type_cuisines']}</p>
                                <p><strong>⚙️ Services:</strong> {restaurant['fonctionnalites']}</p>
                                <p><strong>ℹ️ Info:</strong> {restaurant['infos_pratiques']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("👆 Cliquez sur un restaurant pour voir les détails")
            except Exception as e:
                logger.error(f"Error displaying details: {e}")
                st.error("Erreur d'affichage des détails")

    except Exception as e:
        logger.error(f"Error: {e}")
        st.error(f"Une erreur est survenue: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

# if __name__ == "__main__":
#     show()