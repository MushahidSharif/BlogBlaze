
from pathlib import Path
from fastapi.templating import Jinja2Templates

APP_BASE_DIR = str(Path(__file__).parent.resolve())

EMAIL_TEMPLATES_DIR = APP_BASE_DIR +  "/sysdata/email_templates"

APP_NAME = "BlogBlaze"

templates = Jinja2Templates(directory="templates")
app_global_data = {"APP_NAME":APP_NAME}
templates.env.globals["APP_GLOBAL_DATA"] = app_global_data