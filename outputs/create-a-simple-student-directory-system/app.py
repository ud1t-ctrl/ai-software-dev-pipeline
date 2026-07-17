from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
db = SQLAlchemy(app)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    enrollment_id = db.Column(db.String(20), unique=True, nullable=False)
    major = db.Column(db.String(50))
    sub_group = db.Column(db.String(50))
    email_address = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "enrollment_id": self.enrollment_id,
            "major": self.major,
            "sub_group": self.sub_group,
            "email_address": self.email_address
        }

import os
from flask import send_from_directory

# Serve the index.html file directly from the current folder
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([student.to_dict() for student in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()
    if not all(key in data for key in ["full_name", "enrollment_id", "email_address"]):
        return jsonify({"error": "Missing required fields"}), 400
    new_student = Student(**data)
    db.session.add(new_student)
    db.session.commit()
    return new_student.to_dict(), 201

@app.route('/api/students/<enrollment_id>', methods=['DELETE'])
def delete_student(enrollment_id):
    student = Student.query.filter_by(enrollment_id=enrollment_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted successfully", "enrollment_id": enrollment_id}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)