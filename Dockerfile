FROM python:2.7-slim

RUN apt-get update && apt-get install --yes build-essential libmysqlclient-dev

RUN mkdir /app
WORKDIR /app
COPY gunicorn.conf logging.conf requirements.txt tasks.py tasks.py web.py /app/
COPY templates/ /app/templates/
RUN pip install gunicorn json-logging-py -r requirements.txt

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":3000", "web:app"]
