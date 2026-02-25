from fastapi import FastAPI
from db.session import engine, Base, SessionLocal
from db.base import *
from db.seed import seed_roles, seed_super_admin
from api import auth, users, banners


app = FastAPI()

Base.metadata.create_all(bind=engine)

# Seed roles saat startup
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    seed_roles(db)
    seed_super_admin(db)
    db.close()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(banners.router, prefix="/banners", tags=["Banners"])