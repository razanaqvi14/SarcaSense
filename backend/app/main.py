import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from .config import get_settings
from .database import Base, engine
from .ml.predictor import Predictor
from .ratelimit import limiter
from .routers import auth, history, predict

logger = logging.getLogger("sarcasm")
settings = get_settings()

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    app.state.predictor = Predictor(settings.model_path, settings.vocab_path)
    # Touch every lazily-loaded piece (WordNet, contractions, torch kernels) now, so the
    # memory they need is allocated before traffic arrives rather than during it.
    app.state.predictor.predict("warm up the model before serving traffic")
    logger.info("Model loaded and warmed up")
    yield


app = FastAPI(
    title="SarcaSense API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.enable_docs else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.enable_docs else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    """Cookie auth + state-changing request => require a header a cross-site form can't set.

    Setting a custom header forces a CORS preflight, and no cross-origin access is allowed.
    This is on top of SameSite=Strict on the session cookie.
    """
    if (
        request.method in _UNSAFE_METHODS
        and request.headers.get("x-requested-with") != "sarcasense"
    ):
        return JSONResponse({"detail": "Missing CSRF header"}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/live", tags=["meta"])
def live():
    """Liveness only: no database call. Used by hosts that probe often, so a scale-to-zero
    database is not kept awake by health checks."""
    return {"status": "ok"}


@app.get("/api/health", tags=["meta"])
def health(request: Request):
    """Liveness + readiness: the model is loaded and the database answers."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "model_loaded": hasattr(request.app.state, "predictor")}


app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
