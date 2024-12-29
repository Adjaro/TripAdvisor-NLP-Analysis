import json
import os
import datetime
import uuid
from dateutil import parser
from .utils import database
from .model import models, schemas
from functools import lru_cache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# models.Base.metadata.create_all(bind=database.engine)

@lru_cache(maxsize=None)
def get_month_mapping():
    return {
        'janvier': 'January', 'février': 'February', 'mars': 'March',
        'avril': 'April', 'mai': 'May', 'juin': 'June', 'juillet': 'July',
        'août': 'August', 'septembre': 'September', 'octobre': 'October',
        'novembre': 'November', 'décembre': 'December'
    }

def parse_date(date_str):
    try:
        fr_to_en = get_month_mapping()
        day, month, year = date_str.split(' ')
        month_en = fr_to_en[month.lower()]
        date_en = f"{day} {month_en} {year}"
        return parser.parse(date_en, dayfirst=True)
    except Exception as e:
        logger.error(f"Error parsing date {date_str}: {e}")

# Charger un fichier JSON
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Obtenir la liste des fichiers JSON
def get_data_list(data_dir='./data'):
    return [f for f in os.listdir(data_dir) if f.endswith('.json')]


# Insérer des données en base de données (optimisé pour les batchs)
def insert_data(dict_data):
    db = database.SessionLocal()
    try:
        # Insérer la localisation
        id_location = str(uuid.uuid4())
        dict_location = {
            'id_location': id_location,
            'longitude': dict_data['longitude'],
            'latitude': dict_data['latitude'],
            'adresse': dict_data['adresse']
        }
        location = models.DimLocation(**schemas.DimLocation(**dict_location).model_dump())
        db.add(location)

        # Insérer le restaurant
        id_restaurant = str(uuid.uuid4())
        dict_restaurant = {
            'id_restaurant': id_restaurant,
            'nom': dict_data['nom'],
            'id_location': id_location
        }
        restaurant = models.DimRestaurant(**schemas.DimRestaurant(**dict_restaurant).model_dump())
        db.add(restaurant)

        # Préparer les entrées pour les avis et les dates
        avis_entries = []
        date_entries = []

        for avis in dict_data['avis']:
            # Insérer la date
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

            # Insérer l'avis
            id_avis = str(uuid.uuid4())
            dict_avis = {
                'id_avis': id_avis,
                'id_restaurant': id_restaurant,
                'id_date': id_date,
                'note': avis['nb_etoiles']
            }
            avis_entry = models.FaitAvis(**schemas.FaitAvis(**dict_avis).model_dump())
            avis_entries.append(avis_entry)

        # Exécuter les insertions groupées
        db.add_all(date_entries)
        db.add_all(avis_entries)
        db.commit()

    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()

# Charger tous les fichiers JSON en mémoire
def load_all_json(data_dir='./data'):
    data_list = []
    for file in get_data_list(data_dir):
        data = read_json_file(f'{data_dir}/{file}')
        data_list.append(data)
    return data_list

# Insérer les données des fichiers JSON
def insert_json_data(data_dir='./data'):
    all_data = load_all_json(data_dir)
    for data in all_data:
        insert_data(data)

# # Lancer l'importation
# if __name__ == "__main__":
#     insert_json_data()
