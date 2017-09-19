from unittest.mock import Mock


class MockStream(Mock):
    def get_content(self, *args, **kwargs):
        return [], {}
