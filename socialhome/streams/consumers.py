from channels.generic.websockets import WebsocketConsumer


class StreamConsumer(WebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return [kwargs.get("stream")]
