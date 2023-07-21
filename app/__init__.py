from flask import Flask

def create_app():
    app = Flask(__name__)
    #app.config.from_object(config_class)
    app.config.from_envvar('PYRENGINE_SETTINGS')

    # Initialize Flask extensions here

    # Register blueprints here

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app
