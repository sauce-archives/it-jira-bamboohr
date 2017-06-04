from flask import jsonify, redirect, request, abort
from functools import wraps
import atlassian_jwt
import logging
import re


class ACAddon(object):
    """Atlassian Connect Addon"""
    def __init__(self, app, key, get_client_by_id_func=None, set_client_by_id_func=None):
        self.descriptor = {
            "name": "Add bamboohr information to tickets",
            "description": "Add bamboohr information to tickets",
            "key": key,
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
        self.get_client_by_id = get_client_by_id_func
        self.set_client_by_id = set_client_by_id_func

        self.app = app
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


    def lifecycle(self, name, path=None):
        if path is None:
            path = "/lifecycle/" + name

        self.descriptor.setdefault('lifecycle', {})[name] = path

        def inner(func):
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
            return self.app.route(rule=path, **kwargs)(func)

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