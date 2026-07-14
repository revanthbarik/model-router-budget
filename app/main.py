from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

ROOT_DIR = Path(__file__).resolve().parent.parent


def _resolve_static_dir() -> Path:
    # Prefer ./static so FileResponse works inside the Vercel Python bundle.
    # public/static is CDN-only and may not exist on the function filesystem.
    for candidate in (ROOT_DIR / "static", ROOT_DIR / "public" / "static"):
        if candidate.is_dir():
            return candidate
    return ROOT_DIR / "static"


STATIC_DIR = _resolve_static_dir()

# No lifespan DB init: on Vercel, a failed lifespan makes uvicorn shut down and
# the runtime reports "Python process exited with exit status: 0".
app = FastAPI(title="Model Router Budget API")
app.include_router(router)

# Local + serverless fallback for /static/*. On Vercel, public/static is also
# served from the CDN at the same path.
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")



def _page(name: str) -> FileResponse:
    path = STATIC_DIR / name
    if not path.is_file():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Missing UI file {name!r}. Expected under {STATIC_DIR}. "
                "Redeploy with the static/ directory included."
            ),
        )
    return FileResponse(path)


@app.get("/")
def root():
    return RedirectResponse(url="/home")


@app.get("/ui")
def ui():
    return RedirectResponse(url="/home")


@app.get("/home")
def home_page():
    return _page("home.html")


@app.get("/chat")
def chat_page():
    return _page("chat.html")


@app.get("/admin")
def admin_page():
    return _page("admin.html")
