import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_talisman import Talisman
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db, migrate, limiter


def create_app():
    app = Flask(__name__)

    # Load config
    from config import Config
    app.config.from_object(Config)
    Config.validate()

    # Initialize extensions
    db.init_app(app)
    # Point Flask-Migrate explicitly to backend/migrations folder
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migrate.init_app(app, db, directory=migrations_dir)
    limiter.init_app(app)

    # Security and proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    Talisman(app, force_https=app.config['FLASK_ENV'] == 'production', content_security_policy=None)

    # Configure CORS
    cors_origins = app.config.get('CORS_ORIGINS') or ['*']
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Health check routes
    @app.route('/', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'service': 'EthioShop API',
            'version': '1.0.0'
        }), 200

    @app.route('/health', methods=['GET'])
    def health():
        try:
            with db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'

        return jsonify({
            'status': 'ok',
            'database': db_status
        }), 200

    # Register blueprints
    from routes import products, orders, users, admin, upload, requests, refunds, settings, bot_api

    app.register_blueprint(products.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(bot_api.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(requests.bp)
    app.register_blueprint(refunds.bp)
    app.register_blueprint(settings.bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config['DEBUG']
    )
