import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user_schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse, LoginRequest

# Fixtures for common test data
@pytest.fixture
def user_base_data():
    return {
        "username": "john_doe_123",
        "email": "john.doe@example.com",
        "full_name": "John Doe",
        "bio": "I am a software engineer with over 5 years of experience in building scalable web applications using Python and JavaScript.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe.jpg"
    }

@pytest.fixture
def user_create_data(user_base_data):
    return {**user_base_data, "password": "SecurePassword123!"}

@pytest.fixture
def user_update_data():
    return {
        "email": "john.doe.new@example.com",
        "full_name": "John H. Doe",
        "bio": "I specialize in backend development with Python and Node.js.",
        "profile_picture_url": "https://example.com/profile_pictures/john_doe_updated.jpg"
    }

@pytest.fixture
def user_response_data():
    return {
        "id": "unique-id-string",
        "username": "testuser",
        "email": "test@example.com",
        "last_login_at": datetime.now(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "links": []
    }

@pytest.fixture
def login_request_data():
    return {"username": "john_doe_123", "password": "SecurePassword123!"}

# Tests for UserBase
def test_user_base_valid(user_base_data):
    user = UserBase(**user_base_data)
    assert user.username == user_base_data["username"]
    assert user.email == user_base_data["email"]

def test_user_base_config_example(user_base_data):
    example = UserBase.Config.json_schema_extra['example']
    assert UserBase(**example)

# Tests for UserCreate
def test_user_create_valid(user_create_data):
    user = UserCreate(**user_create_data)
    assert user.username == user_create_data["username"]
    assert user.password == user_create_data["password"]

def test_user_create_config_example(user_base_data):
    example = UserCreate.Config.json_schema_extra['example']
    assert UserCreate(**example)

# Tests for UserUpdate
def test_user_update_partial(user_update_data):
    partial_data = {"email": user_update_data["email"]}
    user_update = UserUpdate(**partial_data)
    assert user_update.email == partial_data["email"]

# Tests for UserResponse
def test_user_response_datetime(user_response_data):
    user = UserResponse(**user_response_data)
    assert user.last_login_at == user_response_data["last_login_at"]
    assert user.created_at == user_response_data["created_at"]
    assert user.updated_at == user_response_data["updated_at"]

# Tests for LoginRequest
def test_login_request_valid(login_request_data):
    login = LoginRequest(**login_request_data)
    assert login.username == login_request_data["username"]
    assert login.password == login_request_data["password"]

# Parametrized tests for username and email validation
@pytest.mark.parametrize("username, expected", [
    ("test_user", "test_user"),
    ("test-user", "test-user"),
    ("testuser123", "testuser123"),
    ("JOHN_Doe_123", "john_doe_123"),  # Normalization check
    ("john_doe_123", "john_doe_123"),
    ("John_DOE_123", "john_doe_123")
])
def test_user_base_username_valid_and_normalized(username, expected, user_base_data):
    user_base_data["username"] = username
    user = UserBase(**user_base_data)
    assert user.username == expected, f"Username should be normalized and stored as {expected} but found {user.username}"

# Combine tests for invalid usernames including start and end validations
@pytest.mark.parametrize("username", [
    "john doe", "john?doe", "1john", "john@", "jo", "a"*51, "_johndoe", "johndoe-",  # Invalid characters and lengths
    "9john", "-johndoe", "johndoe_",  # Invalid start and end characters
])
def test_user_base_username_invalid(user_base_data, username):
    user_base_data["username"] = username
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Test for boundary conditions of username length
@pytest.mark.parametrize("username", ["abc", "a"*50])  # Minimum and maximum valid lengths
def test_user_base_username_max_length_valid(user_base_data, username):
    user_base_data["username"] = username
    user = UserBase(**user_base_data)
    assert len(user.username) == len(username), f"Username {username} should be exactly {len(username)} characters long."

@pytest.mark.parametrize("username", ["ab", "abc*50"])  # Below minimum length
def test_user_base_username_max_length_invalid(user_base_data, username):
    user_base_data["username"] = username
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Test for usernames starting and ending correctly
@pytest.mark.parametrize("username", ["aJohnDoe1", "z1234567890"])
def test_user_base_username_start_end_valid(user_base_data, username):
    user_base_data["username"] = username
    user = UserBase(**user_base_data)
    assert user.username[0].isalpha() and user.username[-1].isalnum(), "Username must start with a letter and end with an alphanumeric character."

# Test Profile Picture URL Validation
@pytest.mark.parametrize("url", [
    "https://example.com/profile_pictures/john_doe.jpg",
    "https://example.com/profile_pictures/john_doe.jpeg",
    "https://example.com/profile_pictures/john_doe.png"
])
def test_user_base_profile_picture_url_valid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    user = UserBase(**user_base_data)
    # Convert the Url object to string using str() for comparison
    assert user.profile_picture_url == url

@pytest.mark.parametrize("url", [
    "https://example.com/profile_pictures/john_doe.gif",  # Invalid file extension
    "https://example.com/profile_pictures/john_doe.bmp",  # Invalid file extension
    "ftp://example.com/profile_pictures/john_doe.jpg",    # Invalid scheme
    "https://example.com/profile_pictures/john_doe"       # No file extension
])
def test_user_base_profile_picture_url_invalid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

@pytest.mark.parametrize("profile_picture_url", ["https://" + "example.com/" + "a" * 255 + ".jpg"])
def test_profile_picture_url_length_exceeded(profile_picture_url, user_base_data):
    user_base_data["profile_picture_url"] = profile_picture_url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Tests for password validation
# List of passwords and their expected validation messages
password_test_cases = [
    ("Space Password123!", "Password must not contain spaces."),
    ("Short7!", "String should have at least 8 characters."),
    ("A" * 255 + "1a!", "String should have at most 255 characters"),
    ("1startswithdigit", "Password must start with a letter."),  # Testing start with a digit
    ("!starts!with!special", "Password must start with a letter."),  # Testing start with a special character
    ("nouppercase123!", "Password must contain at least one uppercase letter."),
    ("NOLOWERCASE123!", "Password must contain at least one lowercase letter."),
    ("NoDigitPassword!", "Password must contain at least one digit."),
    ("NoSpecialCharacter123", "Password must contain at least one special character."),
    ("ValidPassword1!", None)  # This is assumed to be a valid password
]

@pytest.mark.parametrize("password, expected_error", password_test_cases)
def test_password_validation(user_create_data, password, expected_error):
    user_data = {**user_create_data, "password": password}
    if expected_error:
        with pytest.raises(ValidationError, match=expected_error):
            UserCreate(**user_data)
    else:
        assert UserCreate(**user_data).password == password, "Valid password should pass validation without errors."

# Tests for validate email
@pytest.mark.parametrize("input_email, expected_email", [
    ("John.Doe@example.com", "john.doe@example.com"),  # Mixed case to lowercase
    ("JANE.DOE@EXAMPLE.COM", "jane.doe@example.com"),  # Upper case to lowercase
    ("joe.bloggs@Example.org", "joe.bloggs@example.org"),  # Domain part normalization
    ("sally.smith@EXAMPLE.EDU", "sally.smith@example.edu"),  # Entire email normalization
])
def test_email_normalization(input_email, expected_email):
    # Create a UserBase instance with the input email
    user = UserBase(username="default_username_123", email=input_email)
    # Check that the email has been normalized to lowercase
    assert user.email == expected_email, f"Email should be normalized to {expected_email} but got {user.email}"

@pytest.mark.parametrize("email", [
    "user@example.com",
    "contact@organization.org",
    "admin@agency.gov",
    "info@educational.edu",
    "support@network.net",
    "invalid@domain.xyz"  # This should fail
])
def test_email_domain_validation(email):
    if email.endswith((".com", ".org", ".gov", ".edu", ".net")):
        # This should pass validation
        user = UserBase(username="default_username_123", email=email)  # Provide a default username
        assert user.email == email.lower()  # Use the instantiated user object for comparison
    else:
        # This should raise a validation error
        with pytest.raises(ValidationError):
            UserBase(email=email)

@pytest.mark.parametrize("invalid_email", [
    "invalid@domain.xyz",  # Invalid domain that should trigger a validation error
    "username@localhost"  # Typically invalid for internet-facing applications
])
def test_invalid_email_domain(invalid_email):
    with pytest.raises(ValidationError):
        UserBase(username="default_username", email=invalid_email)
