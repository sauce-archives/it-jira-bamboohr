import os


class Config(object):
    DEBUG = False
    TESTING = False
    APP_NAME = "BambooHR Integration"
    ADDON_NAME = APP_NAME
    ADDON_KEY = 'it-jira-bamboohr'
    ADDON_DESCRIPTION = """
    Add bamboohr information to tickets
    """
    ADDON_VENDOR_URL = 'https://saucelabs.com'
    ADDON_VENDOR_NAME = 'Sauce Labs'

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:////tmp/test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SENTRY_DSN = None
    SENTRY_DSN = os.environ.get('SENTRY_DSN')



class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    BASE_URL = 'https://no idea yet'


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SENTRY_DSN = None