from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .model import models, schemas
from .utils import database
from pydantic import BaseModel
from .scraper import TripadvisorScraper
from .alimentationBd import insert_json_data, get_data_list, read_json_file
import os
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def check_existing_data(db: Session, nom_restaurant: str, address: str) -> bool:
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

@app.on_event("startup")
async def startup():
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
            data_exists = await check_existing_data(db, data['nom'], data['adresse'])
            if not data_exists:
                logger.info("Inserting initial data...")
                await insert_json_data(data_dir)
            else:
                logger.info("Data already exists in database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/scrape")
def scrape(url: str):
    try:
        scraper = TripadvisorScraper(url)
        scraper.scrapper()
        # return {"message": "Scraping successful"}
        data = scraper.data
        return data
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/allrestaurants", response_model=List[schemas.DimRestaurant])
def read_restaurant(db: Session = Depends(get_db)):
    try:
        return db.query(models.DimRestaurant).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/location", response_model=List[schemas.DimLocation])
def read_location(db: Session = Depends(get_db)):
    try:
        return db.query(models.DimLocation).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/date", response_model=List[schemas.DimDate])
def read_date(db: Session = Depends(get_db)):
    try:
        return db.query(models.DimDate).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/review", response_model=List[schemas.FaitAvis])
def read_review(db: Session = Depends(get_db)):
    try:
        return db.query(models.FaitAvis).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))