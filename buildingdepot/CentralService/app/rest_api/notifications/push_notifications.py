"""
CentralService.rest_api.network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module handles push notifications, which are messages sent out to some system or
device instantaneously. The default implementation of this class uses Rabbit MQ to send out
push notifications. If a different push notification service must be used, for example Firebase,
then this class must be extended in another file. After extending this class and implementing
'send', you must update cs_config to point to the implementation that should be loaded.

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

class PushNotification:
    def send(self, recipient_id, message, destination=''):
        """
        Sends a message to the push notification system selected during install.
        recipient_id (str) : <token or key of the intended recipient of the message>
        message (str) : <message to send to recipient>
        destination (str) : <name of exchange or topic to send the message to - optional depending on notification system>
        """
        raise NotImplementedError('Must override this method in a subclass')
