from flask import jsonify, redirect, request, abort
from functools import wraps
from jwt.exceptions import DecodeError
import atlassian_jwt
import httplib
import jwt
import logging
import os
import re
import requests


class ACAddon(object):
    """Atlassian Connect Addon"""
    def __init__(self, app, key, 
                 get_client_by_id_func=None, 
                 set_client_by_id_func=None,
                 config=None,
                 env_prefix="AC_"):
        self.app = app
        self._init_app(app, config, env_prefix)

        self.descriptor = {
            "name": "Add bamboohr information to tickets",
            "description": "Add bamboohr information to tickets",
            "key": key,
            "authentication": {"type": "jwt"},
            "baseUrl": self._relative_to_base('/'),
            "scopes": ["READ"],
            "vendor": {
                "name": "Sauce Labs",
                "url": "https://saucelabs.com"
            },
            "lifecycle": {
                "installed": "/lifecycle/installed",
                "enabled": "/ping",
            },
            "links": {
                "self": self._relative_to_base("/addon/descriptor")
            },
        }
        self.get_client_by_id = get_client_by_id_func
        self.set_client_by_id = set_client_by_id_func

        class SimpleAuthenticator(atlassian_jwt.Authenticator):
            def get_shared_secret(self, client_key):
                return get_client_by_id_func(client_key)['sharedSecret']

        self.auth = SimpleAuthenticator()

        @app.route('/', methods=['GET'])
        def redirect_to_descriptor():
            return redirect('/addon/descriptor')

        @app.route('/addon/descriptor', methods=['GET'])
        def get_descriptor():
            return jsonify(self.descriptor)

    @staticmethod
    def _init_app(app, config, env_prefix):
        app.config.from_object('ac_flask.default_settings')
        if config is not None:
            app.config.from_object(config)

        if env_prefix is not None:
            env_vars = {key[len(env_prefix):]: val for key, val in os.environ.items()}
            app.config.update(env_vars)

        if app.config['DEBUG']:
            # These two lines enable debugging at httplib level (requests->urllib3->httplib)
            # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
            # The only thing missing will be the response.body which is not logged.
            httplib.HTTPConnection.debuglevel = 1

            # You must initialize logging, otherwise you'll not see debug output.
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
        else:
            logging.basicConfig()
            logging.getLogger().setLevel(logging.WARN)

    def _installed_wrapper(self, func):
        def inner(*args, **kwargs):
            client = request.get_json()
            response = requests.get(
                client['baseUrl'].rstrip('/') + 
                '/plugins/servlet/oauth/consumer-info')
            response.raise_for_status()

            key = re.search(r"<key>(.*)</key>", response.text).groups()[0]
            publicKey = re.search(  
                r"<publicKey>(.*)</publicKey>", response.text
            ).groups()[0]

            if key != client['clientKey'] or publicKey != client['publicKey']:
                raise Exception("Invalid Credentials")

            stored_client = self.get_client_by_id(client['clientKey'])
            if stored_client:
                token = request.headers.get('authorization', '').lstrip('JWT ')
                if not token:
                    # Is not first install, but did not sign the request
                    # properly for an update
                    return '', 401
                try:
                    jwt.decode(token,
                               stored_client['sharedSecret'], 
                               audience=stored_client['clientKey'])
                except (ValueError, DecodeError):
                    # Invalid secret, so things did not get installed
                    return '', 401

            self.set_client_by_id(client)
            kwargs['client'] = client
            return func(*args, **kwargs)
        return inner

    def lifecycle(self, name, path=None):
        if path is None:
            path = "/lifecycle/" + name

        self.descriptor.setdefault('lifecycle', {})[name] = path

        def inner(func):
            if name == 'installed':
                return self.app.route(rule=path, methods=['POST'])(
                    self._installed_wrapper(func))
            else:
                return self.app.route(rule=path, methods=['POST'])(func)

        return inner

    def module(self, key, name, location, **kwargs):
        def inner(func):
            path = "/module/" + key
            self.descriptor.setdefault('modules', {})[location] = {
                "url": path,
                "name": {"value": name},
                "key": func.__name__

            }
            return self.route(anonymous=False, rule=path, **kwargs)(func)

        return inner

    def webpanel(self, key, name, location, **kwargs):
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

        self.descriptor.setdefault(
            'modules', {}
        ).setdefault(
            'webPanels', []
        ).append(webpanel_capability)

        def inner(func):
            def inner_inner(*args, **kwargs):
                client_key = self.auth.authenticate(
                    request.method, request.url, request.headers)
                client = self.get_client_by_id(client_key)
                kwargs['client'] = client
                return func(*args, **kwargs)
            return self.app.route(rule=path, **kwargs)(inner_inner)

        return inner

    def _relative_to_base(self, path):
        base = self.app.config['BASE_URL']
        path = '/' + path if not path.startswith('/') else path
        return base + path

    def require_tenant(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            client_key = self.auth.authenticate(
                request.method, 
                request.url,
                request.headers)
            client = self.get_client_by_id(client_key)
            if not client:
                abort(401)
            return func(*args, **kwargs)

        return inner

    def route(self, anonymous=False, *args, **kwargs):
        """
        Decorator for routes with defaulted required authenticated tenants
        """
        def inner(func):
            if not anonymous:
                func = self.require_tenant(func)
            func = self.app.route(*args, **kwargs)(func)
            return func

        return inner