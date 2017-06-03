import re
import os
import atlassian_jwt
import requests
import cPickle as pickle
from PyBambooHR import PyBambooHR
from flask import Flask, request, jsonify, redirect, render_template

ADDON_KEY = "it-confluence-bamboohr"
clients = {}
bamboo = PyBambooHR(
    subdomain=os.environ['BAMBOOHR_SUBDOMAIN'],
    api_key=os.environ['BAMBOOHR_API_KEY']
)


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


app = Flask(__name__)
descriptor = {
    "name": "Add bamboohr information to tickets",
    "description": "Add bamboohr information to tickets",
    "key": ADDON_KEY,
    "authentication": {"type": "jwt"},
    "baseUrl": "https://dev.gavinmogan.com",
    "scopes": ["READ"],
    "vendor": {
        "name": "Sauce Labs",
        "url": "https://saucelabs.com"
    },
    "lifecycle": {
        "installed": "/lifecycle/installed",
        "enabled": "/ping",
    },
}
load_clients()


def lifecycle(name, path=None):
    if path is None:
        path = "/lifecycle/" + name

    descriptor.setdefault('lifecycle', {})[name] = path

    def inner(func):
        return app.route(path, methods=['POST'])(func)

    return inner


def webpanel(key, name, location, **kwargs):

    if not re.search(r"^[a-zA-Z0-9-]+$", key):
        raise Exception("Webpanel(%s) must match ^[a-zA-Z0-9-]+$" % key)

    path = "/webpanel/" + key

    webpanel_capability = {
        "key": key,
        "name": {"value": name},
        "url": path + '?issueKey={issue.key}',
        "location": location
    }
    if kwargs.get('conditions'):
        webpanel_capability['conditions'] = kwargs.pop('conditions')

    descriptor.setdefault(
        'modules', {}
    ).setdefault(
        'webPanels', []
    ).append(webpanel_capability)

    def inner(func):
        return app.route(rule=path, **kwargs)(func)

    return inner


class SimpleAuthenticator(atlassian_jwt.Authenticator):
    def get_shared_secret(self, client_key):
        return clients[client_key]['sharedSecret']


auth = SimpleAuthenticator()


@app.route('/', methods=['GET'])
def redirect_to_descriptor():
    return redirect('/addon/descriptor')


@app.route('/addon/descriptor', methods=['GET'])
def get_descriptor():
    return jsonify(descriptor)


@lifecycle('installed')
def installed():
    client = request.get_json()
    clients[client['clientKey']] = client
    save_clients()
    return '', 204


@webpanel(key="userPanel",
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


@app.template_filter('stripalpha')
def strip_alpha(s):
    return re.sub(r'[^\d+]+', '', s)


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', "3000")))
