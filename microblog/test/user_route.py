import os
import tempfile
import unittest
from app import create_app, db
from app.models import User
from flask import url_for
from io import BytesIO
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

class UserRoutesTestCase(unittest.TestCase):

    def setUp(self):
        db_fd, db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(basedir, 'test_data', 'app.db'),
            'UPLOAD_FOLDER': tempfile.mkdtemp()
        })
        self.client = self.app.test_client()
        self.db_fd = db_fd
        self.db_path = db_path

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    # Helper function to create a user
    def create_user(self, username, email, password):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    # Test cases
    def test_user_registration(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123',
            'password2': 'Password123',
            'location':'AUS'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')

    def test_user_login(self):
        with self.app.app_context():
            self.create_user('testuser', 'test@example.com', 'Password123')

        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)  # Assuming a welcome message after login

    def test_profile_update(self):
        with self.app.app_context():
            self.create_user('testuser', 'test@example.com', 'Password123')

        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'Password123'
            }, follow_redirects=True)
            response = self.client.post('/edit_profile', data={
                'username': 'updateduser',
                'email': 'updated@example.com'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            user = User.query.filter_by(username='updateduser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'updated@example.com')

    def test_follow_unfollow(self):
        with self.app.app_context():
            user1 = self.create_user('user1', 'user1@example.com', 'Password123')
            user2 = self.create_user('user2', 'user2@example.com', 'Password123')

        with self.client:
            self.client.post('/login', data={
                'username': 'user1',
                'password': 'Password123'
            }, follow_redirects=True)
            response = self.client.post(url_for('user.follow', username='user2'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(user1.is_following(user2))

            response = self.client.post(url_for('user.unfollow', username='user2'), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(user1.is_following(user2))

    def test_upload(self):
        with self.app.app_context():
            self.create_user('testuser', 'test@example.com', 'Password123')

        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'Password123'
            }, follow_redirects=True)
            data = {
                'title': 'Test Upload',
                'hashtag': 'fashion',
                'description': 'This is a test upload',
                'upload_time': '2023-04-01 12:00:00'
            }
            data['file'] = (BytesIO(b"abcdef"), 'test.jpg')
            response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'All files successfully uploaded', response.data)


if __name__ == '__main__':
    unittest.main()
