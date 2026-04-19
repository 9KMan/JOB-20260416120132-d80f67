"""Tests for the ERP system."""

import pytest
from app.models.base_models import Supplier, Material, Customer, Product


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'service' in data


class TestAuthentication:
    """Test authentication endpoints."""

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = response.get_json()
        assert 'user' in data
        assert data['user']['username'] == 'newuser'

    def test_login_success(self, client, app):
        """Test successful login."""
        # Create user first
        with app.app_context():
            from app import bcrypt
            from app.models.user import User
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='logintest', email='login@test.com', password_hash=password_hash)
            from app import db
            db.session.add(user)
            db.session.commit()

        response = client.post('/auth/login', json={
            'username': 'logintest',
            'password': 'testpass'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        assert response.status_code == 401


class TestProcurementModule:
    """Test procurement module endpoints."""

    def test_create_supplier(self, client, app):
        """Test creating a supplier."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        # Login first
        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        response = client.post('/procurement/suppliers', json={
            'code': 'SUP001',
            'name': 'Test Supplier',
            'email': 'supplier@test.com'
        })
        assert response.status_code == 201

    def test_get_suppliers(self, client, app):
        """Test getting suppliers list."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        # Create a supplier first
        client.post('/procurement/suppliers', json={
            'code': 'SUP002',
            'name': 'Another Supplier'
        })

        response = client.get('/procurement/suppliers')
        assert response.status_code == 200
        data = response.get_json()
        assert 'suppliers' in data


class TestMaterialsModule:
    """Test materials management."""

    def test_create_material(self, client, app):
        """Test creating a material."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        response = client.post('/procurement/materials', json={
            'code': 'MAT001',
            'name': 'Steel Sheet',
            'unit': 'kg',
            'unit_cost': 25.50
        })
        assert response.status_code == 201

    def test_get_materials(self, client, app):
        """Test getting materials list."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        response = client.get('/procurement/materials')
        assert response.status_code == 200
        data = response.get_json()
        assert 'materials' in data


class TestSalesModule:
    """Test sales module endpoints."""

    def test_create_customer(self, client, app):
        """Test creating a customer."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        response = client.post('/sales/customers', json={
            'code': 'CUST001',
            'name': 'Test Customer',
            'email': 'customer@test.com'
        })
        assert response.status_code == 201


class TestReportingModule:
    """Test reporting module endpoints."""

    def test_get_dashboard(self, client, app):
        """Test getting dashboard data."""
        with app.app_context():
            from app.models.user import User
            from app import bcrypt, db
            password_hash = bcrypt.generate_password_hash('testpass').decode('utf-8')
            user = User(username='test', email='test@test.com', password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

        client.post('/auth/login', json={'username': 'test', 'password': 'testpass'})

        response = client.get('/reporting/dashboard')
        assert response.status_code == 200
        data = response.get_json()
        assert 'dashboard' in data
