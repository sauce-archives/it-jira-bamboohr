import os
import re

import requests
from atlassian_jwt import encode_token
from flask import Flask, render_template, request
from flask_atlassian_connect import AtlassianConnect
from PyBambooHR import PyBambooHR
from raven.contrib.flask import Sentry
from werkzeug.contrib.fixers import ProxyFix

from flask_sslify import SSLify

from .client import Client
from .shared import db

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
sslify = SSLify(app)
app.config.from_object('app.config.%sConfig' %
                       os.environ.get('FLASK_ENV', 'development').title())
db.init_app(app)
if os.environ.get('SENTRY_DSN'):
    sentry = Sentry(app, dsn=os.environ['SENTRY_DSN'])
ac = AtlassianConnect(app, client_class=Client)


@app.template_filter('stripalpha')
def strip_alpha(s):
    return re.sub(r'[^\d+]+', '', s or '')


def get_bamboohr(client):
    return PyBambooHR(
        subdomain=client['bamboohrSubdomain'],
        api_key=client['bamboohrApi']
    )


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
        'GET', issue_url, app.config.get('ADDON_KEY'), 
        client.sharedSecret)
    result = requests.get(
        client.baseUrl.rstrip('/') + issue_url,
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


@ac.module("configurePage", name="Configure")
def configure_page(client):
    if request.method.lower() == 'post':
        try:
            client.bamboohrApi = request.form['bamboohr_api']
            client.bamboohrSubdomain = request.form['bamboohr_subdomain']
            Client.save(client)
            return render_template('configure_page_success.html')
        except ValueError:
            pass

    args = request.args.copy()
    del args['jwt']

    signature = encode_token(
        'POST',
        request.path + '?' + urlencode(args),
        client.clientKey,
        client.sharedSecret)
    args['jwt'] = signature

    return render_template(
        'configure_page.html',
        xdm_e=args['xdm_e'],
        url=request.path + '?' + urlencode(args)
    )


@app.route('/healthcheck')
def healthcheck():
    return 'OK', 200


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(
        debug=True,
        port=int(os.environ.get('PORT', "3000")),
        host="0.0.0.0"
    )
