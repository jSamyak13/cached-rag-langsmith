import re
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def check_email(email: str) -> str:
    if not EMAIL_REGEX.match(email):
        raise ValueError("Invalid email format.")
    return email.lower().strip()

class UserRegister(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., min_length=12, description="User's password.")
    full_name: str = Field(..., description="User's full name.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

class UserLogin(BaseModel):
    email: str = Field(..., description="User's email address.")
    password: str = Field(..., description="User's password.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

class UserResponse(BaseModel):
    id: str = Field(..., description="User's unique database ID.")
    email: str = Field(..., description="User's email address.")
    full_name: str = Field(..., description="User's full name.")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Short-lived JWT access token.")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token.")
    token_type: str = Field("bearer", description="Token authentication type.")

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to request a new access token.")

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User's email address to request reset.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return check_email(v)

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token.")
    new_password: str = Field(..., min_length=12, description="New password.")
