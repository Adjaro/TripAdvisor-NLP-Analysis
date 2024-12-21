from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, database
from pydantic import BaseModel
from .scraper import TripadvisorScraper

app = FastAPI()

class ItemCreate(BaseModel):
    name: str
    description: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup():
    models.Base.metadata.create_all(bind=database.engine)

@app.post("/items/")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/scrape/")
def scrape_restaurant(url, driver_path):
    # # Exemple d'utilisation
    # url = 'https://www.tripadvisor.fr/Restaurant_Review-g187265-d3727154-Reviews-Les_Terrasses_de_Lyon-Lyon_Rhone_Auvergne_Rhone_Alpes.html'
    # driver_path = 'path/to/chromedriver.exe'
    # scraper = TripadvisorScraper(url, driver_path)
    # scraper.scrape()
   
    scrape = TripadvisorScraper(url, driver_path)
    scrape.scrape()
    return {"message": "Scraping terminé, données sauvegardées dans restaurant_data.json."}




@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()