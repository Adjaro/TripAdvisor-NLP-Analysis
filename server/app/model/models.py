from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid


Base = declarative_base()

class DimLocation(Base):
    __tablename__ = "dim_location"
    id_location = Column(String, primary_key=True, index=True , default=lambda: str(uuid.uuid4()))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    adresse = Column(String, nullable=True, index=True)

class DimRestaurant(Base):
    __tablename__ = "dim_restaurant"
    id_restaurant = Column(String, primary_key=True, index=True , default=lambda: str(uuid.uuid4()) )
    nom = Column(String, nullable=True)
    id_location = Column(String, ForeignKey("dim_location.id_location"))

class DimDate(Base):
    __tablename__ = "dim_date"
    id_date = Column(String, primary_key=True, index=True , default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=True)
    jour = Column(String, nullable=True)
    mois = Column(String, nullable=True)
    annee = Column(String, nullable=True)

class FaitAvis(Base):
    __tablename__ = "fait_avis"
    id_avis = Column(String, primary_key=True, index=True , default=lambda: str(uuid.uuid4()) )
    id_restaurant = Column(String, ForeignKey("dim_restaurant.id_restaurant"))
    id_date = Column(String, ForeignKey("dim_date.id_date"))
    note = Column(Integer, nullable=True)