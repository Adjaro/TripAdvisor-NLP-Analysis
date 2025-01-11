import streamlit as st
import pandas as pd
from manager import read_restaurant, read_location, read_date, read_review, get_db  # Importation des fonctions nécessaires

def show():
    # Titre principal avec un style attrayant
    st.markdown(
        """
        <h1 style="text-align:center; color:#4CAF50; font-family:Arial;">
        📊 Data Visualization Dashboard
        </h1>
        <p style="text-align:center; color:gray; font-size:16px;">
        Explorez et interagissez avec vos données facilement.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Connexion à la base de données
    db = next(get_db())  # Récupération de la session de base de données

    # Fonction de pagination
    def paginate_dataframe(df, page_size=20):
        total_pages = (len(df) // page_size) + (1 if len(df) % page_size != 0 else 0)
        page = st.number_input(
            "Page", min_value=1, max_value=max(total_pages, 1), step=1, key="pagination"
        )
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return df.iloc[start_idx:end_idx]

    # Onglets pour une navigation intuitive
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📋 Reviews", "📍 Locations", "🍴 Restaurants", "📅 Dates", "🔄 Fusion Temp"]
    )

    try:
        # Tab 1: Reviews
        with tab1:
            st.subheader("📋 Avis")
            try:
                reviews = read_review(db=db)  # Récupération des données
                if reviews:  # Vérification que les données ne sont pas vides
                    df_reviews = pd.DataFrame(reviews)
                    if not df_reviews.empty:  # Vérification explicite pour les DataFrames
                        df_paginated = paginate_dataframe(df_reviews)
                        st.dataframe(df_paginated, use_container_width=True)
                    else:
                        st.info("ℹ️ Aucune donnée d'avis disponible.")
                else:
                    st.info("ℹ️ Aucune donnée d'avis disponible.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des reviews : {e}")

        # Tab 2: Locations
        with tab2:
            st.subheader("📍 Localisations")
            try:
                locations = read_location(db=db)  # Récupération des données
                if locations:
                    df_locations = pd.DataFrame(locations)
                    if not df_locations.empty:
                        df_paginated = paginate_dataframe(df_locations)
                        st.dataframe(df_paginated, use_container_width=True)
                    else:
                        st.info("ℹ️ Aucune localisation disponible.")
                else:
                    st.info("ℹ️ Aucune localisation disponible.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des localisations : {e}")

        # Tab 3: Restaurants
        with tab3:
            st.subheader("🍴 Restaurants")
            try:
                restaurants = read_restaurant(db=db)  # Récupération des données
                if restaurants:
                    df_restaurants = pd.DataFrame(restaurants)
                    if not df_restaurants.empty:
                        df_paginated = paginate_dataframe(df_restaurants)
                        st.dataframe(df_paginated, use_container_width=True)
                    else:
                        st.info("ℹ️ Aucun restaurant disponible.")
                else:
                    st.info("ℹ️ Aucun restaurant disponible.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des restaurants : {e}")

        # Tab 4: Dates
        with tab4:
            st.subheader("📅 Dates")
            try:
                dates = read_date(db=db)  # Récupération des données
                if dates:
                    df_dates = pd.DataFrame(dates)
                    if not df_dates.empty:
                        df_paginated = paginate_dataframe(df_dates)
                        st.dataframe(df_paginated, use_container_width=True)
                    else:
                        st.info("ℹ️ Aucune donnée de date disponible.")
                else:
                    st.info("ℹ️ Aucune donnée de date disponible.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des dates : {e}")

        # Tab 5: Temp Data Fusion
        with tab5:
            st.subheader("🔄 Fusion Temp")
            try:
                restaurants = read_restaurant(db=db)  # Récupération des restaurants
                locations = read_location(db=db)  # Récupération des localisations

                if restaurants and locations:
                    df_restaurant = pd.DataFrame(restaurants)
                    df_location = pd.DataFrame(locations)

                    # Fusion des données sur "id_location"
                    if not df_restaurant.empty and not df_location.empty:
                        merged_data = pd.merge(df_restaurant, df_location, on="id_location")
                        merged_data = merged_data[["nom", "adresse"]]  # Colonnes utiles
                        df_paginated = paginate_dataframe(merged_data)
                        st.dataframe(df_paginated, use_container_width=True)
                    else:
                        st.info("ℹ️ Données insuffisantes pour effectuer la fusion.")
                else:
                    st.info("ℹ️ Données insuffisantes pour effectuer la fusion.")
            except Exception as e:
                st.error(f"Erreur lors de la fusion des données : {e}")

    except Exception as e:
        st.error(f"🚨 Une erreur inattendue s'est produite : {e}")
    finally:
        db.close()  # Fermeture de la session de base de données


# # Exécutez la fonction principale
# if __name__ == "__main__":
#     show()
