import os
import sys

# Allow `gunicorn wsgi:app` when cwd is backend/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.app import create_app

app = create_app()
