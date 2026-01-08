"""Authentication API endpoints using magic links."""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import resend

from app.database import get_db
from app.models import User, MagicLinkAttempt, GameSession
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Initialize Resend
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    message: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    games_played: int
    wins_vs_benchmark: int
    losses_vs_benchmark: int


class SetUsernameRequest(BaseModel):
    username: str


def generate_magic_token() -> str:
    """Generate a secure random token for magic links."""
    return secrets.token_urlsafe(32)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from session token cookie."""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    
    user = db.query(User).filter(
        User.session_token == session_token,
        User.session_expires > datetime.utcnow()
    ).first()
    
    return user


def require_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Require authentication - raises 401 if not logged in."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/magic-link", response_model=MagicLinkResponse)
def request_magic_link(
    data: MagicLinkRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request a magic link to be sent to email."""
    email = data.email.lower()
    
    # Rate limiting: max 3 attempts per email per hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_attempts = db.query(MagicLinkAttempt).filter(
        MagicLinkAttempt.email == email,
        MagicLinkAttempt.attempted_at > one_hour_ago
    ).count()
    
    if recent_attempts >= 3:
        raise HTTPException(
            status_code=429, 
            detail="Too many login attempts. Please try again later."
        )
    
    # Record attempt
    attempt = MagicLinkAttempt(
        email=email,
        ip_address=request.client.host if request.client else None
    )
    db.add(attempt)
    
    # Get or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
    
    # Generate magic link token
    token = generate_magic_token()
    user.magic_link_token = token
    user.magic_link_expires = datetime.utcnow() + timedelta(
        minutes=settings.magic_link_expires_minutes
    )
    
    db.commit()
    
    # Build magic link URL
    magic_link_url = f"{settings.frontend_url}/auth/verify?token={token}"
    
    # Send email
    if settings.resend_api_key:
        try:
            resend.Emails.send({
                "from": "Hindsight Economics <noreply@notifications.diftar.co>",
                "to": [email],
                "subject": "Your login link for Hindsight Economics",
                "html": f"""
                    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1 style="color: #3b82f6;">Hindsight Economics</h1>
                        <p>Click the link below to log in:</p>
                        <p>
                            <a href="{magic_link_url}" 
                               style="display: inline-block; background: #3b82f6; color: white; 
                                      padding: 12px 24px; text-decoration: none; border-radius: 8px;">
                                Log In
                            </a>
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            This link expires in {settings.magic_link_expires_minutes} minutes.
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            If you didn't request this, you can safely ignore this email.
                        </p>
                    </div>
                """
            })
        except Exception as e:
            # Log the magic link so you can still use it (helpful for testing with Resend free tier)
            print(f"[EMAIL FAILED] Magic link for {email}: {magic_link_url}")
            print(f"[EMAIL ERROR] {e}")
            # NOTE: On Resend's free tier, you can only send to the email you registered with.
            # To send to other emails: 1) Verify your own domain in Resend, or 2) Add emails to Resend Audience
            if settings.environment == "production":
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to send email. If using Resend free tier, you may need to verify a custom domain."
                )
    else:
        # In development without Resend, log the link
        print(f"[DEV] Magic link for {email}: {magic_link_url}")
    
    return MagicLinkResponse(
        message="If an account exists, a login link has been sent to your email."
    )


@router.get("/verify")
def verify_magic_link(
    token: str,
    game_token: Optional[str] = None,  # Optional: link a recent game
    db: Session = Depends(get_db)
):
    """Verify magic link and create session."""
    user = db.query(User).filter(
        User.magic_link_token == token,
        User.magic_link_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    
    # Clear magic link token
    user.magic_link_token = None
    user.magic_link_expires = None
    
    # Create session
    session_token = generate_magic_token()
    user.session_token = session_token
    user.session_expires = datetime.utcnow() + timedelta(days=settings.session_expires_days)
    user.last_login = datetime.utcnow()
    
    # Link recent anonymous game if provided
    if game_token:
        game = db.query(GameSession).filter(
            GameSession.session_token == game_token,
            GameSession.user_id.is_(None)
        ).first()
        if game:
            game.user_id = user.id
            # Update username if user has one and game doesn't
            if user.username and not game.username:
                game.username = user.username
    
    db.commit()
    
    # Return JSON response with cookie set
    # (Frontend handles redirect - can't set cookies via redirect with redirect: 'manual')
    response = Response(
        content='{"success": true, "has_username": ' + ('true' if user.username else 'false') + '}',
        media_type="application/json"
    )
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="none",
        max_age=settings.session_expires_days * 24 * 60 * 60
    )
    
    return response


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db)):
    """Log out - clear session."""
    response.delete_cookie("session_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(require_auth)):
    """Get current user info."""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        games_played=user.games_played or 0,
        wins_vs_benchmark=user.wins_vs_benchmark or 0,
        losses_vs_benchmark=user.losses_vs_benchmark or 0
    )


@router.post("/username", response_model=UserResponse)
def set_username(
    data: SetUsernameRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Set or update username."""
    username = data.username.strip()
    
    # Validate username
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(
            status_code=400, 
            detail="Username must be 3-20 characters"
        )
    
    if not username.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Username can only contain letters, numbers, underscores, and hyphens"
        )
    
    # Check if username is taken
    existing = db.query(User).filter(
        User.username == username,
        User.id != user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user.username = username
    
    # Update any games to use this username
    db.query(GameSession).filter(
        GameSession.user_id == user.id
    ).update({GameSession.username: username})
    
    db.commit()
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        games_played=user.games_played or 0,
        wins_vs_benchmark=user.wins_vs_benchmark or 0,
        losses_vs_benchmark=user.losses_vs_benchmark or 0
    )


@router.post("/link-game/{game_token}")
def link_game_to_user(
    game_token: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Link an anonymous game to the current user."""
    game = db.query(GameSession).filter(
        GameSession.session_token == game_token
    ).first()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.user_id is not None and game.user_id != user.id:
        raise HTTPException(status_code=400, detail="Game belongs to another user")
    
    if game.user_id == user.id:
        return {"message": "Game already linked"}
    
    game.user_id = user.id
    if user.username and not game.username:
        game.username = user.username
    
    db.commit()
    
    return {"message": "Game linked to your account"}

