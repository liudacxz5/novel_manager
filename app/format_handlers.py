from . import models, schemas, crud
from sqlalchemy.orm import Session
import re

class BaseFormatHandler:
    """处理导入导出的格式处理器基类"""
    def export_content(self, novel: models.Novel, setting_types: list) -> str:
        raise NotImplementedError

    def import_content(self, novel_id: int, content_str: str, db: Session):
        raise NotImplementedError

class MarkdownFormatHandler(BaseFormatHandler):
    """处理 Markdown 格式的导入导出"""

    def export_content(self, novel: models.Novel, setting_types: list) -> str:
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
                continue # Add continue to avoid extra newlines
            for entry in s_type.entries:
                md_content += f"### {entry.name}\n\n"
                if not entry.fields:
                    md_content += "*此条目下暂无字段。*\n\n"
                for field in entry.fields:
                    md_content += f"**{field.key}**: {field.value or ''}\n\n"
                # md_content += "\n" # Removed extra newline for cleaner output
            md_content += "---\n\n" # Separator after each type
        return md_content

    def import_content(self, novel_id: int, content_str: str, db: Session):
        lines = content_str.split('\n')

        current_type_obj = None
        current_entry_obj = None
        current_field_key = None
        current_field_value_lines = []

        def save_current_field():
            if current_entry_obj and current_field_key:
                full_value = "\n".join(current_field_value_lines).strip()
                crud.create_setting_field(db, key=current_field_key, value=full_value, entry_id=current_entry_obj.id)
                current_field_value_lines.clear()

        for line in lines:
            stripped_line = line.strip()

            is_new_type = stripped_line.startswith('## ')
            is_new_entry = stripped_line.startswith('### ')
            is_new_field = bool(re.match(r'\*\*(.+?)\*\*:\s*(.*)', stripped_line))

            if is_new_type:
                save_current_field()
                current_field_key = None
                current_entry_obj = None

                type_name = stripped_line[3:].strip()
                if type_name in ["小说简介", "作者"]: continue

                current_type_obj = crud.get_setting_type_by_name(db, novel_id=novel_id, name=type_name)
                if not current_type_obj:
                    type_schema = schemas.SettingTypeCreate(name=type_name)
                    current_type_obj = crud.create_setting_type(db, setting_type=type_schema, novel_id=novel_id)

            elif is_new_entry:
                save_current_field()
                current_field_key = None
                if not current_type_obj: continue

                entry_name = stripped_line[4:].strip()
                current_entry_obj = crud.get_setting_entry_by_name_and_type(db, type_id=current_type_obj.id, name=entry_name)
                if not current_entry_obj:
                    entry_schema = schemas.SettingEntryCreate(name=entry_name)
                    current_entry_obj = crud.create_setting_entry(db, entry=entry_schema, novel_id=novel_id, type_id=current_type_obj.id)
                else: # Overwrite: clear existing fields
                    for field in current_entry_obj.fields: db.delete(field)
                    db.commit()

            elif is_new_field:
                save_current_field()
                match = re.match(r'\*\*(.+?)\*\*:\s*(.*)', line)
                key, first_line_value = match.groups()
                current_field_key = key.strip()
                current_field_value_lines = [first_line_value.strip()] if first_line_value.strip() else []

            elif current_field_key and current_entry_obj:
                current_field_value_lines.append(line)

        save_current_field() # Save the very last field

# 实例化处理器，未来可以在这里添加更多格式
format_handlers = {
    "markdown": MarkdownFormatHandler()
}
