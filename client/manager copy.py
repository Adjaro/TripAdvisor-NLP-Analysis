from sqlalchemy.orm import Session
import os
import logging
import pandas as pd
from sqlalchemy import text
from typing import List, Optional

from model import models, schemas
from utils import database
from scraper import TripadvisorScraper
from alimentationBd import insert_json_data, get_data_list, read_json_file

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Check if specific data already exists in the database
def check_existing_data(db: Session, nom_restaurant: str, address: str) -> bool:
    try:
        exists = db.query(models.DimRestaurant, models.DimLocation)\
            .join(models.DimLocation)\
            .filter(
                models.DimRestaurant.nom == nom_restaurant,
                models.DimLocation.adresse == address
            ).first() is not None
        return exists
    except Exception as e:
        logger.error(f"Error checking existing data: {e}")
        return False

# Initialize the database
def InitialisationBD():
    try:
        models.Base.metadata.create_all(bind=database.engine)
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        logger.info(f"Data directory: {data_dir}")

        files = get_data_list(data_dir)
        if not files:
            logger.warning("No data files found")
            return

        data = read_json_file(os.path.join(data_dir, files[0]))
        db = next(get_db())
        try:
            data_exists = check_existing_data(db, data['nom'], data['adresse'])
            if not data_exists:
                logger.info("Inserting initial data...")
                insert_json_data(data_dir)
            else:
                logger.info("Data already exists in the database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Scrape data from a given URL
def scrape(url: str):
    try:
        scraper = TripadvisorScraper(url)
        scraper.scrapper()
        data = scraper.data
        return data
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise RuntimeError(f"Scraping failed: {str(e)}")

# Query restaurants
def read_restaurant(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.DimRestaurant]:
    try:
        return db.query(models.DimRestaurant).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error querying restaurants: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Query locations
def read_location(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.DimLocation]:
    try:
        return db.query(models.DimLocation).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error querying locations: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Query dates
def read_date(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.DimDate]:
    try:
        return db.query(models.DimDate).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error querying dates: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Query reviews
def read_review(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    restaurant_id: Optional[str] = None,
    min_note: Optional[int] = None,
    max_note: Optional[int] = None
) -> List[schemas.FaitAvis]:
    try:
        query = db.query(models.FaitAvis)

        # Apply filters
        if restaurant_id:
            query = query.filter(models.FaitAvis.id_restaurant == restaurant_id)
        if min_note:
            query = query.filter(models.FaitAvis.note >= min_note)
        if max_note:
            query = query.filter(models.FaitAvis.note <= max_note)

        # serialized_reviews = [FaitAvisSchema.model_validate(avis) for avis in reviews]
        response = [schemas.FaitAvisBase.model_validate(avis) for avis in query.offset(skip).limit(limit).all()]
        # response = [schemas.FaitAvis.from_orm(avis) for avis in query.offset(skip).limit(limit).all()]
        print(response)
        return response
        # print(query)
        # Accessing attributes
        # result = schemas.FaitAvis.from_orm(query.first())
        # result = 
        # result = 
        # for avis in query:
        #     print(f"Restaurant ID: {avis.id_restaurant}")
            # print(f"Note: {avis.note}")
            # print(f"Commentaire: {avis.commentaire}")

        # return query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error querying reviews: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")
