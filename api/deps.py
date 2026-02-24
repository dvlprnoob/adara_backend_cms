from fastapi import Depends, HTTPException, Header
from jose import jwt
from core.security import SECRET_KEY, ALGORITHM

def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload

def role_required(roles: list):
    def checker(user = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return user
    return checker