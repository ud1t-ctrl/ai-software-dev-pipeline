# API Documentation

## 1. User Authentication and Authorization

### 1.1 Register (`POST /register`)
- **Request Body:**
    ```json
    {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    ```
- **Response Body on Success (200 OK):**
    ```json
    {
        "userId": 1,
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    }
    ```

### 1.2 Login (`POST /login`)
- **Request Body:**
    ```json
    {
        "email": "john.doe@example.com",
        "password": "securepassword"
    }
    ```
- **Response Body on Success (200 OK):**
    ```json
    {
        "userId": 1,
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    }
    ```

## 2. Mining Sites

### 2.1 Create Mining Site (`POST /miningsites`)
- **Request Body:**
    ```json
    {
        "location": "North Pole",
        "mineralType": "Gold",
        "depositSize": 1000000,
        "estimatedProductionCapacity": 50000,
        "explorationStatus": "Discovered"
    }
    ```
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (201 Created):**
    ```json
    {
        "siteId": 1,
        "location": "North Pole",
        "mineralType": "Gold",
        "depositSize": 1000000,
        "estimatedProductionCapacity": 50000,
        "explorationStatus": "Discovered"
    }
    ```

### 2.2 Update Mining Site (`PUT /miningsites/{siteId}`)
- **Request Body:**
    ```json
    {
        "location": "New Location",
        "mineralType": "Silver",
        "depositSize": 500000,
        "estimatedProductionCapacity": 60000,
        "explorationStatus": "Developed"
    }
    ```
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    {
        "siteId": 1,
        "location": "New Location",
        "mineralType": "Silver",
        "depositSize": 500000,
        "estimatedProductionCapacity": 60000,
        "explorationStatus": "Developed"
    }
    ```

### 2.3 Delete Mining Site (`DELETE /miningsites/{siteId}`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (204 No Content):**

## 3. Startup Ideas

### 3.1 Generate Startup Idea from Mining Site (`GET /startupideas/miningsite/{miningSiteId}`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    {
        "ideaId": 1,
        "title": "Mining Gold Exploration Project",
        "description": "Extensive mining for gold in northern locations with high feasibility.",
        "relatedMineralType": "Gold",
        "feasibilityScore": 90,
        "estimatedCost": 50000
    }
    ```

### 3.2 Save Startup Idea as Favorite (`POST /favorites`)
- **Request Body:**
    ```json
    {
        "ideaId": 1
    }
    ```
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (201 Created):**

### 3.3 Remove Startup Idea from Favorites (`DELETE /favorites/{favorId}`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (204 No Content):**

## 4. Filtering and Sorting Ideas

### 4.1 Filter Startup Ideas (`GET /startupideas?mineralType=Gold&region=Northern`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    [
        {
            "ideaId": 1,
            "title": "Mining Gold Exploration Project",
            "description": "Extensive mining for gold in northern locations with high feasibility.",
            "relatedMineralType": "Gold",
            "feasibilityScore": 90,
            "estimatedCost": 50000
        }
    ]
    ```

### 4.2 Sort Startup Ideas by Feasibility Score (`GET /startupideas/sort?order=desc`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    [
        {
            "ideaId": 1,
            "title": "Mining Gold Exploration Project",
            "description": "Extensive mining for gold in northern locations with high feasibility.",
            "relatedMineralType": "Gold",
            "feasibilityScore": 90,
            "estimatedCost": 50000
        }
    ]
    ```

### 4.3 Sort Startup Ideas by Estimated Cost (`GET /startupideas/sort?order=asc`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    [
        {
            "ideaId": 1,
            "title": "Mining Gold Exploration Project",
            "description": "Extensive mining for gold in northern locations with high feasibility.",
            "relatedMineralType": "Gold",
            "feasibilityScore": 90,
            "estimatedCost": 50000
        }
    ]
    ```

## 5. User Favorites

### 5.1 List Saved Ideas (`GET /favorites/{userId}`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**
    ```json
    [
        {
            "ideaId": 1,
            "title": "Mining Gold Exploration Project",
            "description": "Extensive mining for gold in northern locations with high feasibility.",
            "relatedMineralType": "Gold",
            "feasibilityScore": 90,
            "estimatedCost": 50000
        }
    ]
    ```

### 5.2 Update Favorite (`PUT /favorites/{favoriteId}`)
- **Request Body:**
    ```json
    {
        "ideaId": 2
    }
    ```
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (200 OK):**

### 5.3 Remove Favorite (`DELETE /favorites/{favoriteId}`)
- **Request Headers:**
    ```http
    Authorization: Bearer <token>
    ```
- **Response Body on Success (204 No Content):`