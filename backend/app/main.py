from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import UserContext, get_current_user
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="BrandGuard API",
    description="Pre-publication brand governance platform API. AI suggests, humans decide.",
    version="0.1.0",
)

# CORS setup for frontend at http://localhost:3000
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint used by monitoring and frontend verification."""
    return {
        "status": "ok",
        "service": "brandguard-api",
        "mock_llm": settings.mock_llm,
        "llm_provider": settings.llm_provider,
    }


@app.get("/api/me", tags=["Auth"])
async def get_me(current_user: UserContext = Depends(get_current_user)):
    """Returns the authenticated user's profile, role, and org context."""
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "org_id": str(current_user.org_id),
        "role": current_user.role.value,
        "full_name": current_user.full_name,
    }
