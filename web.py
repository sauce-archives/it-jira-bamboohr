import re
import os
import atlassian_jwt
import requests
import cPickle as pickle
import jwt as jwt
from PyBambooHR import PyBambooHR
from flask import Flask, request, jsonify, redirect, render_template
from ac_flask import ACAddon

clients = {}


def save_clients():
    global clients
    with open('clients.pk', 'wb') as f:
        pickle.dump(clients, f, pickle.HIGHEST_PROTOCOL)


def load_clients():
    global clients
    try:
        with open('clients.pk', 'rb') as f:
            clients = pickle.load(f)
    except:
        pass


ADDON_KEY = "it-confluence-bamboohr"
bamboo = PyBambooHR(
    subdomain=os.environ['BAMBOOHR_SUBDOMAIN'],
    api_key=os.environ['BAMBOOHR_API_KEY']
)

app = Flask(__name__)
ac = ACAddon(app, key=ADDON_KEY)
load_clients()

class SimpleAuthenticator(atlassian_jwt.Authenticator):
    def get_shared_secret(self, client_key):
        return clients[client_key]['sharedSecret']


auth = SimpleAuthenticator()


@ac.lifecycle('installed')
def installed():
    client = request.get_json()
    response = requests.get(
        client['baseUrl'].rstrip('/') + '/plugins/servlet/oauth/consumer-info')
    response.raise_for_status()

    key = re.search(r"<key>(.*)</key>", response.text).groups()[0]
    publicKey = re.search(
        r"<publicKey>(.*)</publicKey>", response.text
    ).groups()[0]

    if key != client['clientKey'] or publicKey != client['publicKey']:
        raise Exception("Invalid Credentials")

    if clients.get(client['clientKey']):
        token = request.headers.get('authorization', '').replace(r'^JWT ', '')
        if not token:
            # Is not first install, but did not sign the request properly for
            # an update
            return '', 401
        try:
            jwt.decode(token, clients[client['clientKey']]['sharedSecret'])
        except jwt.exceptions.DecodeError:
            # Invalid secret, so things did not get installed
            return '', 401

    clients[client['clientKey']] = client
    save_clients()
    return '', 204


@ac.webpanel(key="userPanel",
          name="Bamboo Employee Information",
          location="atl.jira.view.issue.right.context",
          conditions=[{
              "condition": "project_type",
              "params": {"projectTypeKey": "service_desk"}
          }])
def right_context():
    client_key = auth.authenticate(request.method, request.url,
                                   request.headers)
    client = clients[client_key]

    ping_url = '/rest/api/latest/issue/' + request.args.get('issueKey')
    jwt_authorization = 'JWT %s' % atlassian_jwt.encode_token(
        'GET', ping_url, ADDON_KEY, client['sharedSecret'])
    result = requests.get(
        client['baseUrl'].rstrip('/') + ping_url,
        headers={'Authorization': jwt_authorization})
    result.raise_for_status()
    email = result.json()['fields']['reporter']['emailAddress']

    employee = next((e for e in bamboo.get_employee_directory()
                     if e['workEmail'] == email), None)
    if not employee:
        return '', 404

    employee.update(bamboo.get_employee(int(employee['id'])))

    return render_template(
        'bamboo_user.html',
        xdm_e=request.args.get('xdm_e'),
        employee=employee
    )


@ac.module(key="userPanel", name="Configure", location="configurePage")
def configure_page():
    return '', 204

@app.template_filter('stripalpha')
def strip_alpha(s):
    return re.sub(r'[^\d+]+', '', s)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', "3000")))
