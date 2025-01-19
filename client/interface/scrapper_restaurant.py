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
# import sys
# import io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
    st.markdown("""
        <div class='title-container'>
            <h1> 🍽️ Ajouter un Restaurant</h1>    
        </div>
    """, unsafe_allow_html=True)
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
            try:
                data = scraper.scrapper()
            except Exception as e:
                st.warning("❌ Erreur de scraping. Veuillez réessayer.")
                # handle_scraping_error(e)
                return
            # data = scraper.scrapper()
            
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
                insert_data(data)
                st.success("✅ Données sauvegardées avec succès dans  la base!")
 
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