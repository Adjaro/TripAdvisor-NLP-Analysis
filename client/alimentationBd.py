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

# Load all JSON files into memory
def load_all_json(data_dir='./data'):
    data_list = []
    for file in get_data_list(data_dir):
        data = read_json_file(f'{data_dir}/{file}')
        data_list.append(data)
    return data_list

# Insert data from JSON files
def insert_json_data(data_dir='./data'):
    all_data = load_all_json(data_dir)
    db = database.SessionLocal()
    try:
        for data in all_data:
            insert_data(data)
    finally:
        db.close()

# # Start the import process
# if __name__ == "__main__":
#     insert_json_data()