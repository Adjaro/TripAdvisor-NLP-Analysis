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

class DimRestaurantBase(BaseModel):
    nom: Optional[str]
    id_location: Optional[str]

class DimDateBase(BaseModel):
    date: Optional[date]
    jour: Optional[str]
    mois: Optional[str]
    annee: Optional[str]

class FaitAvisBase(BaseModel):
    id_restaurant: str
    id_date: str
    note: Optional[int]

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