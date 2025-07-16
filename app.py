from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///golive.db')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Add user_loader for Flask-Login
from app.models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

try:
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    print('auth blueprint registered', flush=True)
except Exception as e:
    print(f'Error registering auth blueprint: {e}', flush=True)

try:
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    print('main blueprint registered', flush=True)
except Exception as e:
    print(f'Error registering main blueprint: {e}', flush=True)

try:
    from app import models
    print('models imported', flush=True)
except Exception as e:
    print(f'Error importing models: {e}', flush=True)

@app.route("/")
def hello():
    return "Hello from full Flask!"

if __name__ == '__main__':
    app.run()