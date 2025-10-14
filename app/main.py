from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from . import crud, models
from .database import engine, get_db
from .routers import novels
from .templating import templates
from fastapi.staticfiles import StaticFiles

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="小说设定管理器")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(novels.router)

@app.get("/", response_class=HTMLResponse, summary="获取所有小说列表，展示首页")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Renders the main page with a list of all novels.
    """
    all_novels = crud.get_novels(db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "novels": all_novels}
    )

