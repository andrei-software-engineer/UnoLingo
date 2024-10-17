import unittest
import json
from auth_service import app, init_db
import jwt
import sqlite3
import datetime

SECRET_KEY = '2222'

class AuthServiceTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test database before any test
        init_db()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def register_user(self, username, password):
        """Helper method to register a new user"""
        return self.app.post('/register', 
                             data=json.dumps({'username': username, 'password': password}),
                             content_type='application/json')

    def login_user(self, username, password):
        """Helper method to login user and get token"""
        return self.app.post('/login',
                             data=json.dumps({'username': username, 'password': password}),
                             content_type='application/json')

    def validate_token(self, token):
        """Helper method to validate token"""
        return self.app.get('/validate_token', headers={'Authorization': f'Bearer {token}'})

    def test_user_registration(self):
        """Test that a user can register successfully"""
        response = self.register_user('testuser', 'testpassword')
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'User testuser registered successfully!', response.data)

    def test_user_registration_duplicate(self):
        """Test that registering the same user again fails"""
        self.register_user('duplicateuser', 'testpassword')
        response = self.register_user('duplicateuser', 'testpassword')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Username already exists!', response.data)

    def test_login_success(self):
        """Test that a user can log in and receive a JWT token"""
        self.register_user('loginuser', 'loginpassword')
        response = self.login_user('loginuser', 'loginpassword')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)

    def test_login_failure(self):
        """Test that invalid login credentials return an error"""
        self.register_user('failuser', 'failpassword')
        response = self.login_user('failuser', 'wrongpassword')
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Invalid credentials', response.data)

    def test_token_validation_success(self):
        """Test that a valid token is validated successfully"""
        self.register_user('tokenuser', 'tokenpassword')
        login_response = self.login_user('tokenuser', 'tokenpassword')
        token = json.loads(login_response.data)['token']
        validate_response = self.validate_token(token)
        self.assertEqual(validate_response.status_code, 200)
        self.assertIn(b'Token is valid!', validate_response.data)

    def test_token_validation_invalid(self):
        """Test that an invalid token returns an error"""
        token = jwt.encode({
            'username': 'invaliduser',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
        }, SECRET_KEY, algorithm='HS256')

        validate_response = self.validate_token(token)
        self.assertEqual(validate_response.status_code, 401)
        self.assertIn(b'Token is not valid or expired!', validate_response.data)

    def test_get_user(self):
        """Test fetching a user by their ID"""
        self.register_user('fetchuser', 'fetchpassword')
        conn = sqlite3.connect('auth_service.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', ('fetchuser',))
        user_id = cursor.fetchone()[0]
        conn.close()

        response = self.app.get(f'/user/{user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'fetchuser', response.data)

    def test_get_all_users(self):
        """Test fetching all users"""
        self.register_user('allusers1', 'password1')
        self.register_user('allusers2', 'password2')
        
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreaterEqual(len(data), 2)  # At least two users in response

if __name__ == "__main__":
    unittest.main()
