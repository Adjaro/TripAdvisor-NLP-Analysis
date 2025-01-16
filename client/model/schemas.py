from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
import string
# from uuid import UUID
# Common base schema
class DimLocationBase(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    adresse: Optional[str]
    # model_config = {
    #     "from_attributes": True
    # }

class DimRestaurantBase(BaseModel):
    nom: Optional[str]
    classement: Optional[int]
    horaires: Optional[str]
    note_globale: Optional[float]
    note_cuisine: Optional[float]
    note_service: Optional[float]
    note_rapportqualiteprix: Optional[float]
    note_ambiance: Optional[float]
    infos_pratiques: Optional[str]
    repas: Optional[str]
    # regimes: Optional[str]
    fourchette_prix: Optional[str]
    fonctionnalites: Optional[str]
    type_cuisines: Optional[str]
    nb_avis: Optional[int]
    nbExcellent: Optional[int]
    nbTresbon: Optional[int]
    nbMoyen: Optional[int]
    nbMediocre: Optional[int]
    nbHorrible: Optional[int]

    id_location: Optional[str]

class DimDateBase(BaseModel):
    date: Optional[date]
    jour: Optional[str]
    mois: Optional[str]
    annee: Optional[str]

class FaitAvisBase(BaseModel):
    id_restaurant: str
    id_date: str
    # experience: Optional[str]
    review: Optional[str]
    # titre_avis: Optional[str]
    nb_etoiles: Optional[int]

class RagAvisBase(BaseModel):
    restaurantName: Optional[str]
    review: Optional[str]

    
# Create schemas
class DimLocationCreate(DimLocationBase):
    pass

class DimRestaurantCreate(DimRestaurantBase):
    pass

class DimDateCreate(DimDateBase):
    pass

class FaitAvisCreate(FaitAvisBase):
    pass

# Response schemas
class DimLocation(DimLocationBase):
    id_location: str
    model_config = ConfigDict(from_attributes=True)

class DimRestaurant(DimRestaurantBase):
    id_restaurant: str
    model_config = ConfigDict(from_attributes=True)

class DimDate(DimDateBase):
    id_date: str
    model_config = ConfigDict(from_attributes=True)

class FaitAvis(FaitAvisBase):
    id_avis: str
    model_config = ConfigDict(from_attributes=True)

class RagAvis(RagAvisBase):
    id_rag: str
    model_config = ConfigDict(from_attributes=True)