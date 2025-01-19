import streamlit as st
from scraper import TripadvisorScraper
import json
import pandas as pd
from datetime import datetime
import os
from alimentationBd import insert_data
import math

def enregistrer_dans_la_base(data):
    try:
        insert_data(data)
        st.success("✅ Données sauvegardées avec succès!")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")

def show():
    st.title("🍽️ Ajouter un Restaurant")
    
    # Style definitions
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            margin-top: 1rem;
        }
        .info-card {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # URL Input section
    with st.container():
        url = st.text_input(
            "URL du restaurant TripAdvisor",
            placeholder="https://www.tripadvisor.fr/Restaurant_Review-..."
        )

    # Scraping section
    if st.button("🔄 Scraper le restaurant"):
        if not url:
            st.warning("⚠️ Veuillez entrer une URL valide")
            return
            
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize scraper
            status_text.text("Initialisation du scraper...")
            progress_bar.progress(10)
            scraper = TripadvisorScraper(url)
            
            # Progress container
            stats_container = st.container()
            
            with stats_container:
                try:
                    # Get restaurant info
                    with st.spinner("🔍 Recherche du restaurant..."):
                        scraper.find_restaurant_name()
                        nom = scraper.nom
                        if nom:
                            st.success(f"Restaurant trouvé: {nom}")
                            
                    # Extract page info
                    with st.spinner("📊 Analyse des pages..."):
                        scraper.extraire_infos()
                        
                    # Show stats
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Commentaires totaux",
                            scraper.nb_total_commentaires
                        )
                        
                    with col2:
                        st.metric(
                            "Pages à scraper",
                            scraper.nb_pages
                        )
                        
                    with col3:
                        average_time_per_page = 15
                        estimated_time = math.ceil((average_time_per_page * scraper.nb_pages) / 60)
                        st.metric(
                            "Temps estimé",
                            f"{estimated_time} minutes"
                        )
                    
                    # Start scraping progress bar
                    progress_bar = st.progress(0)
                    st.info(f"⏳ Temps estimé: {estimated_time} minutes")
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
            
            # Start scraping
            status_text.text("Récupération des données...")
            progress_bar.progress(30)
            
            # scraper.scrapper()
            # data = scraper.data
            data = {
                "nom": "Agastache Restaurant1",
                "adresse": "134 Rue Duguesclin, 69006 Lyon France",
                "classement": 6,
                "horaires": [
                    "lun : 12:00-13:00 - 19:30-21:00",
                    "mar : 12:00-13:00 - 19:30-21:00",
                    "mer : 12:00-13:00 - 19:30-21:00",
                    "jeu : 12:00-13:00 - 19:30-21:00",
                    "ven : 12:00-13:00 - 19:30-21:00"
                ],
                "note_globale": 5.0,
                "note_cuisine": 4.9,
                "note_service": 5.0,
                "note_rapportqualiteprix": 4.9,
                "note_ambiance": 4.7,
                "infos_pratiques": "L’Agastache, vous connaissez ? Ce nom n’a pas été choisi par hasard ! C’est une plante vivace, au goût anisé très prononcé. Notre cuisine s’inspire de la nature. Le restaurant Agastache vous invite à découvrir son univers « Bistronomique », l’association d’une cuisine gastronomique, et d’un environnement bistrot, décontracté, moderne et chaleureux.",
                "repas": [
                    "Déjeuner",
                    "Dîner"
                ],
                "regimes": "Non renseigné",
                "fourchette_prix": "25,00 -42,00 ",
                "fonctionnalités": [
                    "Réservations",
                    "Places assises",
                    "Sert de l'alcool",
                    "Cartes bancaires acceptées",
                    "Service de table"
                ],
                "type_cuisines": [
                    "Française",
                    "Moderne",
                    "Saine"
                ],
                "latitude": 45.766384,
                "longitude": 4.847662,
                "nb_avis": 203,
                "nbExcellent": 195,
                "nbTrèsbon": 6,
                "nbMoyen": 2,
                "nbMédiocre": 0,
                "nbHorrible": 0,
                "avis": [
                    {
                        "pseudo": "seb301087",
                        "titre_review": "« THE » adresse!",
                        "nb_etoiles": 5,
                        "date": "14 décembre 2024",
                        "experience": "business",
                        "review": "Un très bon accueil, des plats à tomber par terre, la truffe mise à l’honneur en cette période de fête.\nA l’occasion d’un déjeuner entre artisans, un moment incroyable.\nFélicitations au chef, bravo au gérant pour ce concept avec une cuisine digne d’un étoilé, le prix en moins.\nA voir absolument. SG"
                    },
                    {
                        "pseudo": "MaMaMaEl",
                        "titre_review": "Top Top Top !!",
                        "nb_etoiles": 5,
                        "date": "11 décembre 2024",
                        "experience": "family",
                        "review": "menu à 35€ comprenant entrée, plat, dessert 2 interludes + suppléments.\nthé de champignons parfumés, très original offert avant le repas.\napéro maison très délicat parfumé à l’agastache.\ntout le repas était délicieux : foie gras et châtaignes torréfiées, Noix de Saint-Jacques chou poivre de timut ; merlu et betterave ; dessert et interludes merveilleux…\nassiettes très chaudes.\nle chef passe régulièrement et recommande le vin rouge (Loire volcanique, éclat de granit 2023, domaine sérol bio, très bon)\nle serveur donne des explications pour chaque plat ou interlude.\nTop Top Top !!"
                    },  

                  ]                  
                }
            
            if not data:
                st.error("❌ Aucune donnée n'a pu être récupérée")
                return
            
            progress_bar.progress(70)
            status_text.text("Traitement des données...")
            
            # Display results
            st.success(f"✅ Restaurant '{data['nom']}' scrapé avec succès!")
            
            # Restaurant info tabs
            tab1, tab2, tab3 = st.tabs(["📌 Informations", "⭐ Notes", "💬 Avis"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📍 Détails")
                    st.write(f"**Nom:** {data['nom']}")
                    st.write(f"**Adresse:** {data['adresse']}")
                    st.write(f"**Type de cuisine:** {', '.join(data['type_cuisines'])}")
                with col2:
                    st.markdown("### 🕒 Horaires")
                    for horaire in data['horaires']:
                        st.write(horaire)
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Note globale", f"{data['note_globale']}/5")
                    st.metric("Cuisine", f"{data['note_cuisine']}/5")
                with col2:
                    st.metric("Service", f"{data['note_service']}/5")
                    st.metric("Rapport qualité/prix", f"{data['note_rapportqualiteprix']}/5")
            
            with tab3:
                df_reviews = pd.DataFrame(data['avis'])
                st.dataframe(df_reviews, use_container_width=True)
            
            progress_bar.progress(100)
            status_text.text("Terminé !")
            
            # Save data option
            if st.button("💾 Sauvegarder dans la base"):
                try:
                    st.write(insert_data(data))
                    st.success("✅ Données sauvegardées avec succès!")
                except Exception as e:
                    st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
                
        except Exception as e:
            st.error(f"❌ Une erreur est survenue: {str(e)}")
            
    # Help section
    with st.expander("ℹ️ Aide"):
        st.markdown("""
        1. Copiez l'URL d'un restaurant depuis TripAdvisor
        2. Collez l'URL dans le champ ci-dessus
        3. Cliquez sur "Scraper le restaurant"
        4. Attendez la fin du processus
        5. Sauvegardez les données
        """)