# API Documentation for Library Management System

## 1. Introduction
This document outlines the RESTful API contract for a Library Management System, detailing the endpoints required to manage books, members, and loan operations.

## 2. Book Endpoints

### 2.1 Add a New Book
- **Endpoint**: `/api/books`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "Title": "Example Title",
    "Author": "John Doe",
    "ISBN": "9780143035653",
    "Genre": "Fiction",
    "QuantityAvailable": 5
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 201,
    "Message": "Book added successfully"
  }
  ```

### 2.2 Update a Book
- **Endpoint**: `/api/books/{bookId}`
- **Method**: `PUT`
- **Request Body**:
  ```json
  {
    "Title": "Updated Title",
    "Author": "Jane Smith",
    "ISBN": "9780143035653", // ISBN must remain the same for updates
    "Genre": "Non-Fiction",
    "QuantityAvailable": 10
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Book updated successfully"
  }
  ```

### 2.3 Remove a Book
- **Endpoint**: `/api/books/{bookId}`
- **Method**: `DELETE`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Book removed successfully"
  }
  ```

### 2.4 Get Book Details
- **Endpoint**: `/api/books/{bookId}`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": {
      "BookID": 1,
      "Title": "Example Title",
      "Author": "John Doe",
      "ISBN": "9780143035653",
      "Genre": "Fiction",
      "QuantityAvailable": 5
    }
  }
  ```

## 3. Member Endpoints

### 3.1 Register a New Member
- **Endpoint**: `/api/members`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "Name": "John Doe",
    "Address": "123 Elm St, City, State, Zip",
    "ContactNumber": "+1234567890"
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 201,
    "Message": "Member registered successfully",
    "MembershipID": 1
  }
  ```

### 3.2 Update a Member's Information
- **Endpoint**: `/api/members/{membershipId}`
- **Method**: `PUT`
- **Request Body**:
  ```json
  {
    "Name": "Updated Name",
    "Address": "456 Oak St, City, State, Zip",
    "ContactNumber": "+0987654321"
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Member updated successfully"
  }
  ```

### 3.3 Delete a Member's Account
- **Endpoint**: `/api/members/{membershipId}`
- **Method**: `DELETE`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Member account deleted successfully"
  }
  ```

### 3.4 Get Member Details
- **Endpoint**: `/api/members/{membershipId}`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": {
      "MembershipID": 1,
      "Name": "John Doe",
      "Address": "123 Elm St, City, State, Zip",
      "ContactNumber": "+1234567890"
    }
  }
  ```

## 4. Loan Endpoints

### 4.1 Issue a Book
- **Endpoint**: `/api/loans`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "BookID": 1,
    "MembershipID": 1,
    "DateBorrowed": "2023-10-01"
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Book issued successfully",
    "DueDate": "2023-10-15"
  }
  ```

### 4.2 Return a Book
- **Endpoint**: `/api/loans/{loanId}`
- **Method**: `PUT`
- **Request Body**:
  ```json
  {
    "BookID": 1,
    "MembershipID": 1,
    "DateReturned": "2023-10-14"
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Book returned successfully",
    "LateFee": 5.00 // If applicable late fee
  }
  ```

### 4.3 Renew a Loan
- **Endpoint**: `/api/loans/{loanId}`
- **Method**: `PUT`
- **Request Body**:
  ```json
  {
    "BookID": 1,
    "MembershipID": 1
  }
  ```
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Message": "Loan renewed successfully",
    "NewDueDate": "2023-10-29"
  }
  ```

### 4.4 Get Loan Details
- **Endpoint**: `/api/loans/{loanId}`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": {
      "LoanID": 1,
      "BookID": 1,
      "MembershipID": 1,
      "DateBorrowed": "2023-10-01",
      "DueDate": "2023-10-15",
      "DateReturned": null
    }
  }
  ```

## 5. Reporting Endpoints

### 5.1 Book Availability Report
- **Endpoint**: `/api/reports/availability`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": [
      {
        "BookID": 1,
        "Title": "Example Title",
        "Available": true
      },
      {
        "BookID": 2,
        "Title": "Another Example",
        "Available": false
      }
    ]
  }
  ```

### 5.2 Library Usage Report
- **Endpoint**: `/api/reports/usage`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": [
      {
        "MemberID": 1,
        "Name": "John Doe",
        "BooksBorrowedCount": 3
      },
      {
        "MemberID": 2,
        "Name": "Jane Smith",
        "BooksBorrowedCount": 5
      }
    ]
  }
  ```

### 5.3 Overdue Fines Report
- **Endpoint**: `/api/reports/overdue`
- **Method**: `GET`
- **Request Body**: None
- **Response Body**:
  ```json
  {
    "StatusCode": 200,
    "Data": [
      {
        "LoanID": 1,
        "BookID": 1,
        "MembershipID": 1,
        "DateBorrowed": "2023-10-01",
        "DueDate": "2023-10-15",
        "DateReturned": null,
        "FineAmount": 2.50
      },
      {
        "LoanID": 2,
        "BookID": 2,
        "MembershipID": 2,
        "DateBorrowed": "2023-10-05",
        "DueDate": "2023-10-19",
        "DateReturned": null,
        "FineAmount": 5.00
      }
    ]
  }
  ```