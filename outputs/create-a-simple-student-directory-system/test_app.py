import pytest
from flask import Flask
from models import db, Student  # Assuming the student model is saved in models.py

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_students.db'
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_get_students(client):
    # Normal Case
    response = client.get('/api/students')
    assert response.status_code == 200
    assert isinstance(response.json, list)

    # Adding a student to set up for further tests
    new_student_data = {
        "full_name": "Test Student",
        "enrollment_id": "1234567890",
        "email_address": "test.student@example.com"
    }
    client.post('/api/students', json=new_student_data)
    
    # Normal Case with database
    response = client.get('/api/students')
    assert response.status_code == 200
    assert 'Test Student' in response.json[0]['full_name']

def test_post_student(client):
    # Normal Case
    student_data = {
        "full_name": "New Student",
        "enrollment_id": "9876543210",
        "email_address": "new.student@example.com"
    }
    response = client.post('/api/students', json=student_data)
    assert response.status_code == 201
    assert response.json['full_name'] == 'New Student'

    # Edge Case: Missing required fields
    student_data_missing_field = {
        "enrollment_id": "1111111111"
    }
    response = client.post('/api/students', json=student_data_missing_field)
    assert response.status_code == 400

def test_delete_student(client):
    # Normal Case
    student_data = {
        "full_name": "Student to Delete",
        "enrollment_id": "12345678910",
        "email_address": "student.to.delete@example.com"
    }
    client.post('/api/students', json=student_data)

    response = client.delete('/api/students/12345678910')
    assert response.status_code == 200
    assert response.json['message'] == 'Student deleted successfully'

    # Error Case: Student not found
    response = client.delete('/api/students/0')
    assert response.status_code == 404

# Edge Cases and Error Cases are already covered by normal cases due to the try-except block in the delete route.