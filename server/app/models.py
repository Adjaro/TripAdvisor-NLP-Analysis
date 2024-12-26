from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Table: dim_restaurant
class DimRestaurant(Base):
    __tablename__ = "dim_restaurant"
    id_restaurant = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=True)
    service = Column(String, nullable=True)
    type_cuisine = Column(String, nullable=True)
    website = Column(String, nullable=True)
    adresse = Column(String, nullable=True, index=True)

# Table: dim_date
class DimDate(Base):
    __tablename__ = "dim_date"
    id_date = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=True)
    mois = Column(Integer, nullable=True)
    annee = Column(Integer, nullable=True)

class DimAuteur(Base):
    __tablename__ = "dim_auteur"
    id_auteur = Column(Integer, primary_key=True, index=True)
    auteur = Column(String, nullable=True)
    email = Column(String, nullable=True)


class FaitNotes(Base):
    __tablename__ = "fait_avis"
    id_avis = Column(Integer, primary_key=True, index=True)
    id_restaurant = Column(Integer, ForeignKey("dim_restaurant.id_restaurant"))
    id_date = Column(Integer, ForeignKey("dim_date.id_date"))
    id_auteur = Column(Integer, ForeignKey("dim_auteur.id_auteur"))

    note = Column(Integer, nullable=True)
    note_cuisine = Column(Integer, nullable=True)
    note_service = Column(Integer, nullable=True)
    note_qualite_prix = Column(Integer, nullable=True)
    note_ambiance = Column(Integer, nullable=True)

    restaurant = relationship("DimRestaurant")
    date = relationship("DimDate")
    auteur = relationship("DimAuteur")



class FaitCommentaire(Base):
    __tablename__ = "fait_avis"
    id_avis = Column(Integer, primary_key=True, index=True)
    id_restaurant = Column(Integer, ForeignKey("dim_restaurant.id_restaurant"))
    id_date = Column(Integer, ForeignKey("dim_date.id_date"))
    id_auteur = Column(Integer, ForeignKey("dim_auteur.id_auteur"))

    commentaire = Column(String, nullable=True)

    restaurant = relationship("DimRestaurant")
    date = relationship("DimDate")
    auteur = relationship("DimAuteur")


class FaitAvis2(Base):
    nb_commentaire = Column(Integer, nullable=True)

    restaurant = relationship("DimRestaurant")
    date = relationship("DimDate")
    auteur = relationship("DimAuteur")

    restaurant = relationship("DimRestaurant")
    date = relationship("DimDate")
    auteur = relationship("DimAuteur")


# class FaitAvis2(Base):
#     __tablename__ = "fait_avis2"
#     id_avis = Column(Integer, primary_key=True, index=True)
#     id_restaurant = Column(Integer, ForeignKey("dim_restaurant.id_restaurant"))
#     id_date = Column(Integer, ForeignKey("dim_date.id_date"))
#     id_auteur = Column(Integer, ForeignKey("dim_auteur.id_auteur"))
#     note = Column(Integer, nullable=False)
#     commentaire = Column(String, nullable=True)
#     nb_commentaire = Column(Integer, nullable=True)
#     restaurant = relationship("DimRestaurant")
#     date = relationship("DimDate")
#     auteur = relationship("DimAuteur")