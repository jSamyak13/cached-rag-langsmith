import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from crag_with_langsmith_tracing.backend.clients.mongodb_client import mongo_client
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id: str, email: str) -> str:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "jti": jti,
        "exp": expire,
        "type": "refresh"
    }
    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    if mongo_client:
        try:
            db = mongo_client[settings.MONGODB_DB]
            db["refresh_tokens"].insert_one({
                "jti": jti,
                "user_id": user_id,
                "expires_at": expire,
                "revoked": False
            })
        except Exception as e:
            logger.error(f"Error persisting refresh token JTI: {e}")
            
    return token

def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None

def verify_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        
        jti = payload.get("jti")
        if mongo_client:
            db = mongo_client[settings.MONGODB_DB]
            stored_token = db["refresh_tokens"].find_one({"jti": jti, "revoked": False})
            if not stored_token:
                access_logger.warning(f"Replay attack or revoked token attempt detected for JTI")
                return None
        return payload
    except jwt.PyJWTError:
        return None

def revoke_refresh_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("jti")
        if mongo_client:
            db = mongo_client[settings.MONGODB_DB]
            db["refresh_tokens"].update_many({"jti": jti}, {"$set": {"revoked": True}})
            return True
    except jwt.PyJWTError:
        pass
    return False

def get_user_by_email(email: str) -> Optional[dict]:
    if not mongo_client:
        return None
    try:
        db = mongo_client[settings.MONGODB_DB]
        user = db["users"].find_one({"email": email.lower().strip()})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        return None

def create_user(email: str, password_hash: str, full_name: str) -> Optional[dict]:
    if not mongo_client:
        return None
    try:
        db = mongo_client[settings.MONGODB_DB]
        new_user = {
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "full_name": full_name,
            "created_at": datetime.now(timezone.utc)
        }
        res = db["users"].insert_one(new_user)
        new_user["_id"] = str(res.inserted_id)
        return new_user
    except Exception as e:
        logger.error(f"Error creating user in DB: {e}")
        return None

def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": email.lower().strip(),
        "action": "password_reset",
        "exp": expire
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("action") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

def update_user_password(email: str, new_password_hash: str) -> bool:
    if not mongo_client:
        return False
    try:
        db = mongo_client[settings.MONGODB_DB]
        res = db["users"].update_one(
            {"email": email.lower().strip()},
            {"$set": {"password_hash": new_password_hash}}
        )
        return res.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating user password: {e}")
        return False
