"""
Shared Flask extensions — imported by app.py, models, and routes.
Keeping them here breaks the circular import between app.py ↔ models ↔ routes.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=['1000 per day', '100 per hour'])
