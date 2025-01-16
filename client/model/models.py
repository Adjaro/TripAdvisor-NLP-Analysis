from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class DimLocation(Base):
    __tablename__ = "dim_location"
    id_location = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    adresse = Column(String, nullable=True, index=True)

class DimRestaurant(Base):
    __tablename__ = "dim_restaurant"
    id_restaurant = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    nom = Column(String, nullable=True)
    classement = Column(Integer, nullable=True)
    horaires = Column(String, nullable=True)
    note_globale = Column(Float, nullable=True)
    note_cuisine = Column(Float, nullable=True)
    note_service = Column(Float, nullable=True)
    note_rapportqualiteprix = Column(Float, nullable=True)
    note_ambiance = Column(Float, nullable=True)
    infos_pratiques = Column(String, nullable=True)
    repas = Column(String, nullable=True)
    # regimes = Column(String, nullable=True)
    fourchette_prix = Column(String, nullable=True)
    fonctionnalites = Column(String, nullable=True)
    type_cuisines = Column(String, nullable=True)
    nb_avis = Column(Integer, nullable=True)
    nbExcellent = Column(Integer, nullable=True)
    nbTresbon = Column(Integer, nullable=True)
    nbMoyen = Column(Integer, nullable=True)
    nbMediocre = Column(Integer, nullable=True)
    nbHorrible = Column(Integer, nullable=True)
    id_location = Column(String, ForeignKey("dim_location.id_location"))

class DimDate(Base):
    __tablename__ = "dim_date"
    id_date = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=True)
    jour = Column(String, nullable=True)
    mois = Column(String, nullable=True)
    annee = Column(String, nullable=True)

class FaitAvis(Base):
    __tablename__ = "fait_avis"
    id_avis = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    id_restaurant = Column(String, ForeignKey("dim_restaurant.id_restaurant"))
    id_date = Column(String, ForeignKey("dim_date.id_date"))
    nb_etoiles = Column(Integer, nullable=True)
    experience = Column(String, nullable=True)
    review = Column(String, nullable=True)
    titre_avis = Column(String, nullable=True)


class RagAvis(Base):
    __tablename__ = "rag_avis"
    id_rag = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    restaurantName = Column(String, nullable=True)
    review = Column(String, nullable=True)
    embedding = Column(String, nullable=True)