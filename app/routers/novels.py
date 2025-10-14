from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from .. import crud, schemas, models, auth
from ..database import get_db
from ..templating import templates

router = APIRouter(
    prefix="/novels",
    tags=["novels"]
)

# --- Novel Routes ---
@router.get("/new", response_class=HTMLResponse)
async def show_create_novel_form(request: Request, current_user: models.User = Depends(
    auth.get_current_user_from_cookie)):
    return templates.TemplateResponse("create_novel.html", {"request": request, "user": current_user})

@router.post("/", response_class=RedirectResponse)
async def handle_create_novel(
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        title: str = Form(...),
        author: str = Form(None),
        description: str = Form(None),
        db: Session = Depends(get_db)
):
    novel_data = schemas.NovelCreate(title=title, author=author, description=description)
    crud.create_novel(db=db, novel=novel_data, owner_id=current_user.id)
    return RedirectResponse(url="/", status_code=303)

@router.get("/{novel_id}", response_class=HTMLResponse)
async def read_novel_details(
        request: Request,
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    db_novel = crud.get_novel(db, novel_id=novel_id, owner_id=current_user.id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")

    setting_types = crud.get_setting_types_by_novel(db, novel_id=novel_id)

    return templates.TemplateResponse(
        "novel_detail.html",
        {
            "request": request,
            "novel": db_novel,
            "setting_types": setting_types,
            "user": current_user,
            "db": db # For internal link filter
        }
    )

@router.get("/{novel_id}/edit", response_class=HTMLResponse)
async def show_edit_novel_form(
        request: Request,
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")
    return templates.TemplateResponse("edit_novel.html", {"request": request, "novel": novel, "user": current_user})

@router.post("/{novel_id}/edit", response_class=RedirectResponse)
async def handle_edit_novel(
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        title: str = Form(...),
        author: str = Form(None),
        description: str = Form(None),
        db: Session = Depends(get_db)
):
    novel_data = schemas.NovelUpdate(title=title, author=author, description=description)
    crud.update_novel(db, novel_id=novel_id, novel_update=novel_data, owner_id=current_user.id)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

@router.post("/{novel_id}/delete", response_class=RedirectResponse)
async def handle_delete_novel(
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    crud.delete_novel(db, novel_id=novel_id, owner_id=current_user.id)
    return RedirectResponse(url="/", status_code=303)

# --- Routes for Setting Types ---
@router.get("/{novel_id}/types/new", response_class=HTMLResponse)
async def show_create_type_form(
        request: Request,
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")
    return templates.TemplateResponse("create_type.html", {"request": request, "novel": novel, "user": current_user})

@router.post("/{novel_id}/types/new", response_class=RedirectResponse)
async def handle_create_type(
        novel_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        name: str = Form(...),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")
    type_data = schemas.SettingTypeCreate(name=name)
    crud.create_setting_type(db, setting_type=type_data, novel_id=novel_id)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

# --- Routes for Setting Entries ---
@router.get("/{novel_id}/entries/new", response_class=HTMLResponse)
async def show_create_entry_form(
        request: Request,
        novel_id: int,
        type_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    setting_type = crud.get_setting_type(db, type_id)
    if not novel or not setting_type or setting_type.novel_id != novel.id:
        raise HTTPException(404, "Resource not found")
    return templates.TemplateResponse("edit_entry.html", {"request": request, "novel": novel, "setting_type": setting_type, "entry": None, "is_new": True, "user": current_user})

@router.post("/{novel_id}/entries/new", response_class=RedirectResponse)
async def handle_create_entry(
        novel_id: int,
        type_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        name: str = Form(...),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    setting_type = crud.get_setting_type(db, type_id)
    if not novel or not setting_type or setting_type.novel_id != novel.id:
        raise HTTPException(404, "Resource not found")

    entry_data = schemas.SettingEntryCreate(name=name)
    new_entry = crud.create_setting_entry(db, entry=entry_data, novel_id=novel_id, type_id=type_id)
    return RedirectResponse(url=f"/novels/{novel_id}/entries/{new_entry.id}/edit", status_code=303)

@router.get("/{novel_id}/entries/{entry_id}/edit", response_class=HTMLResponse)
async def show_edit_entry_form(
        request: Request,
        novel_id: int,
        entry_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    entry = crud.get_setting_entry(db, entry_id)
    if not novel or not entry or entry.novel_id != novel.id:
        raise HTTPException(404, "Resource not found")
    return templates.TemplateResponse("edit_entry.html", {"request": request, "novel": novel, "setting_type": entry.setting_type, "entry": entry, "is_new": False, "user": current_user})

@router.post("/{novel_id}/entries/{entry_id}/edit", response_class=RedirectResponse)
async def handle_edit_entry(
        request: Request,
        novel_id: int,
        entry_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    entry = crud.get_setting_entry(db, entry_id)
    if not novel or not entry or entry.novel_id != novel.id:
        raise HTTPException(404, "Resource not found")

    form_data = await request.form()
    entry_name = form_data.get("name")

    fields = []
    keys = form_data.getlist("field_key")
    values = form_data.getlist("field_value")
    ids = form_data.getlist("field_id")

    for i in range(len(keys)):
        fields.append({
            "id": ids[i] if i < len(ids) and ids[i] else None,
            "key": keys[i],
            "value": values[i]
        })

    crud.update_setting_entry_with_fields(db, entry_id=entry_id, name=entry_name, fields_data=fields)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)


@router.post("/entries/{entry_id}/delete", response_class=RedirectResponse)
async def handle_delete_entry(
        entry_id: int,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    entry = crud.get_setting_entry(db, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")

    # Check ownership via the novel
    novel = crud.get_novel(db, entry.novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(403, "Not authorized to delete this entry")

    novel_id = entry.novel_id
    crud.delete_setting_entry(db, entry_id=entry_id)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

# --- Sorting Routes ---
@router.post("/{novel_id}/types/reorder", response_class=Response)
async def handle_reorder_types(
        novel_id: int,
        request: Request,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")

    type_ids = await request.json()
    crud.reorder_setting_types(db, novel_id=novel_id, type_ids=type_ids)
    return Response(status_code=200)


@router.post("/types/{type_id}/entries/reorder", response_class=Response)
async def handle_reorder_entries(
        type_id: int,
        request: Request,
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    setting_type = crud.get_setting_type(db, type_id)
    if not setting_type:
        raise HTTPException(404, "Type not found")

    # Check ownership via the novel
    novel = crud.get_novel(db, setting_type.novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(403, "Not authorized")

    entry_ids = await request.json()
    crud.reorder_setting_entries(db, type_id=type_id, entry_ids=entry_ids)
    return Response(status_code=200)

