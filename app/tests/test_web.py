import unittest
from atlassian_jwt.encode import encode_token
import requests_mock
from mock import patch
from .. import app, db, Client
from .fixtures import (
    rest_api_project_expand_id_key_name_project_properties,
    rest_api_project_properties_it_jira_bamboohr,
    rest_api_latest_issue_GAV_
)
try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode


class WebTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        app.debug = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        pass

    @patch('app.web.get_bamboohr')
    @requests_mock.mock()
    def test_web_panel(self, mock_get_bamboohr, m):
        employee = {
            "id": "123",
            "displayName": "Test Person",
            "firstName": "Test",
            "lastName": "Person",
            "jobTitle": "Testing Coordinator",
            "workPhone": "555-555-5555",
            "workPhoneExtension": "",
            "mobilePhone": "555-555-5555",
            "workEmail": "gavin@saucelabs.com",
            "department": "Useless Department",
            "location": "Testville, US",
            "division":  None,
            "photoUploaded":  False,
            "photoUrl": "https://iws.bamboohr.com/images/photo_placeholder.gif",
            'supervisor': 'Supervisor Name'
        }
        m.register_uri(
            "GET",
            'https://gavindev.atlassian.net'
            '/rest/api/latest/issue/TEST-1',
            json=rest_api_latest_issue_GAV_)

        class MockBamboo(object):

            def get_employee_directory(self):
                return [employee]

            def get_employee(self, id):
                return employee

        bamboo = MockBamboo()
        mock_get_bamboohr.return_value = bamboo

        client = dict(
            baseUrl='https://gavindev.atlassian.net',
            clientKey='test_web_panel',
            publicKey='public123',
            sharedSecret='myscret')
        with app.app_context():
            Client.save(client)

        url = '/atlassian_connect/webpanel/userPanel?issueKey=TEST-1'
        auth = encode_token(
            'GET',
            url,
            client.get('clientKey'),
            client.get('sharedSecret'))

        rv = self.app.get(url, headers={'authorization': 'JWT ' + auth})
        self.assertEquals(200, rv.status_code)
        self.assertIn('<td>Test Person</td>'.encode(), rv.data)
        self.assertIn('<th>Display Name</th>'.encode(), rv.data)

    @requests_mock.mock()
    def test_configurePage(self, m):
        m.register_uri(
            'GET',
            'https://gavindev.atlassian.net/rest/api/2/project?expand=id,key,name,project.properties',
            json=rest_api_project_expand_id_key_name_project_properties)
        m.register_uri(
            'GET',
            'https://gavindev.atlassian.net/rest/api/2/project/10000/properties/it-jira-bamboohr',
            json=rest_api_project_properties_it_jira_bamboohr)
        m.register_uri(
            'GET',
            'https://gavindev.atlassian.net/rest/api/2/project/10100/properties/it-jira-bamboohr',
            text='Not Found', status_code=404)
        m.register_uri(
            'GET',
            'https://gavindev.atlassian.net/rest/api/2/project/10200/properties/it-jira-bamboohr',
            text='Not Found', status_code=404)

        client = dict(
            baseUrl='https://gavindev.atlassian.net',
            clientKey='test_configurePage',
            publicKey='public123',
            sharedSecret='myscret',)
        with app.app_context():
            Client.save(client)
        args = {"xdm_e": client['baseUrl']}
        url = '/atlassian_connect/module/configurePage?' + urlencode(args)

        args['jwt'] = encode_token(
            'GET',
            url,
            client['clientKey'],
            client['sharedSecret'])

        rv = self.app.get('/atlassian_connect/module/configurePage?' + urlencode(args))
        self.assertEquals(200, rv.status_code)

    @requests_mock.mock()
    def test_post_configurePage(self, m):
        m.register_uri(
            'GET',
            'https://gavindev.atlassian.net/rest/api/2/project?expand=id,key,name,project.properties',
            json=rest_api_project_expand_id_key_name_project_properties)
        m.register_uri(
            'PUT',
            'https://gavindev.atlassian.net/rest/api/2/project/10000/properties/it-jira-bamboohr',
            json=rest_api_project_properties_it_jira_bamboohr)
        m.register_uri(
            'DELETE',
            'https://gavindev.atlassian.net/rest/api/2/project/10100/properties/it-jira-bamboohr',
            text='Not Found', status_code=404)
        m.register_uri(
            'DELETE',
            'https://gavindev.atlassian.net/rest/api/2/project/10200/properties/it-jira-bamboohr',
            text='Not Found', status_code=404)
        client = dict(
            baseUrl='https://gavindev.atlassian.net',
            clientKey='test_post_configurePage',
            publicKey='public123',
            sharedSecret='myscret',)
        with app.app_context():
            Client.save(client)
        args = {"xdm_e": client['baseUrl']}
        url = '/atlassian_connect/module/configurePage?' + urlencode(args)

        args['jwt'] = encode_token(
            'POST',
            url,
            client['clientKey'],
            client['sharedSecret'])

        rv = self.app.post('/atlassian_connect/module/configurePage?' + urlencode(args),
                           data={
                               "bamboohr_subdomain": "notreal",
                               "bamboohr_api": "ILikeMyRandomAPIKey",
                               "project_10000": "on",
                               "bamboohr_fields": """["supervisor"]"""
                           })
        self.assertEquals(200, rv.status_code)
        with app.app_context():
            updated_client = Client.load(client['clientKey'])
            self.assertEquals("notreal", updated_client.bamboohrSubdomain)
            self.assertEquals("ILikeMyRandomAPIKey", updated_client.bamboohrApi)
            self.assertEquals("""["supervisor"]""", updated_client.bamboohrSelectedFields)


if __name__ == '__main__':
    unittest.main()
