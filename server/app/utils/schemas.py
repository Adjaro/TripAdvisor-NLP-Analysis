from pydantic import BaseModel,ConfigDict
from typing import Optional
from datetime import date

# Common base schema
class DimDateBase(BaseModel):
    date:  Optional[str]
    mois:  Optional[str]
    annee: Optional[str]


class DimAuteurBase(BaseModel):
    auteur: str
    email: Optional[str]


class FaitAvisBase(BaseModel):
    id_restaurant: int
    id_date: int
    id_auteur: int
    note: int
    commentaire: Optional[str]
    nb_commentaire: Optional[int]


# Create schemas
class DimDateCreate(DimDateBase):
    pass


class DimAuteurCreate(DimAuteurBase):
    pass


class FaitAvisCreate(FaitAvisBase):
    pass


# Response schemas
class DimDate(DimDateBase):
    id_date: int
    model_config = ConfigDict(from_attributes=True)


class DimAuteur(DimAuteurBase):
    id_auteur: int
    model_config = ConfigDict(from_attributes=True)


class FaitAvis(FaitAvisBase):
    id_avis: int
    model_config = ConfigDict(from_attributes=True)
