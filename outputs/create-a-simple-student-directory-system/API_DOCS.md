## RESTful API Contract for Student Directory System

### 1. View All Student Records
- **Description**: Retrieves a list of all student records.
  
#### - **Method**: `GET`
#### - **Path**: `/api/students`
#### - **Request Body**: None
#### - **Response Body**:
```json
[
    {
        "id": 1,
        "full_name": "John Doe",
        "enrollment_id": "S000001",
        "major": "Computer Science",
        "sub_group": "Backend Development",
        "email_address": "john.doe@example.com"
    },
    {
        "id": 2,
        "full_name": "Jane Smith",
        "enrollment_id": "S000002",
        "major": "Computer Science",
        "sub_group": "Frontend Development",
        "email_address": "jane.smith@example.com"
    }
]
```

### 2. Add a New Student
- **Description**: Adds a new student record.

#### - **Method**: `POST`
#### - **Path**: `/api/students`
#### - **Request Body**:
```json
{
    "full_name": "Alice Johnson",
    "enrollment_id": "S000003",
    "major": "Business Administration",
    "sub_group": "Marketing Strategy",
    "email_address": "alice.johnson@example.com"
}
```
#### - **Response Body**:
```json
{
    "id": 3,
    "full_name": "Alice Johnson",
    "enrollment_id": "S000003",
    "major": "Business Administration",
    "sub_group": "Marketing Strategy",
    "email_address": "alice.johnson@example.com"
}
```

### 3. Delete an Existing Student
- **Description**: Deletes a student record by enrollment ID.

#### - **Method**: `DELETE`
#### - **Path**: `/api/students/{enrollment_id}`
#### - **Response Body**:
```json
{
    "message": "Student deleted successfully",
    "enrollment_id": "S000003"
}
```

---

### Additional Notes

- All API requests must be made over HTTPS.
- The response time for each endpoint should not exceed 200ms.
- Ensure that all operations are authorized based on user roles (e.g., only admins can perform delete operations).
- Basic unit tests and integration tests mentioned in the Non-Functional Requirements section are essential to maintain system reliability.