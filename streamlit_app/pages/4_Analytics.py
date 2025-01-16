import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

# Fonction pour charger les fichiers JSON
def load_data(data_folder):
    data = []
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            filepath = os.path.join(data_folder, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                try:
                    restaurant_data = json.load(file)
                    data.append({
                        "nom": restaurant_data["nom"],
                        "type_cuisine": restaurant_data["type_cuisines"],  # Liste des types de cuisines
                        "note_globale": restaurant_data["note_globale"],
                        "note_cuisine": restaurant_data["note_cuisine"],
                        "note_service": restaurant_data["note_service"],
                        "note_rapportqualiteprix": restaurant_data["note_rapportqualiteprix"],
                        "note_ambiance": restaurant_data["note_ambiance"],
                    })
                except Exception as e:
                    st.warning(f"Erreur lors de la lecture de {filename}: {e}")
    return pd.DataFrame(data)

# Charger les données
data_folder = "D:/SISE/TripAdvisor-NLP-Analysis/data"
df = load_data(data_folder)

# Vérifier si des données ont été chargées
if df.empty:
    st.error("Aucune donnée n'a été trouvée dans le dossier spécifié.")
else:
    # Transformer `type_cuisine` en liste plate pour le filtrage
    df["type_cuisine_flat"] = df["type_cuisine"].apply(lambda x: [cuisine.strip() for cuisine in x])
    all_cuisines = set([cuisine for sublist in df["type_cuisine_flat"] for cuisine in sublist])

    # Interface utilisateur
    st.title("Analyse des Restaurants")
    st.write("Bar plot des restaurants avec un filtre `type_cuisine`.")

    # Déplacer le filtre dans la barre latérale
    st.sidebar.header("Filtres")

    # Filtre par type de cuisine
    selected_cuisine = st.sidebar.selectbox(
        "Type de cuisine (sélectionner un mot-clé)",
        options=list(all_cuisines),
        index=0  # Par défaut, sélectionner le premier mot-clé
    )

    # Filtrer les données
    def filter_by_cuisine(row):
        return selected_cuisine in row["type_cuisine_flat"]

    filtered_df = df[df.apply(filter_by_cuisine, axis=1)]

    # Bar plot
    if not filtered_df.empty:
        bar_fig = px.bar(
            filtered_df,
            x="nom",
            y="note_globale",
            title=f"Notes globales des restaurants (cuisine : {selected_cuisine})",
            labels={"nom": "Restaurant", "note_globale": "Note Globale"},
            text="note_globale"
        )
        bar_fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        bar_fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        # Afficher le graphe
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.warning("Aucun restaurant ne correspond au type de cuisine sélectionné.")
