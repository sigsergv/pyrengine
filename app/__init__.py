from flask import Flask

def create_app():
    app = Flask(__name__)
    #app.config.from_object(config_class)
    app.config.from_envvar('PYRENGINE_SETTINGS')

    # Initialize Flask extensions here

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app
