"""
CentralService.rest_api.network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles push notifications, which are messages sent out to some system or
device instantaneously. The default implementation of this class uses Rabbit MQ to send out
push notifications. If a different push notification service must be used, for example Firebase,
then this class must be extended in another file. After extending this class and implementing
'send', you must update cs_config to point to the implementation that should be loaded.

@copyright: (c) 2020 SynergyLabs
@license: CMU License. See License file for details.
"""

import firebase_admin
import pika
from firebase_admin import credentials
from firebase_admin import messaging

from ... import notification_type, firebase_credentials


class FirebaseNotification:
    def __init__(self):
        try:
            self.cred = credentials.Certificate(firebase_credentials)
            default_app = firebase_admin.initialize_app(self.cred)
        except ValueError:
            pass

    def send(self, recipient_id, message, destination=""):
        notification = messaging.Message(
            data={"notification_message": message}, token=recipient_id
        )
        response = messaging.send(notification)


class RabbitMQNotification:
    def connect_broker(self, destination):
        """
        Args:
            destination:
        Returns:
            pubsub: object corresponding to the connection with the broker
        """
        try:
            pubsub = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost")
            )
            channel = pubsub.channel()
            channel.exchange_declare(exchange=destination, type="direct")
            channel.close()
            return pubsub
        except Exception as e:
            print("Failed to open connection to broker " + str(e))
            return None

    def send(self, recipient_id, message, destination=""):
        pubsub = self.connect_broker(destination)
        channel = pubsub.channel()
        channel.basic_publish(
            exchange=destination, routing_key=recipient_id, body=message
        )

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print("Failed to end RabbitMQ session " + str(e))


class PushNotification:
    firebase_instance = FirebaseNotification()
    rabbitmq_instance = RabbitMQNotification()

    @staticmethod
    def get_instance():
        if notification_type == "FIREBASE":
            return PushNotification.firebase_instance
        else:
            return PushNotification.rabbitmq_instance

    def send(self, recipient_id, message, destination=""):
        """
        Sends a message to the push notification system selected during install.
        recipient_id (str) : <token or key of the intended recipient of the message>
        message (str) : <message to send to recipient>
        destination (str) : <name of exchange or topic to send the message to - optional depending on notification system>
        """
        raise NotImplementedError("Must override this method in a subclass")
