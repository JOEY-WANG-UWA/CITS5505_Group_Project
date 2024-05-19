import unittest
from app import create_app, db
from app.models import User, Upload, Collection, Comment, Message
from config import TestConfig
from datetime import datetime, timezone

class UserModelCase(unittest.TestCase):

    def setUp(self):
        test_app = create_app(TestConfig)
        self.app_context = test_app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = test_app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan1', email='susan@exmaple.com', location='USA')
        u.set_password('susan1')
        self.assertFalse(u.check_password('wrong_password'))
        self.assertTrue(u.check_password('susan1'))

    def test_register_user(self):
        u = User(username='john', email='john@example.com', location='Australia')
        u.set_password('john')
        db.session.add(u)
        db.session.commit()

        registered_user = User.query.filter_by(username='john').first()
        self.assertIsNotNone(registered_user)
        self.assertTrue(registered_user.check_password('john'))

    def test_upload(self):
        u = User(username='testuser', email='test@example.com', location='Testland')
        db.session.add(u)
        db.session.commit()
        upload = Upload(user_id=u.id, title='Test Upload', hashtag='test', description='Test description', upload_time=datetime.now(timezone.utc))
        db.session.add(upload)
        db.session.commit()
        uploaded = Upload.query.filter_by(title='Test Upload').first()
        self.assertIsNotNone(uploaded)
        self.assertEqual(uploaded.description, 'Test description')

    def test_collection(self):
        u = User(username='collector', email='collector@example.com', location='Collectland')
        db.session.add(u)
        db.session.commit()
        upload = Upload(user_id=u.id, title='Collectable Upload', hashtag='collect', description='Collect description', upload_time=datetime.now(timezone.utc))
        db.session.add(upload)
        db.session.commit()
        collection = Collection(user_id=u.id, upload_id=upload.id)
        db.session.add(collection)
        db.session.commit()
        collected = Collection.query.filter_by(user_id=u.id, upload_id=upload.id).first()
        self.assertIsNotNone(collected)

    def test_password_reset(self):
        u = User(username='resetuser', email='reset@example.com', location='Resetland')
        u.set_password('initialpassword')
        db.session.add(u)
        db.session.commit()
        token = u.get_reset_password_token()
        user_from_token = User.verify_reset_password_token(token)
        self.assertEqual(user_from_token, u)
        u.set_password('newpassword')
        db.session.commit()
        self.assertTrue(u.check_password('newpassword'))
        self.assertFalse(u.check_password('initialpassword'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com', location='USA')
        u1.set_password('johnpassword')
        u2 = User(username='susan', email='susan@example.com', location='Australia')
        u2.set_password('susanpassword')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
    
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u1.followers_count(), 0)
    
        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        
        following_users = db.session.scalars(u1.following.select()).all()
        followers_users = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following_users[0].username, 'susan')
        self.assertEqual(followers_users[0].username, 'john')
    
        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_messages(self):
        u1 = User(username='john', email='john@example.com', location='USA')
        u1.set_password('johnpassword')
        u2 = User(username='susan', email='susan@example.com', location='Australia')
        u2.set_password('susanpassword')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        msg1 = Message(sender_id=u1.id, recipient_id=u2.id, body='Hello, Susan!')
        msg2 = Message(sender_id=u2.id, recipient_id=u1.id, body='Hi, John!')
        db.session.add(msg1)
        db.session.add(msg2)
        db.session.commit()

        messages_sent_by_u1 = Message.query.filter_by(sender_id=u1.id).all()
        messages_sent_to_u1 = Message.query.filter_by(recipient_id=u1.id).all()
        self.assertEqual(len(messages_sent_by_u1), 1)
        self.assertEqual(len(messages_sent_to_u1), 1)
        self.assertEqual(messages_sent_by_u1[0].body, 'Hello, Susan!')
        self.assertEqual(messages_sent_to_u1[0].body, 'Hi, John!')

    def test_comments(self):
        u1 = User(username='john', email='john@example.com', location='USA')
        u1.set_password('johnpassword')
        u2 = User(username='susan', email='susan@example.com', location='Australia')
        u2.set_password('susanpassword')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        upload = Upload(user_id=u1.id, title='Test Upload', hashtag='test', description='Test description', upload_time=datetime.now(timezone.utc))
        db.session.add(upload)
        db.session.commit()

        comment1 = Comment(user_id=u2.id, upload_id=upload.id, comment_content='Nice upload!', comment_time=datetime.now(timezone.utc))
        comment2 = Comment(user_id=u1.id, upload_id=upload.id, comment_content='Thank you!', comment_time=datetime.now(timezone.utc))
        db.session.add(comment1)
        db.session.add(comment2)
        db.session.commit()

        comments_on_upload = Comment.query.filter_by(upload_id=upload.id).all()
        self.assertEqual(len(comments_on_upload), 2)
        self.assertEqual(comments_on_upload[0].comment_content, 'Nice upload!')
        self.assertEqual(comments_on_upload[1].comment_content, 'Thank you!')

if __name__ == '__main__':
    unittest.main()

