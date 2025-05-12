from flask_login import UserMixin
import firebase_admin
from firebase_admin import credentials, auth
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK (will be done in the app.py file)
# db = SQLAlchemy() - removed for Firebase implementation

class User(UserMixin):
    def __init__(self, uid, username, email):
        self.id = uid
        self.username = username
        self.email = email

    @staticmethod
    def get_by_email(email):
        try:
            user = auth.get_user_by_email(email)
            
            return User(
                uid=user.uid,
                username=user.display_name or email.split('@')[0],
                email=user.email
            )
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    def get_by_id(uid):
        try:
            user = auth.get_user(uid)
            
            return User(
                uid=user.uid,
                username=user.display_name or user.email.split('@')[0],
                email=user.email
            )
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    # This method is no longer needed since we're using client-side Firebase SDK
    # for user creation, but we'll keep it for compatibility
    @staticmethod
    def create_user(email, password, username):
        # Simply fetch the user that was created by the client-side SDK
        # We don't need to create the user again on the server side
        try:
            try:
                # Check if the user exists by email
                user_record = auth.get_user_by_email(email)
                
                # User exists, return a User object
                return User(
                    uid=user_record.uid,
                    username=username or user_record.display_name or email.split('@')[0],
                    email=email
                )
            except auth.UserNotFoundError:
                # If user doesn't exist in Firebase, it means there was an issue with client-side creation
                logger.warning(f"User with email {email} not found in Firebase after client-side creation")
                return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None