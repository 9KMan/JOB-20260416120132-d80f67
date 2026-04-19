"""Test configuration and fixtures."""

import pytest
from app import create_app, db
from app.models.user import User
from app import bcrypt


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def auth_headers(app, client):
    """Create authenticated user and return headers."""
    with app.app_context():
        password_hash = bcrypt.generate_password_hash('testpass123').decode('utf-8')
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=password_hash
        )
        db.session.add(user)
        db.session.commit()

        response = client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })

        data = response.get_json()
        token = data.get('user', {}).get('id', '')

        return {'Authorization': f'Bearer {token}'}
