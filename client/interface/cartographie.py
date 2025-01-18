import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from folium.plugins import MarkerCluster
from manager import read_restaurant, read_location, get_db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def updateDf(df, colname, filters):
    """Filtre le DataFrame selon les valeurs choisies pour une colonne (logique ET)."""
    if not filters:
        return df
    try:
        for filter_value in filters:
            df = df[df[colname].str.contains(filter_value, na=False, case=False)]
        return df
    except Exception as e:
        logger.error(f"Error updating DataFrame for column {colname}: {e}")
        return df

def makefiltre(df, colname):
    """Génère une liste de valeurs uniques pour un filtre."""
    try:
        if colname not in df.columns:
            return []
        values = df[colname].dropna().str.split(',').explode()
        return sorted(values.str.strip().unique())
    except Exception as e:
        logger.error(f"Error creating filter for column {colname}: {e}")
        return []

def show():
    st.title("📍 Carte des Restaurants")

    db = next(get_db())
    try:
        # Charger et fusionner les données
        restaurants = pd.merge(
            read_restaurant(db=db),
            read_location(db=db),
            on='id_location'
        )

        if restaurants.empty:
            st.error("Aucune donnée disponible.")
            return

        # Ajouter des filtres
        with st.expander("🔎 Filtres avancés"):
            col1, col2, col3 = st.columns(3, gap="small")
            
            with col1:
                cuisine_filters = st.multiselect(
                    'Type de cuisine 🍳',
                    makefiltre(restaurants, 'type_cuisines')
                )
            with col2:
                repas_filters = st.multiselect(
                    'Type de repas 🍽️',
                    makefiltre(restaurants, 'repas')
                )
            with col3:
                fonctionnalites_filters = st.multiselect(
                    'Fonctionnalités ⚙️',
                    makefiltre(restaurants, 'fonctionnalites')
                )

        # Appliquer les filtres avec logique ET
        filtered_restaurants = restaurants.copy()
        filtered_restaurants = updateDf(filtered_restaurants, 'type_cuisines', cuisine_filters)
        filtered_restaurants = updateDf(filtered_restaurants, 'repas', repas_filters)
        filtered_restaurants = updateDf(filtered_restaurants, 'fonctionnalites', fonctionnalites_filters)

        # Afficher la carte
        map_col, details_col = st.columns([5, 4], gap="small")
        
        with map_col:
            if filtered_restaurants.empty:
                st.warning("Aucun restaurant ne correspond aux filtres.")
            else:
                # Centrer la carte sur les restaurants filtrés
                map_center = [
                    filtered_restaurants["latitude"].mean(),
                    filtered_restaurants["longitude"].mean()
                ]
                
                # Créer la carte Folium
                folium_map = folium.Map(location=map_center, zoom_start=13)
                # marker_cluster = MarkerCluster().add_to(folium_map)
                
                # Ajouter des marqueurs pour chaque restaurant filtré
                for _, restaurant in filtered_restaurants.iterrows():
                    folium.Marker(
                        location=[restaurant["latitude"], restaurant["longitude"]],
                        tooltip=restaurant["nom"],
                        icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
                    ).add_to(folium_map)

                # Afficher la carte dans Streamlit
                map_data = st_folium(folium_map, width=900, height=600)

        with details_col:
            try:
                if map_data and "last_object_clicked" in map_data:
                    clicked = map_data["last_object_clicked"]
                    if clicked:
                        restaurant = filtered_restaurants[
                            (filtered_restaurants["latitude"] == clicked["lat"]) &
                            (filtered_restaurants["longitude"] == clicked["lng"])
                        ].iloc[0]
                        
                        st.markdown(f"""
                            <div style='
                                background-color: white; 
                                padding: 20px; 
                                border-radius: 10px; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                width: 100%;
                                overflow-y: auto;
                                margin-bottom: 20px;
                            '>
                                <h2 style='font-size: 24px; color: #1E1E1E;'>{restaurant['nom']}</h2>
                                <p><strong>Note:</strong> {restaurant['note_globale']}/5</p>
                                <p><strong>Adresse:</strong> {restaurant['adresse']}</p>
                                <p><strong>Info:</strong> {restaurant['infos_pratiques']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("👆 Cliquez sur un restaurant pour voir les détails.")
            except Exception as e:
                logger.error(f"Error showing restaurant details: {e}")
                # st.error("Une erreur s'est produite lors de l'affichage des détails du restaurant.")
                st.info("👆 Cliquez sur un restaurant pour voir les détails.")

                

    except Exception as e:
        logger.error(f"Error in show function: {e}")
        st.error("Une erreur s'est produite lors du chargement des données.")
        # st.info("👆 Cliquez sur un restaurant pour voir les détails.")

        
    finally:
        db.close()
