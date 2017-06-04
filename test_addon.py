import unittest
import web
import json
import requests_mock
import jwt
import time


# Helpers
def create_jwt_token(clientKey, sharedSecret):
    return jwt.encode({
        'sub': 'admin',
        'iss': clientKey,
        'context': {
            'user': {
                    'userKey': 'admin',
                    'username': 'admin',
                    'displayName': 'admin'
                }
        },
        'exp': time.time() + (1000 * 10),
        'iat': time.time()
    }, sharedSecret)


consumer_info_response = """<?xml version="1.0" encoding="UTF-8"?>
    <consumer>
    <key>abc123</key>
    <name>JIRA</name>
    <publicKey>public123</publicKey>
    <description>Atlassian JIRA at https://gavindev.atlassian.net </description>
    </consumer>"""


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = web.app.test_client()
        web.app.clients = {}

    def tearDown(self):
        pass

    def test_index_redirects(self):
        rv = self.app.get('/')
        self.assertEquals(302, rv.status_code)
        self.assertEquals(
            'http://localhost/addon/descriptor', rv.headers['Location'])
        rv = self.app.get('/', follow_redirects=True)
        self.assertEquals(200, rv.status_code)
        self.assertEquals(
            {"type": "jwt"},
            json.loads(rv.get_data())['authentication']
        )

    def test_descriptor_stuff(self):
        rv = self.app.get('/addon/descriptor')
        self.assertEquals(200, rv.status_code)
        self.assertEquals(
            {"type": "jwt"},
            json.loads(rv.get_data())['authentication']
        )

    def test_lifecycle_installed(self):
        with requests_mock.mock() as m:
            m.get('https://gavindev.atlassian.net/plugins/servlet/oauth/consumer-info',
                  text=consumer_info_response)

            client = dict(
                baseUrl='https://gavindev.atlassian.net',
                clientKey='abc123',
                publicKey='public123')
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json')
            self.assertEquals(204, rv.status_code)

    def test_lifecycle_installed_multiple_no_auth(self):
        """Multiple requests should fail unless auth is provided the second time"""
        with requests_mock.mock() as m:
            m.get('https://gavindev.atlassian.net/plugins/servlet/oauth/consumer-info',
                  text=consumer_info_response)

            client = dict(
                baseUrl='https://gavindev.atlassian.net',
                clientKey='abc123',
                publicKey='public123')
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json')
            self.assertEquals(204, rv.status_code)
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json')
            self.assertEquals(401, rv.status_code)

    def test_lifecycle_installed_multiple_with_auth(self):
        """Multiple requests  should update if the second time has auth"""
        with requests_mock.mock() as m:
            m.get('https://gavindev.atlassian.net/plugins/servlet/oauth/consumer-info',
                  text=consumer_info_response)

            client = dict(
                baseUrl='https://gavindev.atlassian.net',
                clientKey='abc123',
                publicKey='public123',
                sharedSecret='myscret')
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json')
            self.assertEquals(204, rv.status_code)
            # Add auth
            auth = create_jwt_token(client['clientKey'], client['sharedSecret'])
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json',
                               headers={'Authorization': auth})
            self.assertEquals(204, rv.status_code)

    def test_lifecycle_installed_multiple_invalid_auth(self):
        """Multiple requests should error if second update is untrusted"""
        with requests_mock.mock() as m:
            m.get('https://gavindev.atlassian.net/plugins/servlet/oauth/consumer-info',
                  text=consumer_info_response)

            client = dict(
                baseUrl='https://gavindev.atlassian.net',
                clientKey='abc123',
                publicKey='public123',
                sharedSecret='myscret')
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json')
            self.assertEquals(204, rv.status_code)
            # Add auth
            auth = create_jwt_token(client['clientKey'], 'some other secret')
            rv = self.app.post('/lifecycle/installed',
                               data=json.dumps(client),
                               content_type='application/json',
                               headers={'Authorization': auth})
            self.assertEquals(401, rv.status_code)


if __name__ == '__main__':
    unittest.main()
