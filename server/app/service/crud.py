from sqlalchemy.orm import Session
from model import models, schemas

# Create a new location entry
def create_location(db: Session, location: schemas.DimLocationCreate):
    db_location = models.DimLocation(
        latitude=location.latitude,
        longitude=location.longitude,
        adresse=location.adresse
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

# Read location entry by ID
def get_location(db: Session, location_id: int):
    return db.query(models.DimLocation).filter(models.DimLocation.id_location == location_id).first()

# Create a new restaurant entry
def create_restaurant(db: Session, restaurant: schemas.DimRestaurantCreate):
    db_restaurant = models.DimRestaurant(
        nom=restaurant.nom,
        id_location=restaurant.id_location
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

# Read restaurant entry by ID
def get_restaurant(db: Session, restaurant_id: int):
    return db.query(models.DimRestaurant).filter(models.DimRestaurant.id_restaurant == restaurant_id).first()

# Create a new date entry
def create_date(db: Session, date: schemas.DimDateCreate):
    db_date = models.DimDate(
        date=date.date,
        jour=date.jour,
        mois=date.mois,
        annee=date.annee
    )
    db.add(db_date)
    db.commit()
    db.refresh(db_date)
    return db_date

# Read date entry by ID
def get_date(db: Session, date_id: int):
    return db.query(models.DimDate).filter(models.DimDate.id_date == date_id).first()

# Create a new review entry
def create_review(db: Session, review: schemas.FaitAvisCreate):
    db_review = models.FaitAvis(
        id_restaurant=review.id_restaurant,
        id_date=review.id_date,
        note=review.note
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

# Read review entry by ID
def get_review(db: Session, review_id: int):
    return db.query(models.FaitAvis).filter(models.FaitAvis.id_avis == review_id).first()
