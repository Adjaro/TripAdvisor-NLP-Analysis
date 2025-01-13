import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import json

# Configuration de la page
st.set_page_config(
    page_title="Cartography",
    page_icon="🌍",
    layout="wide",  # Mettre la page en mode large
)

# Titre de la page
st.title("Cartographie")
st.write("Bienvenue sur la page de cartographie.")

# Définir les colonnes pour l'affichage
col1, col2 = st.columns([3, 1]) 

 
 
# Charger les fichiers JSON et extraire les informations nécessaires
restaurants = []
for filename in os.listdir(data_folder):
    if filename.endswith(".json"):
        with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as file:
            data = json.load(file)
            # Extraire directement les informations nécessaires
            restaurant = {
                "name": data["nom"],
                "latitude": data["latitude"],
                "longitude": data["longitude"],
                "address": data["adresse"],
                "type_cuisine": ", ".join(data["type_cuisines"]),

            }
            restaurants.append(restaurant)

# Vérifier si des données de restaurant ont été trouvées
if not restaurants:
    st.error("Aucune donnée de restaurant trouvée. Vérifiez vos fichiers JSON.")
else:
    # Créer une carte Folium centrée sur le premier restaurant
    first_restaurant = restaurants[0]
    map_center = [first_restaurant["latitude"], first_restaurant["longitude"]]
    folium_map = folium.Map(location=map_center, zoom_start=13)

    # Ajouter les marqueurs pour chaque restaurant (sans popup)
    for restaurant in restaurants:
        folium.Marker(
            location=[restaurant["latitude"], restaurant["longitude"]],
            tooltip=restaurant["name"],  # Tooltip pour survol
            icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
        ).add_to(folium_map)

    # Afficher la carte avec Streamlit dans la colonne 1
    with col1:
        map_data = st_folium(folium_map, width=900, height=600)  # Carte agrandie

    # Afficher les détails du restaurant cliqué dans la colonne 2
    with col2:
       
        # Identifier le restaurant sélectionné à partir du clic sur la carte
        if map_data and "last_object_clicked" in map_data:
            last_clicked = map_data["last_object_clicked"]

            # Vérifier si des données de clic existent
            if last_clicked:
                clicked_lat = last_clicked["lat"]
                clicked_lng = last_clicked["lng"]

                # Trouver le restaurant correspondant
                selected_restaurant = next(
                    (
                        r for r in restaurants
                        if r["latitude"] == clicked_lat and r["longitude"] == clicked_lng
                    ),
                    None,
                )

                if selected_restaurant:
                    # Afficher les détails avec un cadre et un style
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #F0F2F6;
                            border-radius: 5px;
                            padding: 15px;
                            background-color: #FFFFFF;
                            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                            font-size: 15px;
                        ">
                            <h5 style="color: #31333F; text-align: center;">{selected_restaurant['name']}</h5>
                            <hr style="border: 1px solid #F0F2F6; margin-top: 0; margin-bottom: 5px;">
                            <p><strong>Adresse :</strong> {selected_restaurant['address']}</p>
                            <p><strong>Type de cuisine :</strong> {selected_restaurant['type_cuisine']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.write("Cliquez sur un restaurant pour voir les détails.")
        else:
            st.write("Cliquez sur un restaurant pour voir les détails.")
