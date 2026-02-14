
from pathlib import Path
from fastapi.templating import Jinja2Templates

APP_BASE_DIR = str(Path(__file__).parent.resolve())

EMAIL_TEMPLATES_DIR = APP_BASE_DIR +  "/sysdata/email_templates"


templates = Jinja2Templates(directory="templates")