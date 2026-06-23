import logging
from fastapi import APIRouter, HTTPException, status, Depends
from crag_with_langsmith_tracing.backend.api.schemas import ErrorResponse
from crag_with_langsmith_tracing.backend.api.auth.schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    TokenRefreshRequest, ForgotPasswordRequest, ResetPasswordRequest
)
from crag_with_langsmith_tracing.backend.services.auth.service import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_refresh_token, revoke_refresh_token, get_user_by_email, create_user,
    create_password_reset_token, verify_password_reset_token, update_user_password
)
from crag_with_langsmith_tracing.backend.api.dependencies import verify_auth_rate_limit

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

router = APIRouter()

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_auth_rate_limit)],
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def signup(request: UserRegister):
    existing_user = get_user_by_email(request.email)
    if existing_user:
        access_logger.info(f"Signup failed: Email {request.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email address is already registered. Please login instead."
        )
    
    password_hash = hash_password(request.password)
    user = create_user(request.email, password_hash, request.full_name)
    if not user:
        access_logger.error(f"Signup failed: DB write error for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user."
        )
        
    access_logger.info(f"Signup successful: User registered with email {request.email}")
    return UserResponse(
        id=user["_id"],
        email=user["email"],
        full_name=user["full_name"]
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_auth_rate_limit)],
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def login(request: UserLogin):
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.password, user["password_hash"]):
        access_logger.info(f"Login failed: Invalid credentials for email {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
        
    access_token = create_access_token(user["_id"], user["email"])
    refresh_token = create_refresh_token(user["_id"], user["email"])
    
    access_logger.info(f"Login successful: Session established for user {user['email']}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_auth_rate_limit)],
    responses={
        400: {"model": ErrorResponse}
    }
)
async def logout(request: TokenRefreshRequest):
    success = revoke_refresh_token(request.refresh_token)
    if not success:
        access_logger.warning("Logout failed: Invalid or expired refresh token passed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed: The refresh token provided is invalid or has already been revoked."
        )
        
    access_logger.info("Logout successful: Refresh token revoked and session terminated")
    return {"message": "Logged out successfully."}

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_auth_rate_limit)],
    responses={
        401: {"model": ErrorResponse}
    }
)
async def refresh(request: TokenRefreshRequest):
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        access_logger.warning("Token refresh failed: Invalid refresh token signature or token revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in again."
        )
        
    user_id = payload.get("sub")
    email = payload.get("email")
    
    revoke_refresh_token(request.refresh_token)
    
    new_access_token = create_access_token(user_id, email)
    new_refresh_token = create_refresh_token(user_id, email)
    
    access_logger.info(f"Token refresh successful: Access and Refresh tokens rotated for user {email}")
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_auth_rate_limit)]
)
async def forgot_password(request: ForgotPasswordRequest):
    user = get_user_by_email(request.email)
    if user:
        reset_token = create_password_reset_token(user["email"])
        access_logger.info(f"Forgot password successful: Reset token generated for {user['email']}")
    else:
        access_logger.info(f"Forgot password request for non-existent email: {request.email}")
        
    return {
        "message": "If an account exists with the provided email, a password reset link has been sent."
    }

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_auth_rate_limit)],
    responses={
        400: {"model": ErrorResponse}
    }
)
async def reset_password(request: ResetPasswordRequest):
    email = verify_password_reset_token(request.token)
    if not email:
        access_logger.warning("Password reset failed: Invalid or expired reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The password reset link is invalid or has expired. Please request a new one."
        )
        
    user = get_user_by_email(email)
    if user and verify_password(request.new_password, user["password_hash"]):
        access_logger.warning(f"Password reset failed: New password matches current password for {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password."
        )
        
    password_hash = hash_password(request.new_password)
    success = update_user_password(email, password_hash)
    if not success:
        access_logger.error(f"Password reset failed: DB update error for {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update password. Please try again later."
        )
        
    access_logger.info(f"Password reset successful: Password changed for user {email}")
    return {"message": "Password reset successfully."}
