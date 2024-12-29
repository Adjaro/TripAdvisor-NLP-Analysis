import streamlit as st
import requests
import pandas as pd

# URL du serveur (utiliser le bon alias réseau si applicable)
server_url = "http://server:8000"

def show():
    # Personnalisation du design de la page
    # st.set_page_config(page_title="Data Dashboard", layout="wide", initial_sidebar_state="expanded")

    # Barre latérale
    st.sidebar.title("Options")
    st.sidebar.markdown("### Naviguez entre les données 📊")

    option = st.sidebar.selectbox(
        "Choisissez un type de données",
        ("📋 Reviews", "📍 Location", "🍴 All Restaurants", "📅 Date",  'temp'),
        help="Sélectionnez une option pour afficher les données correspondantes."
    )

    # Définition de l'endpoint selon l'option sélectionnée
    if option == "📋 Reviews":
        endpoint = "/review"
        st.sidebar.markdown("#### 📋 Affichage des reviews")
    elif option == "📍 Location":
        endpoint = "/location"
        st.sidebar.markdown("#### 📍 Affichage des locations")
    elif option == "🍴 All Restaurants":
        endpoint = "/allrestaurants"
        st.sidebar.markdown("#### 🍴 Liste des restaurants")
    elif option == "📅 Date":
        endpoint = "/date"
        st.sidebar.markdown("#### 📅 Données par date")
    elif option == "temp":
        data_restaurant = requests.get(f"{server_url}/allrestaurants").json()   
        data_localisation = requests.get(f"{server_url}/location").json()
        df_restaurant = pd.DataFrame(data_restaurant)
        df_localisation = pd.DataFrame(data_localisation)

        merge = pd.merge(df_restaurant, df_localisation, on='id_location')
        data = merge[['nom', 'adresse']]
        st.dataframe(data, use_container_width=True)

 


    # Affichage principal
    st.title("Data Visualization Dashboard")
    st.markdown(
        """
        Visualisez et explorez vos données API directement via cette interface intuitive.
        """
    )

    # Requête API
    try:
        response = requests.get(f"{server_url}{endpoint}")
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ Données récupérées avec succès depuis `{server_url}{endpoint}`")
            
            # Affichage des données
            if isinstance(data, list):
                st.dataframe(data, use_container_width=True)
            else:
                st.json(data)
        else:
            st.error(f"⚠️ Erreur lors de la récupération des données: {response.status_code}")
    except Exception as e:
        st.error(f"🚨 Une erreur s'est produite : {e}")

 
# # Exécutez la fonction principale
# if __name__ == "__main__":
#     show()
