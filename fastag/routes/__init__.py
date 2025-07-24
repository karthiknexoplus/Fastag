from .bank_api import bank_api
from .bank_callbacks import bank_callbacks
from .tariff import tariff_bp

def register_blueprints(app):
    app.register_blueprint(bank_api)
    app.register_blueprint(bank_callbacks)
    app.register_blueprint(tariff_bp) 