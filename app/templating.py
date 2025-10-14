import markdown2
import re
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session
from . import crud

# --- Jinja2Templates Instance Setup ---
# Use Starlette's Jinja2Templates which provides the .TemplateResponse method
templates = Jinja2Templates(directory="app/templates")

# --- Custom Filters ---
def nl2br(value):
    """Converts newlines in a string to HTML <br> tags."""
    if not value:
        return ""
    return value.replace('\n', '<br>\n')

def _create_internal_links(text: str, db: Session, novel_id: int) -> str:
    """
    Parses text for [[Entry Name]] syntax and replaces it with internal links.
    """
    if not text:
        return ""

    def replacer(match):
        entry_name = match.group(1).strip()
        # Use a case-insensitive search for better usability
        entry = crud.get_setting_entry_by_name_and_novel(db, novel_id=novel_id, entry_name=entry_name)

        if entry:
            # Found a matching entry, create a valid link
            return f'<a href="#entry-{entry.id}" class="internal-link">{entry_name}</a>'
        else:
            # No matching entry found, create a "broken link"
            return f'<span class="broken-link" title="未找到名为「{entry_name}」的设定">{entry_name}</span>'

    # Regex to find all occurrences of [[...]]
    pattern = re.compile(r"\[\[(.*?)\]\]")

    return pattern.sub(replacer, text)

def markdown_to_html(value, db: Session = None, novel_id: int = None):
    """
    Converts Markdown text to HTML, processing internal links if db and novel_id are provided.
    """
    if not value:
        return ""

    processed_text = value
    if db and novel_id is not None:
        processed_text = _create_internal_links(value, db=db, novel_id=novel_id)

    return markdown2.markdown(processed_text, extras=["fenced-code-blocks", "tables", "spoiler", "break-on-newline"])

# --- Register Filters on the underlying Jinja2 environment ---
templates.env.filters['nl2br'] = nl2br
templates.env.filters['markdown_to_html'] = markdown_to_html

