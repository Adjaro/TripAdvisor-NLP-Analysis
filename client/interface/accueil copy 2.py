import streamlit as st
from PIL import Image
import os

def show():
    # Page config
    # st.set_page_config(
    #     page_title="TripAdvisor NLP Analysis",
    #     page_icon="🍽️",
    #     layout="wide"
    # )

    # Title Section
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🍽️ Analyse des Avis TripAdvisor")
        st.markdown("### Une analyse approfondie des restaurants parisiens")

    # Project Description
    st.markdown("""
    ## À propos du projet
    
    Ce projet utilise le **Natural Language Processing** (NLP) pour analyser les avis des restaurants sur TripAdvisor. 
    Nous exploitons des techniques avancées d'analyse de sentiment, de clustering et de visualisation pour extraire 
    des insights pertinents des commentaires des clients.
    """)

    # Key Features
    st.markdown("## Fonctionnalités principales")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### 🔍 Analyse de Sentiment
        - Évaluation des avis
        - Classification des émotions
        - Tendances temporelles
        """)

    with col2:
        st.markdown("""
        ### 📊 Visualisations
        - Nuages de mots
        - Graphiques interactifs
        - Cartographie des restaurants
        """)

    with col3:
        st.markdown("""
        ### 🤖 NLP Avancé
        - Word Embeddings
        - Analyse thématique
        - Clustering de restaurants
        """)

    # Team Section
    st.markdown("## Notre équipe")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### Adjaro
        Data Scientist & NLP Expert
        - 🔬 Spécialiste en analyse de sentiment
        - 📊 Expert en visualisation de données
        """)

    with col2:
        st.markdown("""
        ### Lin
        Data Engineer & ML Specialist
        - 🛠️ Architecture du projet
        - 🤖 Modélisation machine learning
        """)

    with col3:
        st.markdown("""
        ### Nancy
        Data Analyst & Project Manager
        - 📈 Analyse des données
        - 📋 Gestion de projet
        """)

    # Project Stats
    st.markdown("## Statistiques du projet")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Restaurants analysés", "1000+")
    with col2:
        st.metric("Avis traités", "50,000+")
    with col3:
        st.metric("Précision du modèle", "85%")
    with col4:
        st.metric("Villes couvertes", "Paris")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Développé avec ❤️ par l'équipe TripAdvisor NLP Analysis</p>
        <p>Master Data Science - Promotion 2024</p>
    </div>
    """, unsafe_allow_html=True)

    # Add some interactivity
    if st.button("🎯 Commencer l'analyse"):
        st.success("Naviguez vers l'onglet 'Analyse NLP' pour explorer les données !")