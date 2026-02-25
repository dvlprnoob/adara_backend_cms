from sqlalchemy.orm import Session
from models.user import User
from models.role import Role
from core.security import hash_password


def seed_roles(db: Session):
    roles = ["super_admin", "admin", "resident"]
    
    for r in roles:
        existing = db.query(Role).filter(Role.name == r).first()
        if not existing:
            db.add(Role(name=r))
    
    db.commit()
    
def seed_super_admin(db: Session):
    super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
    
    if not super_admin_role:
        return 
    
    existing_admin = db.query(User).filter(
        User.email == "superadmin@aeg.com"
    ).first()
    
    if not existing_admin:
        new_admin = User(
            name="Super Admin",
            email="superadmin@aeg.com",
            password=hash_password("SuperAdmin123!"),
            role_id=super_admin_role.id
        )
        
        db.add(new_admin)
        db.commit()
        