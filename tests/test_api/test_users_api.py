import pytest
from httpx import AsyncClient
from app.database import get_async_db
from app.main import app
from app.models.user_model import User
from app.utils.security import hash_password  # Import your FastAPI app
from uuid import uuid4  # To generate a random UUID

# Example of a test function using the async_client fixture
@pytest.mark.asyncio
async def test_create_user(async_client):
    form_data = {
        "username": "admin",
        "password": "secret",
    }
    # Login and get the access token
    token_response = await async_client.post("/token", data=form_data)
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Define user data for the test
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "sS#fdasrongPassword123!",
    }

    # Send a POST request to create a user
    response = await async_client.post("/users/", json=user_data, headers=headers)

    # Asserts
    assert response.status_code == 201

# You can similarly refactor other test functions to use the async_client fixture
# Tests for get_user
@pytest.mark.asyncio
async def test_retrieve_user(async_client, user, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get(f"/users/{user.id}", headers=headers)
    response_data = response.json()

    # Assert the HTTP status and user ID
    assert response.status_code == 200
    assert response_data["id"] == str(user.id)

    # Additional assertions to verify all relevant fields are returned correctly
    assert response_data["username"] == user.username
    assert response_data["email"] == user.email
    assert response_data["full_name"] == user.full_name  # Ensure this field exists in your User model
    assert response_data["bio"] == user.bio            # Ensure this field exists in your User model
    assert response_data["profile_picture_url"] == user.profile_picture_url  # Ensure this field exists

@pytest.mark.asyncio
async def test_get_nonexistent_user(async_client: AsyncClient, token: str):
    # Generate a random UUID that will not match any user
    non_existent_user_id = uuid4()
    headers = {"Authorization": f"Bearer {token}"}

    # Make the request to the endpoint
    response = await async_client.get(f"/users/{non_existent_user_id}", headers=headers)

    # Assert that the response status code is 404
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

# Tests for update_user
@pytest.mark.asyncio
async def test_update_user(async_client, user, token):
    updated_data = {"email": f"updated_{user.id}@example.com"}
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.put(f"/users/{user.id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == updated_data["email"]

@pytest.mark.asyncio
async def test_delete_user(async_client, user, token):
    headers = {"Authorization": f"Bearer {token}"}
    delete_response = await async_client.delete(f"/users/{user.id}", headers=headers)
    assert delete_response.status_code == 204
    # Verify the user is deleted
    fetch_response = await async_client.get(f"/users/{user.id}", headers=headers)
    assert fetch_response.status_code == 404


@pytest.mark.asyncio
async def test_login_success(async_client, user):
    # Set up the test client for FastAPI application

    # Attempt to login with the test user
    response = await async_client.post("/login/", json={"username": user.username, "password": "MySuperPassword$1234"})
    
    # Check for successful login response
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_user_duplicate_username(async_client, user):
    user_data = {
        "username": user.username,
        "email": "unique@example.com",
        "password": "AnotherPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Username and/or Email already exist" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_register_user_duplicate_email(async_client, user):
    # Use a unique username but the same email as the existing 'user'
    user_data = {
        "username": "unique_username_123",
        "email": user.email,
        "password": "AnotherPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 400
    assert "Username and/or Email already exist" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client):
    user_data = {
        "username": "uniqueuser",
        "email": "notanemail",
        "password": "ValidPassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_user_not_found(async_client):
    login_data = {
        "username": "nonexistentuser",
        "password": "DoesNotMatter123!"
    }
    response = await async_client.post("/login/", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_login_incorrect_password(async_client, user):
    login_data = {
        "username": user.username,
        "password": "IncorrectPassword123!"
    }
    response = await async_client.post("/login/", json=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_delete_user_does_not_exist(async_client, token):
    non_existent_user_id = "00000000-0000-0000-0000-000000000000"  # Valid UUID format
    headers = {"Authorization": f"Bearer {token}"}
    delete_response = await async_client.delete(f"/users/{non_existent_user_id}", headers=headers)
    assert delete_response.status_code == 404

# Test for register
@pytest.mark.asyncio
async def test_register_success(async_client):
    user_data = {
        "username": "newuniqueuser123",
        "email": "newunique@example.com",
        "password": "SecurePassword123!",
    }
    response = await async_client.post("/register/", json=user_data)
    assert response.status_code == 200
    assert "id" in response.json()

# Tests for list_users
@pytest.fixture
async def create_users(async_client, token):
    users_data = [
        {"username": "user1", "email": "user1@example.com", "password": "Password123!"},
        {"username": "user2", "email": "user2@example.com", "password": "Password123!"},
        {"username": "user3", "email": "user3@example.com", "password": "Password123!"},
    ]
    headers = {"Authorization": f"Bearer {token}"}
    for user_data in users_data:
        await async_client.post("/users/", json=user_data, headers=headers)

@pytest.mark.asyncio
async def test_list_users_pagination(async_client, create_users, token):
    headers = {"Authorization": f"Bearer {token}"}
    # Test fetching the first page
    response = await async_client.get("/users/?skip=0&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 2  # Check that only two users are returned

    # Test fetching the second page
    response = await async_client.get("/users/?skip=2&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 1  # Assuming you have three users in total

@pytest.mark.asyncio
async def test_list_users_no_users_found(async_client, token):
    headers = {"Authorization": f"Bearer {token}"}
    # Assuming skip is set beyond the range of existing users
    response = await async_client.get("/users/?skip=3&limit=10", headers=headers)
    assert response.status_code == 400
    assert "No users found" in response.json().get("detail", "")

@pytest.mark.asyncio
async def test_list_users_with_valid_parameters(async_client, create_users, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/users/?skip=0&limit=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert len(data['items']) == 3  # Check if all created users are listed

