import streamlit as st
import pandas as pd
from manager import read_restaurant, read_location, read_date, read_review, get_db  # Importation des fonctions nécessaires

def show():
    # Configuration de la page
    # st.set_page_config(page_title="Data Dashboard", layout="wide", initial_sidebar_state="expanded")

    # Barre latérale
    st.sidebar.title("Options")
    st.sidebar.markdown("### Naviguez entre les données 📊")

    option = st.sidebar.selectbox(
        "Choisissez un type de données",
        ("📋 Reviews", "📍 Location", "🍴 All Restaurants", "📅 Date", "🔄 Temp"),
        help="Sélectionnez une option pour afficher les données correspondantes."
    )

    # Connexion à la base de données
    db = next(get_db())  # Récupération de la session de base de données

    # Affichage principal
    st.title("Data Visualization Dashboard")
    st.markdown(
        """
        Visualisez et explorez vos données directement via cette interface intuitive.
        """
    )

    def paginate_dataframe(df, page_size=20):
        total_pages = (len(df) // page_size) + 1
        page = st.sidebar.number_input("Page", min_value=1, max_value=total_pages, step=1)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return df.iloc[start_idx:end_idx]

    try:
        if option == "📋 Reviews":
            st.sidebar.markdown("#### 📋 Affichage des reviews")
            reviews = read_review(db=db, limit=10)  # Appel de la fonction pour lire les reviews
            if not reviews.empty:
                df = paginate_dataframe(reviews)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Aucune review disponible.")

        elif option == "📍 Location":
            st.sidebar.markdown("#### 📍 Affichage des locations")
            locations = read_location(db=db, limit=10)  # Appel de la fonction pour lire les locations
            if not locations.empty:
                df = paginate_dataframe(locations)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Aucune location disponible.")

        elif option == "🍴 All Restaurants":
            st.sidebar.markdown("#### 🍴 Liste des restaurants")
            restaurants = read_restaurant(db=db, limit=10)  # Appel de la fonction pour lire les restaurants
            if not restaurants.empty:
                df = paginate_dataframe(restaurants)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Aucun restaurant disponible.")

        elif option == "📅 Date":
            st.sidebar.markdown("#### 📅 Données par date")
            dates = read_date(db=db, limit=10)  # Appel de la fonction pour lire les dates
            if not dates.empty:
                df = paginate_dataframe(dates)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Aucune donnée disponible.")

        elif option == "🔄 Temp":
            st.sidebar.markdown("#### 🔄 Données fusionnées temporairement")
            restaurants = read_restaurant(db=db, limit=10)  # Lecture des restaurants
            locations = read_location(db=db, limit=10)  # Lecture des localisations

            if not restaurants.empty and not locations.empty:
                df_restaurant = pd.DataFrame(restaurants)
                df_location = pd.DataFrame(locations)

                # Fusion des données sur 'id_location'
                merged_data = pd.merge(df_restaurant, df_location, on="id_location")
                data = merged_data[["nom", "adresse"]]  # Colonnes pertinentes
                df = paginate_dataframe(data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Données insuffisantes pour effectuer la fusion.")
    except Exception as e:
        st.error(f"🚨 Une erreur s'est produite : {e}")
    finally:
        db.close()  # Fermeture de la session de base de données

# # Exécutez la fonction principale
# if __name__ == "__main__":
#     show()