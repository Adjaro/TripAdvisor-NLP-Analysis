import json
from util import database
from model import models, schemas

# def get_db():
#     db = database.SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

models.Base.metadata.create_all(bind= database.engine)