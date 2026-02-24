from fastapi import FastAPI
from db.session import engine, Base
from db.base import *
from api import auth, users

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])