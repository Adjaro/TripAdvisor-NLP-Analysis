import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from manager import read_restaurant, read_location, get_db, read_review, read_date


# Charger les données
def load_data():
    db = next(get_db())
    with db:
        df_restaurant = read_restaurant(db)
        df_date = read_date(db)
        df_review = read_review(db)
        df_location = read_location(db)
    return df_restaurant, df_date, df_review, df_location

# Charger les données
df_restaurant, df_date, df_review, df_location = load_data()

# Interface Streamlit
def show():
    #st.write(df_restaurant, df_date, df_review, df_location)
    st.title("Analyse des performances des restaurants")
    # Ajouter des onglets pour la navigation
    tab1, tab2, tab3 = st.tabs(["Analyse Globale", "Analyse des Avis", "Autres Analyses"])
    
    # Onglet 1 : Analyse Globale
    with tab1:
        st.header("Analyse Globale des Performances")
        
        # Créer deux colonnes : une pour les filtres et une pour les graphiques
        col1, col2 = st.columns([1, 3])

        with col1:
            st.write("##### Filtres")
            
            # Filtre restaurant via une fenêtre contextuelle
            if st.checkbox("Tous les restaurants", value=True):
                selected_restaurants = df_restaurant['nom'].unique()
            else:
                # Créer une fenêtre contextuelle pour afficher les restaurants avec des checkboxes
                selected_restaurants = []
                restaurant_names = df_restaurant['nom'].unique()
                with st.expander("Sélectionnez des restaurants"):
                    for restaurant in restaurant_names:
                        if st.checkbox(restaurant, value=False):
                            selected_restaurants.append(restaurant)

            # Filtre pour le critère
            critere = st.selectbox(
                "Critère de comparaison",
                ["note_globale", "note_cuisine", "note_service", "note_rapportqualiteprix", "note_ambiance"]
            )

            # Filtre pour afficher les restaurants
            classement_option = st.selectbox(
                "Afficher les classements",
                ["Tous les restaurants", "5 meilleurs restaurants", "5 pires restaurants"]
            )

        with col2:
            # Filtrer les données
            filtered_df = df_restaurant[df_restaurant['nom'].isin(selected_restaurants)]
            
            # Calcul des statistiques
            stats = filtered_df.groupby('nom')[['note_globale', 'note_cuisine', 'note_service', 'note_rapportqualiteprix', 'note_ambiance']].mean().reset_index()

            if stats.empty:
                st.warning("Aucune donnée disponible pour les restaurants sélectionnés.")
            else:
                # Filtrer en fonction du classement sélectionné
                if classement_option == "5 meilleurs restaurants":
                    stats = stats.nlargest(5, critere)
                elif classement_option == "5 pires restaurants":
                    stats = stats.nsmallest(5, critere)

                # Graphique par critère
                fig = px.bar(
                    stats,
                    x="nom",
                    y=critere,
                    title=f"Comparaison des restaurants selon {critere}",
                    labels={"nom": "Restaurant", critere: "Note"},
                    color="nom",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Radar chart pour un aperçu global
                radar_df = stats.melt(id_vars=["nom"], var_name="Critère", value_name="Note")
                fig_radar = px.line_polar(
                    radar_df,
                    r="Note",
                    theta="Critère",
                    color="nom",
                    line_close=True,
                    title="Performance globale par critères"
                )
                st.plotly_chart(fig_radar, use_container_width=True)

    # Onglet 2 : Analyse des Avis
    with tab2:
        st.header("Analyse des Avis")
        
        # Jointure des données avis et restaurant
        avis_data = df_review.merge(df_restaurant, on="id_restaurant", how="left")
        avis_data = avis_data.merge(df_date, on="id_date", how="left")
        
        # Définir un ordre explicite pour les mois
        mois_ordre = [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre"
        ]
        
        # Convertir 'mois' en une catégorie ordonnée et gérer les valeurs manquantes
        avis_data["mois"] = pd.Categorical(avis_data["mois"], categories=mois_ordre, ordered=True)
        
        # Trier les données par année et mois pour garantir l'ordre chronologique
        avis_data = avis_data.sort_values(by=["annee", "mois"])

        # Créer une colonne pour la période après le tri
        avis_data["période"] = avis_data["mois"].str.capitalize() + " " + avis_data["annee"].astype(str)

        # Filtres dynamiques pour l'analyse des avis
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_critere = st.selectbox(
                "Sélectionnez un critère",
                ["Nombre d'avis", "Note moyenne", "Répartition des avis"]
            )
            selected_years = st.multiselect(
                "Filtrer par année",
                options=sorted(avis_data["annee"].unique()),
                default=sorted(avis_data["annee"].unique())
            )
            selected_months = st.multiselect(
                "Filtrer par mois",
                options=mois_ordre,  # Utilisation de l'ordre explicite des mois
                default=mois_ordre
            )
            selected_restaurants = st.multiselect(
                "Sélectionnez un ou plusieurs restaurants",
                options=avis_data["nom"].unique(),
                default=list(avis_data["nom"].unique())
            )
        
        with col2:
            # Appliquer les filtres sur les avis
            filtered_avis = avis_data[
                (avis_data["nom"].isin(selected_restaurants)) &
                (avis_data["annee"].isin(selected_years)) &
                (avis_data["mois"].isin(selected_months))
            ]

            if filtered_avis.empty:
                st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
            else:
                # Recalculer dynamiquement la période après les filtres
                filtered_avis["période"] = (
                    filtered_avis["mois"].str.capitalize() + " " + filtered_avis["annee"].astype(str)
                )

                # Ajouter des colonnes pour trier explicitement par année et mois
                filtered_avis["mois_ordre"] = filtered_avis["mois"].cat.codes
                filtered_avis = filtered_avis.sort_values(by=["annee", "mois_ordre"])

                # Analyse et visualisation des avis
                if selected_critere == "Nombre d'avis":
                    avis_par_periode = (
                        filtered_avis.groupby(["période", "annee", "mois_ordre"])  # Ajouter les colonnes nécessaires pour le tri
                        .agg(nb_avis=("id_avis", "count"))
                        .reset_index()
                    )

                    avis_par_periode = avis_par_periode.sort_values(by=["annee", "mois_ordre"])  # Trier explicitement

                    st.write("### Évolution du nombre d'avis par période")
                    fig = px.line(
                        avis_par_periode,
                        x="période",
                        y="nb_avis",
                        title="Nombre d'avis au fil du temps",
                        labels={"période": "Période", "nb_avis": "Nombre d'avis"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif selected_critere == "Note moyenne":
                    avis_par_periode = (
                        filtered_avis.groupby(["période", "annee", "mois_ordre"])  # Ajouter les colonnes nécessaires pour le tri
                        .agg(note_moyenne=("nb_etoiles", "mean"))
                        .reset_index()
                    )

                    avis_par_periode = avis_par_periode.sort_values(by=["annee", "mois_ordre"])  # Trier explicitement

                    st.write("### Évolution de la note moyenne par période")
                    fig = px.line(
                        avis_par_periode,
                        x="période",
                        y="note_moyenne",
                        title="Note moyenne au fil du temps",
                        labels={"période": "Période", "note_moyenne": "Note moyenne"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                elif selected_critere == "Répartition des avis":
                    avis_categorie = (
                        filtered_avis.groupby(["période", "annee", "mois_ordre"])  # Ajouter les colonnes nécessaires pour le tri
                        .agg(
                            nbExcellent=("nbExcellent", "sum"),
                            nbTresbon=("nbTresbon", "sum"),
                            nbMoyen=("nbMoyen", "sum"),
                            nbMediocre=("nbMediocre", "sum"),
                            nbHorrible=("nbHorrible", "sum")
                        )
                        .reset_index()
                    )

                    avis_categorie = avis_categorie.sort_values(by=["annee", "mois_ordre"])  # Trier explicitement

                    avis_categorie = avis_categorie.melt(
                        id_vars=["période"],
                        value_vars=["nbExcellent", "nbTresbon", "nbMoyen", "nbMediocre", "nbHorrible"],
                        var_name="Catégorie",
                        value_name="Nombre"
                    )

                    avis_categorie["Catégorie"] = avis_categorie["Catégorie"].replace({
                        "nbExcellent": "Excellent",
                        "nbTresbon": "Très Bon",
                        "nbMoyen": "Moyen",
                        "nbMediocre": "Médiocre",
                        "nbHorrible": "Horrible"
                    })

                    st.write("### Répartition des avis par période et par catégorie")
                    fig = px.bar(
                        avis_categorie,
                        x="période",
                        y="Nombre",
                        color="Catégorie",
                        title="Répartition des avis par catégorie au fil du temps",
                        barmode="stack",
                        labels={"période": "Période", "Nombre": "Nombre d'avis", "Catégorie": "Type d'avis"}
                    )
                    st.plotly_chart(fig, use_container_width=True)


    # Onglet 3 : Autres Analyses
    with tab3:
        st.header("Autres Analyses")
        st.write("Vous pouvez ajouter ici d'autres types d'analyses (par exemple, tendances temporelles, localisation, etc.).")

