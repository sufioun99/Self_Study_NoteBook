from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from .database import init_db

app = FastAPI(title="Study Notebook", version="0.1.0")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_PATH = os.path.join(BASE_DIR, "app", "templates", "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    init_db()


def render_template():
    with open(TEMPLATE_PATH, "r") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=render_template())


@app.exception_handler(404)
async def not_found(request, exc):
    if request.url.path.startswith(("/api/", "/materials/", "/search/")):
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return HTMLResponse(content=render_template())


# Import and include routers after app is defined to avoid circular imports
from .routers import materials, search  # noqa: E402

app.include_router(materials.router)
app.include_router(search.router)
