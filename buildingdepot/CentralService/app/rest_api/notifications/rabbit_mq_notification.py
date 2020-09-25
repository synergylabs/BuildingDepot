import pika
from push_notifications import PushNotification

class RabbitMQNotification(PushNotification):
    def connect_broker(self):
        """
        Args:
            None:
        Returns:    
            pubsub: object corresponding to the connection with the broker
        """
        try:
            pubsub = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            channel = pubsub.channel()
            channel.exchange_declare(exchange='permission_requests', type='direct')
            channel.close()
            return pubsub
        except Exception as e:
            print "Failed to open connection to broker " + str(e)
            return None

    def send(self, recipient_id, message, destination=''):
        pubsub = self.connect_broker()
        channel = pubsub.channel()
        print "About to send this out"
        print str(recipient_id) + " to send " + str(message) + " to " + str(destination)
        channel.basic_publish(exchange=destination, routing_key=recipient_id, body=message)

        if pubsub:
            try:
                channel.close()
                pubsub.close()
            except Exception as e:
                print "Failed to end RabbitMQ session " + str(e)
