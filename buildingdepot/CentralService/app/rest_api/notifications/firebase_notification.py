import firebase_admin
from firebase_admin import messaging
from firebase_admin import credentials
from push_notifications import PushNotification
import os

try:
    cred = credentials.Certificate('/home/kiithnabaal/firebase-credentials.json')
    default_app = firebase_admin.initialize_app(cred)
except ValueError:
    pass

class FirebaseNotification(PushNotification):
    def send(self, recipient_id, message):
        notification = messaging.Message(data={'notification_message': message}, token=recipient_id)
        response = messaging.send(notification)
