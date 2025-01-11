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
def read_restaurant(db: Session, skip: int = 0, limit: int = 100) -> pd.DataFrame:
    try:
        restaurants = db.query(models.DimRestaurant).offset(skip).limit(limit).all()
        df = pd.DataFrame([schemas.DimRestaurant.from_orm(restaurant).dict() for restaurant in restaurants])
        return convert_to_arrow_compatible(df)
    except Exception as e:
        logger.error(f"Error querying restaurants: {e}")
        raise RuntimeError(f"Query failed: {str(e)}") from e

# Query locations
def read_location(db: Session, skip: int = 0, limit: int = 100) -> pd.DataFrame:
    try:
        locations = db.query(models.DimLocation).offset(skip).limit(limit).all()
        df = pd.DataFrame([schemas.DimLocation.from_orm(location).dict() for location in locations])
        return convert_to_arrow_compatible(df)
    except Exception as e:
        logger.error(f"Error querying locations: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Query dates
def read_date(db: Session, skip: int = 0, limit: int = 100) -> pd.DataFrame:
    try:
        dates = db.query(models.DimDate).offset(skip).limit(limit).all()
        df = pd.DataFrame([schemas.DimDate.from_orm(date).dict() for date in dates])
        return convert_to_arrow_compatible(df)
    except Exception as e:
        logger.error(f"Error querying dates: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Query reviews
def read_review(
    db: Session,
    skip: int = 0,
    limit: int = 5,
    restaurant_id: Optional[str] = None,
    min_note: Optional[int] = None,
    max_note: Optional[int] = None
) -> pd.DataFrame:
    try:
        query = db.query(models.FaitAvis)

        # Apply filters
        if restaurant_id:
            query = query.filter(models.FaitAvis.id_restaurant == restaurant_id)
        if min_note is not None:
            query = query.filter(models.FaitAvis.note >= min_note)
        if max_note is not None:
            query = query.filter(models.FaitAvis.note <= max_note)

        reviews = query.offset(skip).limit(limit).all()
        df = pd.DataFrame([schemas.FaitAvis.from_orm(review).dict() for review in reviews])
        return convert_to_arrow_compatible(df)
    except Exception as e:
        logger.error(f"Error querying reviews: {e}")
        raise RuntimeError(f"Query failed: {str(e)}")

# Convert DataFrame to Arrow-compatible format
def convert_to_arrow_compatible(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].astype(str)
        elif df[column].dtype == 'int64':
            df[column] = df[column].astype('int32')
    return df

# Example usage
def example_usage():
    db = next(get_db())
    try:
        restaurants_df = read_restaurant(db)
        print(restaurants_df)
    finally:
        db.close()

if __name__ == "__main__":
    example_usage()