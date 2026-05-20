from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.uploads import UPLOAD_ROOT
from db.session import engine, Base, SessionLocal
from db.schema_migrations import ensure_installment_due_date_column, ensure_progress_warranty_columns
from db.base import *
from db.seed import seed_roles, seed_super_admin
from api import auth, users, banners, roles, services, emergency_type, emergency_report, ipl, installment, payment_method, progress, chat, service_report


app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")

Base.metadata.create_all(bind=engine)
ensure_installment_due_date_column(engine)
ensure_progress_warranty_columns(engine)

# Seed roles saat startup
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_roles(db)
        seed_super_admin(db)
    finally:
        db.close()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(banners.router, prefix="/banners", tags=["Banners"])
app.include_router(roles.router, prefix="/roles", tags=["Roles"])
app.include_router(services.router, prefix="/services", tags=["Services"])
app.include_router(emergency_type.router, prefix="/emergency-types", tags=["Emergency Types"])
app.include_router(emergency_report.router, prefix="/emergency-reports", tags=["Emergency Reports"])
app.include_router(ipl.router, prefix="/ipls", tags=["IPLs"])
app.include_router(installment.router, prefix="/installments", tags=["Installments"])
app.include_router(payment_method.router, prefix="/payment-methods", tags=['Payment Method'])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])
app.include_router(chat.router, prefix="/chats", tags=["Chats"])
app.include_router(service_report.router, prefix="/service-reports", tags=["Service Reports"])
