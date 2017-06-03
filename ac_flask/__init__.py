from flask import jsonify
import atlassian_jwt
import logging
import re

class ACAddon(object):

        def __init__(self, app, key):
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

            self.app = app
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
                return self.app.route(path, methods=['POST'])(func)

            return inner


        def module(self, key, name, location, **kwargs):
            def inner(func):
                path = "/module/" + key
                self.descriptor.setdefault('modules', {})['location'] = {
                    "url": path,
                    "name": { "value": name },
                    "key": func.__name__

                }
                return self.app.route(rule=path, **kwargs)(func)

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
