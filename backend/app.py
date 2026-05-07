import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

IS_PROD        = os.getenv('FLASK_ENV') == 'production'
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')]

LOG_LEVEL = logging.INFO if IS_PROD else logging.DEBUG
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('app')

if IS_PROD:
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

app = Flask(__name__)
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY', 'dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv('DATABASE_URL', 'sqlite:///worker_hours.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE']        = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY']        = True
app.config['SESSION_COOKIE_SECURE']          = IS_PROD

CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

from extensions import db, migrate, limiter
db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)

from routes.auth     import bp as auth_bp
from routes.users    import bp as users_bp
from routes.projects import bp as projects_bp
from routes.invites  import bp as invites_bp
from routes.hours    import bp as hours_bp
from routes.leave    import bp as leave_bp

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(invites_bp)
app.register_blueprint(hours_bp)
app.register_blueprint(leave_bp)


@app.errorhandler(404)
def not_found(_e):
    return jsonify({'error': 'Resurso nerasta'}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({'error': 'Metodas neleidžiamas'}), 405


@app.errorhandler(429)
def rate_limited(_e):
    return jsonify({'error': 'Per daug užklausų. Bandykite vėliau.'}), 429


@app.errorhandler(500)
def server_error(_e):
    logger.error('Unhandled exception', exc_info=True)
    return jsonify({'error': 'Vidinė serverio klaida. Bandykite vėliau.'}), 500


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=not IS_PROD)
