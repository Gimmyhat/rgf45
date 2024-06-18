# __init__.py
from flask import Flask
from app.config.default import DefaultConfig


def create_app():
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)

    @app.template_filter('no_leading_slash')
    def no_leading_slash(url):
        return url.lstrip('/')

    # Регистрация главного блюпринта
    from app.main.views import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
