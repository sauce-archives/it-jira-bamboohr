import re
import os
from atlassian_jwt import encode_token
import requests
import cPickle as pickle
from PyBambooHR import PyBambooHR
from flask import Flask, request, render_template
from ac_flask import ACAddon
try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

app = Flask(__name__)
app.clients = None
app.config['ADDON_VENDOR_URL'] = 'https://saucelabs.com'
app.config['ADDON_VENDOR_NAME'] = 'Sauce Labs'
app.config['ADDON_KEY'] = 'it-confluence-bamboohr'
app.config['ADDON_NAME'] = 'BambooHR Integration'
app.config['ADDON_DESCRIPTION'] = 'Add bamboohr information to tickets'


@app.template_filter('stripalpha')
def strip_alpha(s):
    return re.sub(r'[^\d+]+', '', s)


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


def get_bamboohr(client):
    return PyBambooHR(
        subdomain=client['bamboohr_subdomain'],
        api_key=client['bamboohr_api']
    )


ac = ACAddon(app,
             get_client_by_id_func=get_client,
             set_client_by_id_func=set_client)


@ac.lifecycle('installed')
def installed(client):
    return '', 204


@ac.webpanel(key="userPanel",
             name="Bamboo Employee Information",
             location="atl.jira.view.issue.right.context",
             conditions=[{
                 "condition": "project_type",
                 "params": {"projectTypeKey": "service_desk"}
             }])
def right_context(client):
    issue_url = '/rest/api/latest/issue/' + request.args.get('issueKey')
    jwt_authorization = 'JWT %s' % encode_token(
        'GET', issue_url, app.config.get('ADDON_KEY'), client['sharedSecret'])
    result = requests.get(
        client['baseUrl'].rstrip('/') + issue_url,
        headers={'Authorization': jwt_authorization})
    result.raise_for_status()
    email = result.json()['fields']['reporter']['emailAddress']

    bamboo = get_bamboohr(client)
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


@ac.module(name="Configure")
def configure_page(client):
    if request.method.lower() == 'post':
        try:
            client['bamboohr_api'] = request.form['bamboohr_api']
            client['bamboohr_subdomain'] = request.form['bamboohr_subdomain']
            set_client(client)
            return render_template('configure_page_success.html')
        except ValueError:
            pass

    args = request.args.copy()
    del args['jwt']

    signature = encode_token(
        'POST',
        request.path + '?' + urlencode(args),
        client['clientKey'],
        client['sharedSecret'])
    args['jwt'] = signature

    return render_template(
        'configure_page.html',
        xdm_e=args['xdm_e'],
        url=request.path + '?' + urlencode(args)
    )


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(
        debug=True,
        port=int(os.environ.get('PORT', "3000")),
        host="0.0.0.0"
    )
