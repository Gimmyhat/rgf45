# __init__.py
from flask import Flask
from app.config.default import DefaultConfig


def create_app():
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)

    # Регистрация главного блюпринта
    from app.main.views import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix=app.config['APPLICATION_ROOT'])

    return app
