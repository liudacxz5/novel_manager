from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .. import crud, schemas, auth
from ..config import settings
from ..database import get_db
from ..templating import templates

router = APIRouter(
    tags=["authentication"]
)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=RedirectResponse)
async def login_for_access_token(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=username)
    if not user or not auth.verify_password(password, user.hashed_password):
        # Redirect back to login page with an error query parameter
        return RedirectResponse(url="/login?error=true", status_code=status.HTTP_303_SEE_OTHER)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Create a RedirectResponse and set the cookie on it before returning
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=RedirectResponse)
async def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Validate password length to prevent argon2/bcrypt error
    if len(password.encode('utf-8')) > 72:
        return RedirectResponse(url="/register?error=long_password", status_code=status.HTTP_303_SEE_OTHER)

    db_user = crud.get_user_by_username(db, username=username)
    if db_user:
        return RedirectResponse(url="/register?error=username_exists", status_code=status.HTTP_303_SEE_OTHER)

    user = schemas.UserCreate(username=username, password=password)
    crud.create_user(db=db, user=user)

    # Redirect to login with a success message
    return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/logout", response_class=RedirectResponse)
async def logout():
    # Create a redirect response to the login page with a success query param
    response = RedirectResponse(url="/login?logged_out=true", status_code=status.HTTP_303_SEE_OTHER)
    # Delete the access_token cookie from this response
    response.delete_cookie(key="access_token")
    return response

