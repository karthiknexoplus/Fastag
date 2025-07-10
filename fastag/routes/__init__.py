from .bank_api import bank_api
from .bank_callbacks import bank_callbacks

def register_blueprints(app):
    app.register_blueprint(bank_api)
    app.register_blueprint(bank_callbacks) 