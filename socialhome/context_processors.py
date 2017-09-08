from socialhome.streams.enums import StreamType


def enums(request):
    """Add some useful enums to the context."""
    return {
        "ENUMS": {
            "StreamType": StreamType.to_dict(),
        },
    }
