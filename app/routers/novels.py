from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import quote
import re
from .. import crud, schemas, auth, models
from ..database import get_db
from ..templating import templates

router = APIRouter(
    prefix="/novels",
    tags=["novels"]
)

@router.get("/new", response_class=HTMLResponse)
async def show_create_novel_form(request: Request, current_user: models.User = Depends(auth.get_current_user_from_cookie)):
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
            "db": db
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

@router.get("/{novel_id}/export", response_class=Response)
async def handle_export_novel(
        novel_id: int,
        type_ids: Optional[List[int]] = Query(None),
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")

    if not type_ids:
        setting_types = crud.get_setting_types_by_novel(db, novel_id=novel.id)
    else:
        setting_types = [crud.get_setting_type(db, tid) for tid in type_ids if crud.get_setting_type(db, tid)]
        setting_types = [st for st in setting_types if st and st.novel_id == novel.id]

    md_content = f"# {novel.title}\n\n"
    if novel.author:
        md_content += f"**作者**: {novel.author}\n\n"
    if novel.description:
        md_content += f"## 小说简介\n\n{novel.description}\n\n"

    md_content += "---\n\n"

    for s_type in setting_types:
        md_content += f"## {s_type.name}\n\n"
        if not s_type.entries:
            md_content += "*此分类下暂无条目。*\n\n"
        for entry in s_type.entries:
            md_content += f"### {entry.name}\n\n"
            if not entry.fields:
                md_content += "*此条目下暂无字段。*\n\n"
            for field in entry.fields:
                md_content += f"**{field.key}**: {field.value or ''}\n\n"
            md_content += "\n"
        md_content += "---\n\n"

    file_name = f"{novel.title}_设定集.md".replace(" ", "_")

    encoded_file_name = quote(file_name)

    headers = {
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_file_name}'
    }
    return Response(content=md_content.encode('utf-8'), media_type="text/markdown", headers=headers)

@router.post("/{novel_id}/import", response_class=RedirectResponse)
async def handle_import_novel(
        novel_id: int,
        file: UploadFile = File(...),
        current_user: models.User = Depends(auth.get_current_user_from_cookie),
        db: Session = Depends(get_db)
):
    novel = crud.get_novel(db, novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(404, "Novel not found")

    content = await file.read()
    content_str = content.decode('utf-8')
    lines = content_str.split('\n')

    current_type_obj = None
    current_entry_obj = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('## '):
            type_name = line[3:].strip()
            if type_name == "小说简介": continue

            current_type_obj = crud.get_setting_type_by_name(db, novel_id=novel.id, name=type_name)
            if not current_type_obj:
                type_schema = schemas.SettingTypeCreate(name=type_name)
                current_type_obj = crud.create_setting_type(db, setting_type=type_schema, novel_id=novel.id)
            current_entry_obj = None

        elif line.startswith('### '):
            if not current_type_obj: continue
            entry_name = line[4:].strip()
            current_entry_obj = crud.get_setting_entry_by_name_and_type(db, type_id=current_type_obj.id, name=entry_name)
            if not current_entry_obj:
                entry_schema = schemas.SettingEntryCreate(name=entry_name)
                current_entry_obj = crud.create_setting_entry(db, entry=entry_schema, novel_id=novel.id, type_id=current_type_obj.id)
            else:
                # Clear existing fields for overwrite
                for field in current_entry_obj.fields:
                    db.delete(field)
                db.commit()

        elif line.startswith('**'):
            if not current_entry_obj: continue
            match = re.match(r'\*\*(.+?)\*\*:\s*(.*)', line)
            if match:
                key, value = match.groups()
                crud.create_setting_field(db, key=key.strip(), value=value.strip(), entry_id=current_entry_obj.id)

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

    type_ids_str = await request.json()
    type_ids = [int(id_str) for id_str in type_ids_str]
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

    novel = crud.get_novel(db, setting_type.novel_id, owner_id=current_user.id)
    if not novel:
        raise HTTPException(403, "Not authorized")

    entry_ids_str = await request.json()
    entry_ids = [int(id_str) for id_str in entry_ids_str]
    crud.reorder_setting_entries(db, type_id=type_id, entry_ids=entry_ids)
    return Response(status_code=200)

