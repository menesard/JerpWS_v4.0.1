from app import create_app, db
from app.models.database import User
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    # Create a new admin user
    new_admin = User(
        username='admin',
        password_hash=generate_password_hash('admin'),
        is_admin=True,
        role='admin'
    )
    db.session.add(new_admin)
    db.session.commit()
    print("New admin created with username 'admin' and password 'admin'")