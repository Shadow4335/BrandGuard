from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import content, core, insights, review, sources, workflow

settings = get_settings()

app = FastAPI(
    title="BrandGuard API",
    description="Pre-publication brand governance platform API. AI suggests, humans decide.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def announce() -> None:
    import os
    print(f"BrandGuard API {settings.app_version} commit={os.getenv('RENDER_GIT_COMMIT', 'local')[:7]} "
          f"store={'supabase' if settings.use_supabase else 'memory'} ai_live={settings.llm_available}", flush=True)


@app.exception_handler(Exception)
async def friendly_errors(request: Request, exc: Exception):
    """Never leak a stack trace to the UI."""
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def root():
    return {"service": "brandguard-api", "docs": "/docs", "health": "/api/health"}


@app.get("/health", tags=["Health"])
def legacy_health():
    return {"status": "ok", "service": "brandguard-api"}


app.include_router(core.router)
app.include_router(sources.router)
app.include_router(content.router)
app.include_router(review.router)
app.include_router(workflow.router)
app.include_router(insights.router)
