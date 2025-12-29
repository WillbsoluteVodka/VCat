"""Communication module disabled for minimal run.

This module previously implemented `PortalServer` and `PortalClient`
for peer-to-peer teleport messages. Those features are disabled now.
Minimal stub classes are provided to avoid import errors elsewhere.
"""

class PortalServer:
    """Stub server - disabled in minimal mode."""
    def __init__(self, *args, **kwargs):
        print("PortalServer stub initialized (disabled)")

    def start(self):
        print("PortalServer.start() called - disabled")

    def send(self, message):
        print("PortalServer.send() called - disabled")

    def stop(self):
        print("PortalServer.stop() called - disabled")


class PortalClient:
    """Stub client - disabled in minimal mode."""
    def __init__(self, *args, **kwargs):
        print("PortalClient stub initialized (disabled)")

    def connect(self):
        print("PortalClient.connect() called - disabled")

    def send(self, message):
        print("PortalClient.send() called - disabled")

    def start_receiving(self):
        print("PortalClient.start_receiving() called - disabled")

    def disconnect(self):
        print("PortalClient.disconnect() called - disabled")

