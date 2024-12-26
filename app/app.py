# app.py
import streamlit as st
from interface import accueil , navbar, dashbord, cartographie, analyse_nlp, visualisation_data, scrapper_restaurant, rapport
import time

 

# Configuration pour la largeur de la page

st.set_page_config(
    page_title="Tripadvisor Scraper",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def connect_DataBase():
    return True

# Vérifiez le serveur avant de lancer l'application Streamlit
if connect_DataBase():
    # Initialisation de l'état de la page si nécessaire
    if 'page' not in st.session_state:
        st.session_state.page = 'Accueil'
    
    # Afficher le menu latéral
    navbar.show()

    # Affichage du contenu en fonction de la page sélectionnée
    if st.session_state.page == 'Accueil':
        accueil.show()
    elif st.session_state.page == 'Dashbord':
        dashbord.show()
    elif st.session_state.page == 'Cartographie':
        cartographie.show()
    elif st.session_state.page == 'Analyse NLP':
        analyse_nlp.show()
    elif st.session_state.page == 'Visualisation data':
        visualisation_data.show()
    elif st.session_state.page == 'Scrapper Restaurant':
        scrapper_restaurant.show()
    elif st.session_state.page == 'Rapport':
        rapport.show()

else:
    st.error("Le serveur n'est pas disponible. Veuillez réessayer plus tard.")