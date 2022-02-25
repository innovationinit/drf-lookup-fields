import base64
import json
import uuid


def fake_request_factory(header_name):
    class FakeRequest(object):

        def __init__(self, content=None, raw_content=None, user=None):
            self._content = base64.b64encode(json.dumps(content).encode('utf-8')) if content else raw_content
            self.user = user

        @property
        def META(self):
            if self._content:
                return {
                    header_name: self._content,
                }
            return {}
    return FakeRequest


def get_different_uuid(old_uuid):
    new_uuid = uuid.uuid4()
    while old_uuid == new_uuid:
        new_uuid = uuid.uuid4()
    return new_uuid
