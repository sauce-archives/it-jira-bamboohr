FROM tiangolo/uwsgi-nginx-flask:flask-python2.7
MAINTAINER Gavin Mogan <gavin@saucelabs.com>
RUN pip install -r requirements.txt
COPY . /app