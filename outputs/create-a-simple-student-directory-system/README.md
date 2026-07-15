# Create a simple Student Directory System

## Project Overview
The goal of this project is to develop a minimal, efficient student directory system using Flask as the backend and HTML/CSS/JavaScript for the frontend. The system will include a RESTful API allowing users to view, add, and delete student records, with a single-page web interface to interact with it.

### Core Features & Entities
- **Student Record**: Full Name, Enrollment ID, Major, Sub-group (e.g., Group B), and Email Address.
- **Functionality**: Users will be able to:
  - View a list of all students.
  - Add new students.
  - Delete existing students.

## Tech Stack
- Backend: Flask 2.0及以上，Flask-SQLAlchemy 2.5及以上
- Database: SQLite 3.16.2及以上
- Frontend: HTML, CSS, JavaScript (原生或JavaScript框架)

## Setup/Installation Steps

### Prerequisites
Ensure the following are installed:
- Python 3.7 +
- Flask 2.0+
- Flask-SQLAlchemy 2.5+
- SQLite

### Installation process

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/student_directory.git
   cd student_directory
   ```

2. Set up a virtual environment and run:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Initialize the database by running migrations:
   
   ```python
   flask db upgrade
   ```

4. Run the backend:

   ```bash
   python app.py
   ```

5. Start the frontend development server if needed (optional):

   ```bash
   npm install
   npm run serve  # Assuming a basic setup for frontend
   ```

## Backend API Endpoints

### Get all students:
- **URL**: `/api/students`
- **Method**: `GET`
- **Description**: Retrieves all student records.

Example response:

```json
[
    {
        "enrollment_id": "123456789",
        "email_address": "student@example.com",
        "full_name": "John Doe",
        "major": "Computer Science",
        "sub_group": "Group A"
    }
]
```

### Add a new student:
- **URL**: `/api/students`
- **Method**: `POST`
- **Description**: Creates a new student record.

Request example:

```json
{
    "enrollment_id": "123456789",
    "email_address": "student@example.com",
    "full_name": "John Doe",
    "major": "Computer Science",
    "sub_group": "Group A"
}
```

Example response (on success):

```json
{
    "enrollment_id": "123456789",
    "email_address": "student@example.com",
    "full_name": "John Doe",
    "major": "Computer Science",
    "sub_group": "Group A"
}
```

Example response (on failure):

```json
{
    "error": "Missing required fields"  # or "Duplicate enrollment ID or email address"
}
```

### Delete a student:
- **URL**: `/api/students/{enrollment_id}`
- **Method**: `DELETE`
- **Description**: Deletes an existing student record by its enrollment_id.

Example response (on success):

```json
{
    "message": "Student deleted successfully"
}
```

Example response (on failure):

```json
{
    "error": "Student not found"
}
```

## Frontend Development

The frontend uses vanilla JavaScript for interaction with the backend API. Ensure:

- The `index.html` file is properly set up to include necessary scripts and styles.
- Event listeners are added to handle form submissions and display responses from the backend.

For development, use:
    
```bash
npm run serve  # This command starts a local server, typically at http://localhost:PORT
```

## Testing

Unit tests for the backend can be found in `test.py`. Run using:

```bash
pytest test.py
```

Test cases cover retrieving students, adding a new student with normal and abnormal situations, and deleting a student.

### Mismatches Between Backend and Frontend
1. **Role-Based Authorization**: Currently missing from both frontend and backend.
2. **Placeholder Text in Modal Fields**: Placeholder text has been added to the HTML forms for clarity.
3. **Error Handling During API Requests**: Basic error handling using `try-except` blocks in JavaScript.

These issues are noted in the review comments within the respective files, where potential fixes need to be implemented.

## Known Issues

- **Role-Based Authorization**: The current implementation lacks role checks on frontend and backend for deleting students.
- **Placeholder Text**: Missing placeholder text in modal forms for user clarity.
- **Error Handling During API Requests**: Basic error handling using JavaScript might be insufficient. More robust error management should be considered based on application requirements.

## How to Contribute

Feel free to submit pull requests or open issues if you find any bugs or have suggestions for improvements.

---

This document serves as a comprehensive guide to building the Student Directory system, including setup instructions, API documentation, and frontend interaction.