```markdown
# Review Report

## Backend Issues

### 1. Bug: Missing Error Handling in Delete Operation
**Issue:** The `/api/students/{enrollment_id}` endpoint does not handle database errors when deleting a student.

**Current Code:**
```python
@app.route('/api/students/<enrollment_id>', methods=['DELETE'])
def delete_student(enrollment_id):
    student = Student.query.filter_by(enrollment_id=enrollment_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted successfully", "enrollment_id": enrollment_id}), 200
```

**Fix:**
Add a try-except block to catch and handle potential database errors.
```python
@app.route('/api/students/<enrollment_id>', methods=['DELETE'])
def delete_student(enrollment_id):
    try:
        student = Student.query.filter_by(enrollment_id=enrollment_id).first()
        if not student:
            return jsonify({"error": "Student not found"}), 404
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted successfully", "enrollment_id": enrollment_id}), 200
    except Exception as e:
        return jsonify({"error": "Database error"}), 500
```

### 2. Potential SQL Injection Risk in Student Model
**Issue:** The `full_name` and `email_address` fields are not validated, which could lead to SQL injection if input is not properly sanitized.

**Current Code:**
```python
class Student(db.Model):
    # Column definitions...
```

**Fix:**
Ensure that all user inputs are properly validated and sanitized before being passed to the database.
```python
from sqlalchemy.exc import IntegrityError

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()
    if not all(key in data for key in ["full_name", "enrollment_id", "email_address"]):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        new_student = Student(**data)
        db.session.add(new_student)
        db.session.commit()
        return new_student.to_dict(), 201
    except IntegrityError:
        return jsonify({"error": "Duplicate enrollment ID or email address"}), 409
```

## Frontend Issues

### 1. Missing Placeholder in Modal Fields
**Issue:** The modal fields are missing placeholders, making it unclear what input is expected.

**Current Code:**
```html
<form onsubmit="event.preventDefault(); saveStudent()">
    Full Name: <input type="text" id="full-name"><br><br>
    Enrollment ID: <input type="text" id="enrollment-id"><br><br>
    Major: <input type="text" id="major"><br><br>
    Sub-Group: <input type="text" id="sub-group"><br><br>
    Email Address: <input type="email" id="email-address"><br><br>
    <button type="submit">Save</button> | <button onclick="closeModal()">Cancel</button>
</form>
```

**Fix:**
Add placeholder text in each input field.
```html
<form onsubmit="event.preventDefault(); saveStudent()">
    Full Name: <input type="text" id="full-name" placeholder="Enter full name"><br><br>
    Enrollment ID: <input type="text" id="enrollment-id" placeholder="Enter enrollment ID"><br><br>
    Major: <input type="text" id="major" placeholder="Enter major"><br><br>
    Sub-Group: <input type="text" id="sub-group" placeholder="Enter sub-group"><br><br>
    Email Address: <input type="email" id="email-address" placeholder="Enter email address"><br><br>
    <button type="submit">Save</button> | <button onclick="closeModal()">Cancel</button>
</form>
```

### 2. Error Handling in Modal Form
**Issue:** The modal form does not handle errors, such as missing required fields or failed database operations.

**Current Code:**
```html
<script>
    // saveStudent function...
</script>
```

**Fix:**
Add error handling to the `saveStudent` function.
```html
<script>
async function saveStudent() {
    const fullName = document.getElementById('full-name').value;
    const enrollmentId = document.getElementById('enrollment-id').value;
    const major = document.getElementById('major').value;
    const subGroup = document.getElementById('sub-group').value;
    const emailAddress = document.getElementById('email-address').value;

    try {
        await fetchData('/api/students', 'POST', { full_name: fullName, enrollment_id: enrollmentId, major, sub_group: subGroup, email_address: emailAddress });
        closeModal();
        fetchStudents();
        alert("Student added successfully!");
    } catch (error) {
        console.error('Error adding student:', error);
        alert("An error occurred while adding the student.");
    }
}
</script>
```

## Mismatches Between Backend and Frontend

### 1. No Role-Based Authorization
**Issue:** The frontend does not check if the user has the necessary role (e.g., admin) to perform delete operations.

**Current Code:**
```javascript
// Delete student function...
```

**Fix:**
Add role-based authorization in both the frontend and backend.
```javascript
async function deleteStudent(enrollmentId) {
    fetch('/api/check-permission', {
        method: 'GET',
        headers: {
            'Authorization': localStorage.getItem('token')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.isAuthorized) {
            try {
                await fetchData(`/api/students/${enrollmentId}`, 'DELETE');
                fetchStudents();
            } catch (error) {
                console.error('Error deleting student:', error);
            }
        } else {
            alert("You are not authorized to delete students.");
        }
    });
}
```

```python
@app.route('/api/check-permission', methods=['GET'])
def check_permission():
    token = request.headers.get('Authorization')
    if validate_token(token) and has_role('admin'):
        return jsonify({'isAuthorized': True}), 200
    return jsonify({'isAuthorized': False}), 403

def validate_token(token):
    # Validate the token (e.g., JWT)
    pass

def has_role(role):
    # Check user's role
    pass
```

By addressing these issues, the backend and frontend will be more robust and secure.