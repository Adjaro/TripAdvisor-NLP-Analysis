import streamlit as st
from scraper import TripadvisorScraper
import json
import pandas as pd
from datetime import datetime
import os
import math
import logging
import json
import os
import uuid
from dateutil import parser
from utils import database
from model import models, schemas
from functools import lru_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all tables in the database
models.Base.metadata.create_all(bind=database.engine)

@lru_cache(maxsize=None)
def get_month_mapping():
    return {
        'janvier': 'January', 'février': 'February', 'mars': 'March',
        'avril': 'April', 'mai': 'May', 'juin': 'June', 'juillet': 'July',
        'août': 'August', 'septembre': 'September', 'octobre': 'October',
        'novembre': 'November', 'décembre': 'December'
    }

def concatener(lst):
    return ', '.join(lst)

def parse_date(date_str):
    try:
        fr_to_en = get_month_mapping()
        day, month, year = date_str.split(' ')
        month_en = fr_to_en[month.lower()]
        date_en = f"{day} {month_en} {year}"
        return parser.parse(date_en, dayfirst=True)
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")

def get_value(data, key1, key2):
    return data.get(key1) or data.get(key2)

# Load a JSON file
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Get the list of JSON files
def get_data_list(data_dir='./data'):
    return [f for f in os.listdir(data_dir) if f.endswith('.json')]

def apply_concatener_if_list(value):
    if isinstance(value, list):
        return concatener(value)
    return value
# Insert data into the database (optimized for batches)
def insert_data(dict_data):
    db = database.SessionLocal()
    try:
        # Insert location
        id_location = str(uuid.uuid4())
        dict_location = {
            'id_location': id_location,
            'longitude': dict_data['longitude'],
            'latitude': dict_data['latitude'],
            'adresse': dict_data['adresse']
        }
        location = models.DimLocation(**schemas.DimLocation(**dict_location).model_dump())
        db.add(location)

        print(dict_data['nom'])
        # Insert restaurant
        id_restaurant = str(uuid.uuid4())
        dict_restaurant = {
            'id_restaurant': id_restaurant,
            'nom': dict_data['nom'],
            'classement': dict_data['classement'],
            'horaires': apply_concatener_if_list(dict_data['horaires']),
            'note_globale': dict_data['note_globale'],
            'note_cuisine': dict_data['note_cuisine'],
            'note_service': dict_data['note_service'],
            'note_rapportqualiteprix': dict_data['note_rapportqualiteprix'],
            'note_ambiance': dict_data['note_ambiance'],
            'infos_pratiques': apply_concatener_if_list(dict_data['infos_pratiques']),
            'repas': apply_concatener_if_list(dict_data['repas']),
            'fourchette_prix': dict_data['fourchette_prix'],
            'fonctionnalites': apply_concatener_if_list(dict_data['fonctionnalités']),
            'type_cuisines': apply_concatener_if_list(dict_data['type_cuisines']),
            'nb_avis': dict_data['nb_avis'],
            'nbExcellent': dict_data['nbExcellent'],
            'nbTresbon': get_value(dict_data, 'nbTrèsBon', 'nbTrèsbon'),
            'nbMoyen': dict_data['nbMoyen'],
            'nbMediocre': dict_data['nbMédiocre'],
            'nbHorrible': dict_data['nbHorrible'],
            'id_location': id_location
        }
        restaurant = models.DimRestaurant(**schemas.DimRestaurant(**dict_restaurant).model_dump())
        db.add(restaurant)

        # Prepare entries for reviews and dates
        avis_entries = []
        date_entries = []

        for avis in dict_data['avis']:
            # Insert date
            id_date = str(uuid.uuid4())
            date_temp = parse_date(avis['date'])
            jour_temp, mois_temp, annee_temp = avis['date'].split(' ')
            dict_time = {
                'id_date': id_date,
                'date': date_temp,
                'mois': str(mois_temp),
                'annee': str(annee_temp),
                'jour': str(jour_temp),
            }
            date_entry = models.DimDate(**schemas.DimDate(**dict_time).model_dump())
            date_entries.append(date_entry)

            # Insert review
            id_avis = str(uuid.uuid4())
            dict_avis = {
                'id_avis': id_avis,
                'id_restaurant': id_restaurant,
                'id_date': id_date,
                'nb_etoiles': avis['nb_etoiles'],
                'experience': avis['experience'],
                'review': avis['review'],
                'titre_avis': avis['titre_review']
            }
            avis_entry = models.FaitAvis(**schemas.FaitAvis(**dict_avis).model_dump())
            avis_entries.append(avis_entry)

        # Execute batch insertions
        db.add_all(date_entries)
        db.add_all(avis_entries)
        db.commit()
        logger.info(f"Data inserted for {dict_data['nom']}")
        print(f"Data inserted for {dict_data['nom']}")

    except Exception as e:
        logger.error(f"Erreur : {e}")
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()


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
                
                with save_col1:
                    if st.button("💾 Enregistrer dans la base", use_container_width=True):
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