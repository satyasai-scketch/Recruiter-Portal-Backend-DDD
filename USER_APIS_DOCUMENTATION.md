# User Management APIs

This document describes the newly implemented User Management APIs for the Recruiter AI Backend.

## Overview

Two new endpoints have been added to the authentication router (`/api/v1/auth`):

1. **GET /users** - Retrieve all users with pagination
2. **PATCH /users/{user_id}** - Update a specific user

## Authentication

Both endpoints require authentication via Bearer token. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Get All Users

**Endpoint:** `GET /api/v1/auth/users`

**Description:** Retrieves a paginated list of all users in the system.

**Query Parameters:**
- `skip` (optional, default: 0): Number of users to skip for pagination
- `limit` (optional, default: 100): Maximum number of users to return

**Response:**
```json
[
  {
    "id": "user-uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_active": true,
    "role_id": "role-uuid",
    "role_name": "recruiter",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/users?skip=0&limit=10" \
  -H "Authorization: Bearer <your_token>"
```

### 2. Update User

**Endpoint:** `PATCH /api/v1/auth/users/{user_id}`

**Description:** Updates a specific user's information.

**Path Parameters:**
- `user_id`: The UUID of the user to update

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "first_name": "Updated First Name",
  "last_name": "Updated Last Name",
  "phone": "+1234567890",
  "is_active": true,
  "role_id": "new-role-uuid"
}
```

**Note:** All fields are optional. Only provided fields will be updated.

**Response:**
```json
{
  "id": "user-uuid",
  "email": "newemail@example.com",
  "first_name": "Updated First Name",
  "last_name": "Updated Last Name",
  "phone": "+1234567890",
  "is_active": true,
  "role_id": "new-role-uuid",
  "role_name": "admin",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Example Request:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/auth/users/user-uuid" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Updated Name",
    "phone": "+1234567890"
  }'
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Implementation Details

The APIs follow the existing CQRS (Command Query Responsibility Segregation) pattern used throughout the application:

- **Commands:** `UpdateUser` command for user updates
- **Queries:** `ListAllUsers` and `GetUser` queries for data retrieval
- **Services:** `UserService` handles business logic
- **Repository:** `SQLAlchemyUserRepository` handles data persistence

## Validation Rules

### UserUpdate Schema
- `email`: Must be a valid email format and unique across all users
- `first_name`: 1-50 characters
- `last_name`: 1-50 characters
- `phone`: Maximum 20 characters
- `is_active`: Boolean value
- `role_id`: Must reference an existing role

## Security Considerations

1. **Authentication Required:** Both endpoints require valid JWT tokens
2. **Email Uniqueness:** Email updates are validated for uniqueness
3. **Role Validation:** Role ID updates are validated against existing roles
4. **Input Validation:** All input data is validated using Pydantic schemas

## Testing

A test script `test_user_apis.py` is provided to test the endpoints. Make sure to:

1. Start the server: `uvicorn app.main:app --reload`
2. Update the test credentials in the script
3. Run: `python test_user_apis.py`
