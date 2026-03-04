# from fastapi import Depends, HTTPException
# from fastapi.security import OAuth2PasswordBearer
# from jose import jwt, JWTError
# from sqlalchemy.orm import Session
# from db.session import get_db
# from models.user import User
# from core.security import SECRET_KEY, ALGORITHM

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("user_id")

#         if not user_id:
#             raise HTTPException(status_code=401, detail="Invalid token")

#         user = db.query(User).filter(User.id == user_id).first()

#         if not user:
#             raise HTTPException(status_code=401, detail="User not found")

#         return user

#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or expired token")

# def role_required(roles: list):
#     def checker(user = Depends(get_current_user)):
#         if user.role.name not in roles:
#             raise HTTPException(status_code=403, detail="Operation not permitted")
#         return user
#     return checker

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from db.session import get_db
from models.user import User
from core.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User inactive")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def role_required(roles: list):
    def checker(user: User = Depends(get_current_user)):
        if user.role.name not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return user

    return checker