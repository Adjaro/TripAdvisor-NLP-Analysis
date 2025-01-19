import streamlit as st
from scraper import TripadvisorScraper
import json
import pandas as pd
from datetime import datetime
import os
import math
import logging
import subprocess
from alimentationBd import insert_data
import time

def load_css():
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .title-container {
            background: linear-gradient(to right, #1e3c72, #2a5298);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        .team-card {
            text-align: center;
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stat-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def handle_scraping_error(e: Exception) -> None:
    """Handle scraping errors and display appropriate messages"""
    error_msg = str(e)
    if "NoneType" in error_msg:
        st.error("❌ Impossible d'initialiser le navigateur. Veuillez réessayer.")
    elif "timeout" in error_msg.lower():
        st.error("❌ Délai d'attente dépassé. Le site est peut-être surchargé.")
    else:
        st.error(f"❌ Erreur: {error_msg}")
    logging.error(f"Scraping error: {error_msg}")

def enregistrer_dans_la_base(data):
    try:
        subprocess.run(["python", "alimentationBd.py"], check=True)
        insert_data(data)
        st.success("✅ Données sauvegardées avec succès!")
    except Exception as e:
        st.error(f"❌ Erreur de sauvegarde: {str(e)}")
        logging.error(f"Database error: {str(e)}")

def show():
    st.title("🍽️ Ajouter un Restaurant")
    
    # Page layout
    url = st.text_input(
        "URL du restaurant TripAdvisor",
        placeholder="https://www.tripadvisor.fr/Restaurant_Review-...",
        help="Collez l'URL complète du restaurant depuis TripAdvisor"
    )

    if st.button("🔄 Scraper le restaurant", use_container_width=True):
        if not url.startswith("https://www.tripadvisor.fr/Restaurant_Review"):
            st.error("⚠️ URL invalide. Veuillez entrer une URL TripAdvisor valide.")
            return

        try:
            # Progress tracking
            progress = st.progress(0)
            status = st.empty()
            
            # Phase 1: Initialization
            status.info("🔄 Initialisation du scraper...")
            scraper = TripadvisorScraper(url)
            # scraper.create_driver()
            status.success("✅ Initialisation réussie!")
            progress.progress(20)

            # Phase 4: Scraping
            status.info("⚙️ Récupération des données...")
            # data = scraper.scrapper()
            data = {
                "nom": "Agastache Restaurant11",
                "adresse": "134 Rue Duguesclin, 69006 Lyon Franc&ée",
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
            
            
            if data:
                progress.progress(80)
                
                # Display Results
                status.success("✅ Scraping terminé!")
                tabs = st.tabs(["📌 Informations", "⭐ Notes", "💬 Avis"])
                
                with tabs[0]:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 📍 Détails")
                        st.json({
                            "Nom": data['nom'],
                            "Adresse": data['adresse'],
                            "Cuisine": data['type_cuisines']
                        })
                    with col2:
                        st.markdown("### 📊 Statistiques")
                        st.metric("Classement", f"#{data['classement']}")
                        st.metric("Note Globale", f"{data['note_globale']}/5")
                
                with tabs[1]:
                    scores = st.columns(4)
                    scores[0].metric("Cuisine", f"{data['note_cuisine']}/5")
                    scores[1].metric("Service", f"{data['note_service']}/5")
                    scores[2].metric("Qualité/Prix", f"{data['note_rapportqualiteprix']}/5")
                    scores[3].metric("Ambiance", f"{data['note_ambiance']}/5")
                
                with tabs[2]:
                    if data['avis']:
                        reviews_df = pd.DataFrame(data['avis'])
                        st.dataframe(
                            reviews_df,
                            column_config={
                                "nb_etoiles": st.column_config.ProgressColumn(
                                    "Note",
                                    min_value=0,
                                    max_value=5,
                                    format="%d ⭐"
                                ),
                                "date": "Date",
                                "titre_review": "Titre",
                                "review": "Commentaire"
                            },
                            use_container_width=True
                        )
                
                progress.progress(100)
                
                # Save Options
                st.markdown("### 💾 Sauvegarder les données")
                save_col1, save_col2 = st.columns(2)
                insert_data(data)
                with save_col1:
                    if st.button("💾 Enregistrer dans la base", use_container_width=True):
                        insert_data(data)
                        #faire un spinner
                        st.spinner("Sauvegarde en cours...")
                        time.sleep(5)
                        st.success("✅ Données sauvegardées avec succès!")
                        enregistrer_dans_la_base(data)
                
                with save_col2:
                    json_str = json.dumps(data, ensure_ascii=False)
                    st.download_button(
                        "📥 Télécharger JSON",
                        data=json_str,
                        file_name=f"{data['nom'].lower().replace(' ', '_')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
        except Exception as e:
            handle_scraping_error(e)
            st.write(f"Error: {str(e)}")
        finally:
            if 'scraper' in locals():
                scraper.cleanup()

# if __name__ == "__main__":
#     show()