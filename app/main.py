from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from . import crud, models
from .database import engine, get_db
from .routers import novels, auth_router
from .templating import templates
from .auth import try_get_current_user_from_cookie
from fastapi.staticfiles import StaticFiles

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="小说设定管理器")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_router.router)
app.include_router(novels.router)


@app.get("/", response_class=HTMLResponse, summary="获取所有小说列表，展示首页")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    Renders the main page with a list of all novels for the current user.
    If not logged in, redirects to the login page.
    """
    user = await try_get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login")

    all_novels = crud.get_novels_by_owner(db, owner_id=user.id)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "novels": all_novels, "user": user}
    )

