from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db
from ..templating import templates

router = APIRouter(
    prefix="/novels",
    tags=["novels"]
)

# --- Novel Routes ---
@router.get("/new", response_class=HTMLResponse)
async def show_create_novel_form(request: Request):
    return templates.TemplateResponse("create_novel.html", {"request": request})

@router.post("/", response_class=RedirectResponse)
async def handle_create_novel(
        title: str = Form(...),
        author: str = Form(None),
        description: str = Form(None),
        db: Session = Depends(get_db)
):
    novel_data = schemas.NovelCreate(title=title, author=author, description=description)
    crud.create_novel(db=db, novel=novel_data)
    return RedirectResponse(url="/", status_code=303)

@router.get("/{novel_id}", response_class=HTMLResponse)
async def read_novel_details(request: Request, novel_id: int, db: Session = Depends(get_db)):
    db_novel = crud.get_novel(db, novel_id=novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")

    setting_types = crud.get_setting_types_by_novel(db, novel_id=novel_id)

    return templates.TemplateResponse(
        "novel_detail.html",
        {
            "request": request,
            "novel": db_novel,
            "setting_types": setting_types,
            "db": db  # Pass the db session to the template context
        }
    )

@router.get("/{novel_id}/edit", response_class=HTMLResponse)
async def show_edit_novel_form(request: Request, novel_id: int, db: Session = Depends(get_db)):
    db_novel = crud.get_novel(db, novel_id)
    if db_novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return templates.TemplateResponse("edit_novel.html", {"request": request, "novel": db_novel})

@router.post("/{novel_id}/edit", response_class=RedirectResponse)
async def handle_edit_novel(
        novel_id: int,
        title: str = Form(...),
        author: str = Form(None),
        description: str = Form(None),
        db: Session = Depends(get_db)
):
    novel_data = schemas.NovelUpdate(title=title, author=author, description=description)
    crud.update_novel(db, novel_id=novel_id, novel_update=novel_data)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

@router.post("/{novel_id}/delete", response_class=RedirectResponse)
async def handle_delete_novel(novel_id: int, db: Session = Depends(get_db)):
    crud.delete_novel(db, novel_id=novel_id)
    return RedirectResponse(url="/", status_code=303)

# --- Routes for Setting Types ---
@router.get("/{novel_id}/types/new", response_class=HTMLResponse)
async def show_create_type_form(request: Request, novel_id: int, db: Session = Depends(get_db)):
    novel = crud.get_novel(db, novel_id)
    return templates.TemplateResponse("create_type.html", {"request": request, "novel": novel})

@router.post("/{novel_id}/types/new", response_class=RedirectResponse)
async def handle_create_type(novel_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    type_data = schemas.SettingTypeCreate(name=name)
    crud.create_setting_type(db, setting_type=type_data, novel_id=novel_id)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

# --- Routes for Setting Entries ---
@router.get("/{novel_id}/entries/new", response_class=HTMLResponse)
async def show_create_entry_form(request: Request, novel_id: int, type_id: int, db: Session = Depends(get_db)):
    # This route now directly handles the creation and redirects to the edit view of the detail page
    novel = crud.get_novel(db, novel_id)
    setting_type = crud.get_setting_type(db, type_id)
    if not novel or not setting_type or setting_type.novel_id != novel.id:
        raise HTTPException(404, "Novel or Setting Type not found")

    # Create a new entry with a default name and redirect
    entry_data = schemas.SettingEntryCreate(name=f"新 {setting_type.name}")
    new_entry = crud.create_setting_entry(db, entry=entry_data, novel_id=novel_id, type_id=type_id)

    # Redirect to the main detail page, with a hash to the new, editable entry
    return RedirectResponse(url=f"/novels/{novel_id}#entry-{new_entry.id}", status_code=303)


@router.post("/entries/{entry_id}/edit", response_class=RedirectResponse)
async def handle_edit_entry(request: Request, entry_id: int, db: Session = Depends(get_db)):
    form_data = await request.form()
    entry = crud.get_setting_entry(db, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")

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
    return RedirectResponse(url=f"/novels/{entry.novel_id}#entry-{entry_id}", status_code=303)

@router.post("/entries/{entry_id}/delete", response_class=RedirectResponse)
async def handle_delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_setting_entry(db, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    novel_id = entry.novel_id
    crud.delete_setting_entry(db, entry_id=entry_id)
    return RedirectResponse(url=f"/novels/{novel_id}", status_code=303)

@router.post("/entries/{entry_id}/move/{direction}", response_class=RedirectResponse)
async def handle_reorder_entry(entry_id: int, direction: str, db: Session = Depends(get_db)):
    entry = crud.reorder_setting_entry(db, entry_id, direction)
    if not entry:
        raise HTTPException(404, "Entry not found or cannot be moved")
    return RedirectResponse(url=f"/novels/{entry.novel_id}#entry-{entry_id}", status_code=303)

