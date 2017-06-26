# Jira BambooHR Integrations

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/saucelabs/it-jira-bamboohr)

This project is a simple jira integration that adds a BambooHR webpanel that will show you some information about the reporter pulled from bamboohr

## Config Vars

All configuration is done through environmental variables

```
DATABASE_URL: see http://flask-sqlalchemy.pocoo.org/2.1/config/#connection-uri-format
FLASK_ENV:    production
```

Optional
`SENTRY_DSN` - For any error reporting

## Accessing

Add `https://<your domain here>/atlassian_connect/descriptor` to your jira cloud addons
