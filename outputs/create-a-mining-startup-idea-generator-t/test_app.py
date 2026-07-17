import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

db = SQLAlchemy(app)

class User(db.Model):
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class MiningSite(db.Model):
    SiteId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Location = db.Column(db.String(255), nullable=False)
    MineralType = db.Column(db.String(100))
    DepositSize = db.Column(db.DECIMAL(18, 2))
    EstimatedProductionCapacity = db.Column(db.DECIMAL(18, 2))
    ExplorationStatus = db.Column(db.Enum('Exploring', 'Discovered', 'Developed'), default='Exploring')
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class StartupIdea(db.Model):
    IdeaId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(255), nullable=False)
    Description = db.Column(db.Text, nullable=False)
    RelatedMineralType = db.Column(db.String(100))
    FeasibilityScore = db.Column(db.Integer, check_constraint='FeasibilityScore BETWEEN 0 AND 100')
    EstimatedCost = db.Column(db.DECIMAL(18, 2))
    LinkedMiningSiteId = db.Column(db.Integer, db.ForeignKey('miningsites.SiteId'), nullable=True)
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    UpdatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class UserFavorite(db.Model):
    FavoriteId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('users.UserId'), nullable=False)
    IdeaId = db.Column(db.Integer, unique=True, nullable=False)
    CreatedAt = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

def test_register_normal_case():
    payload = {'name': 'Test User', 'email': 'test@example.com'}
    response = app.test_client().post('/register', json=payload)
    assert response.status_code == 200
    data = response.json
    assert 'userId' in data
    assert 'token' in data

def test_register_edge_case():
    payload = {'name': '', 'email': ''}
    response = app.test_client().post('/register', json=payload)
    assert response.status_code == 400

def test_register_error_case():
    db.session.add(User(Email='test@example.com'))
    db.session.commit()
    payload = {'name': 'Test User', 'email': 'test@example.com'}
    response = app.test_client().post('/register', json=payload)
    assert response.status_code == 400

def test_login_normal_case():
    payload = {'email': 'test@example.com', 'password': 'testpass'}
    user = User.query.filter_by(Email='test@example.com').first()
    if not user:
        app.test_client().post('/register', json={'name': 'Test User', 'email': 'test@example.com'})
    response = app.test_client().post('/login', json=payload)
    assert response.status_code == 200
    data = response.json
    assert 'userId' in data
    assert 'token' in data

def test_login_edge_case():
    payload = {'email': '', 'password': ''}
    response = app.test_client().post('/login', json=payload)
    assert response.status_code == 400

def test_create_mining_site_normal_case():
    payload = {
        'location': 'Test Location',
        'mineralType': 'Gold',
        'depositSize': 123.45,
        'estimatedProductionCapacity': 987.65
    }
    response = app.test_client().post('/miningsites', json=payload)
    assert response.status_code == 201
    data = response.json
    assert 'siteId' in data

def test_create_mining_site_edge_case():
    payload = {
        'location': '',
        'mineralType': '',
        'depositSize': None,
        'estimatedProductionCapacity': None
    }
    response = app.test_client().post('/miningsites', json=payload)
    assert response.status_code == 400

def test_create_mining_site_error_case():
    payload = {
        'location': 'Test Location',
        'mineralType': 'Gold',
        'depositSize': -1,
        'estimatedProductionCapacity': -1
    }
    response = app.test_client().post('/miningsites', json=payload)
    assert response.status_code == 400

def test_update_mining_site_normal_case():
    payload = {
        'location': 'Updated Location',
        'exploorationStatus': 'Discovered'
    }
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = 1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().put(f'/miningsites/{user_id}', json=payload)
        assert response.status_code == 200

def test_update_mining_site_edge_case():
    payload = {
        'location': '',
        'exploorationStatus': ''
    }
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = 1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().put(f'/miningsites/{user_id}', json=payload)
        assert response.status_code == 400

def test_update_mining_site_error_case():
    payload = {
        'location': 'Updated Location',
        'exploorationStatus': 'Discovered'
    }
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = -1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().put(f'/miningsites/{user_id}', json=payload)
        assert response.status_code == 404

def test_delete_mining_site_normal_case():
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = 1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().delete(f'/miningsites/{user_id}')
        assert response.status_code == 204

def test_delete_mining_site_edge_case():
    user_id = 1
    response = app.test_client().delete(f'/miningsites/{user_id}')
    assert response.status_code == 404

def test_generate_startup_idea_normal_case():
    with patch.object(db, 'session') as mock_session:
        mining_site_payload = {
            'location': "Test Location",
            'mineralType': 'Gold',
        }
        app.test_client().post('/miningsites', json=mining_site_payload)
        user_id = 1
        response = app.test_client().get(f'/miningsites/{user_id}/startup')
        assert response.status_code == 200

def test_generate_startup_idea_edge_case():
    with patch.object(db, 'session') as mock_session:
        mining_site_payload = {
            'location': None,
            'mineralType': '',
        }
        app.test_client().post('/miningsites', json=mining_site_payload)
        user_id = 1
        response = app.test_client().get(f'/miningsites/{user_id}/startup')
        assert response.status_code == 400

def test_generate_startup_idea_error_case():
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = -1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().get(f'/miningsites/{user_id}/startup')
        assert response.status_code == 404

def test_add_user_favorite_normal_case():
    with patch.object(db, 'session') as mock_session:
        mining_site_payload = {
            'location': "Test Location",
            'mineralType': 'Gold',
        }
        app.test_client().post('/miningsites', json=mining_site_payload)
        user_id = 1
        response = app.test_client().post(f'/miningsites/{user_id}/favorites')
        assert response.status_code == 201

def test_add_user_favorite_edge_case():
    with patch.object(db, 'session') as mock_session:
        mining_site_payload = {
            'location': None,
            'mineralType': '',
        }
        app.test_client().post('/miningsites', json=mining_site_payload)
        user_id = 1
        response = app.test_client().post(f'/miningsites/{user_id}/favorites')
        assert response.status_code == 400

def test_add_user_favorite_error_case():
    with patch.object(db, 'session') as mock_session:
        mock_user = User.query.filter_by(UserId=1).first()
        user_id = -1
        app.test_client().post('/miningsites', json={"location": "Test Location", 'mineralType': 'Gold'})
        response = app.test_client().post(f'/miningsites/{user_id}/favorites')
        assert response.status_code == 404