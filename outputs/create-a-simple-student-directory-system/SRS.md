# Software Requirements Specification (SRS)

## 1. Purpose
This document specifies the requirements for developing and deploying a Student Directory System, which includes a RESTful API and a single-page web interface to manage a list of students.

## 2. Scope

### 2.1 In-Scope Functionality
- A student record database table.
- User interaction for viewing, adding, and deleting student records.
- A RESTful API providing CRUD operations on student records.
- A simple user interface for interacting with the system.

### 2.2 Out-of-Scope Functionality
- Advanced filtering or sorting capabilities beyond basic list views.
- Authentication and authorization for user management unless explicitly required.
- Complex reporting features.

## 3. Functional Requirements

### 3.1 User Roles
- **Admin**: Can perform all CRUD operations on student records.
  
### 3.2 Core Entities
- **Student Record**:
  - Fields: Full Name, Enrollment ID, Major, Sub-group, Email Address.

### 3.3 Actions
1. **View Student Records**
   - Description: The system shall display a list of all students using the provided API and web interface.
   - Precondition: None
   - Postcondition: A table displaying student records is presented to the user.

2. **Add a New Student**
   - Description: Allows adding a new student record via both the front-end form and REST API POST endpoint.
   - Precondition: The application must have an active student record database.
   - Postcondition: A new student record is added to the database, reflecting in both the web interface and API GET response.

3. **Delete an Existing Student**
   - Description: Allows removing a student record from the system via both front-end button click events and REST API DELETE endpoint.
   - Precondition: There must be at least one student records in the system.
   - Postcondition: The student record is removed, updating the list on web interface and API GET response.

4. **Data Persistence**
   - Description: Ensure that all CRUD operations are persisted in the SQLite database for future reference and integrity.
   - Precondition: User is authorized to perform an operation (e.g., admin role).
   - Postcondition: Changes to student records are committed and preserved within the database.

## 4. Non-Functional Requirements

### 4.1 Performance
- System should respond under reasonable load with minimal delay.
- Maximum response time for API endpoints should not exceed 200ms.

### 4.2 Usability
- The web interface should be simple, intuitive, and accessible using HTML/CSS/JavaScript.
- All operations (including CRUD) must lead to a seamless user experience.

### 4.3 Usability - User Interface (UI)
- Front-end development language: HTML, CSS, JavaScript.
- Should adhere to basic accessibility standards.
  
### 4.4 Security
   - The system should implement encryption for data transmitted between client and server using HTTPS.
 
### 4.5 Testing
    - Basic unit tests should be created using pytest or similar unittest framework following simple assertions.
- Integration test to check if the backend server starts successfully.
- GET endpoint returns a 200 status code.

### 4.6 Reliability
- The system shall reliably provide services round-the-clock and maintain at least 95% uptime without downtime.
  

## 5. References
None.

This SRS document provides comprehensive guidance on the development of the Student Directory System, focusing on both functional and non-functional requirements to ensure a simple yet efficient management solution for student records.