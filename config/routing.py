from channels import route_class

from socialhome.streams.consumers import StreamConsumer

channel_routing = [
    route_class(StreamConsumer, path=r'^/ch/streams/(?P<stream>[^/]+)/$'),
]
