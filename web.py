import re
import os
import atlassian_jwt
import requests
import cPickle as pickle
import jwt as jwt
from PyBambooHR import PyBambooHR
from flask import Flask, request, render_template
from ac_flask import ACAddon
from jwt.exceptions import DecodeError

app = Flask(__name__)
app.clients = None


def save_clients():
    with open('clients.pk', 'wb') as f:
        pickle.dump(app.clients, f, pickle.HIGHEST_PROTOCOL)


def load_clients():
    try:
        with open('clients.pk', 'rb') as f:
            app.clients = pickle.load(f)
    except:
        app.clients = {}
        pass


def get_client(id):
    if app.clients is None:
        load_clients()

    return app.clients.get(id)


def set_client(client):
    if app.clients is None:
        load_clients()

    app.clients[client['clientKey']] = client
    save_clients()


ADDON_KEY = "it-confluence-bamboohr"
bamboo = PyBambooHR(
    subdomain=os.environ['BAMBOOHR_SUBDOMAIN'],
    api_key=os.environ['BAMBOOHR_API_KEY']
)
ac = ACAddon(app, key=ADDON_KEY, get_client_by_id_func=get_client, set_client_by_id_func=set_client)


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

    if get_client(client['clientKey']):
        token = request.headers.get('authorization', '').replace(r'^JWT ', '')
        if not token:
            # Is not first install, but did not sign the request properly for
            # an update
            return '', 401
        try:
            jwt.decode(token, get_client(client['clientKey'])['sharedSecret'])
        except (ValueError, DecodeError):
            # Invalid secret, so things did not get installed
            return '', 401

    set_client(client)
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
    client = get_client(client_key)

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


@ac.module(key="configurePage", name="Configure", 
           location="configurePage", methods=['GET', 'POST'])
def configure_page():
    return '', 204


@app.template_filter('stripalpha')
def strip_alpha(s):
    return re.sub(r'[^\d+]+', '', s)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', "3000")))
