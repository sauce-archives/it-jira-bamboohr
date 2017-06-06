FROM python:2.7-slim

COPY gunicorn.conf logging.conf requirements.txt tasks.py tasks.py web.py /
COPY templates/ /templates/
RUN pip install MySQL-python==1.2.5 gunicorn json-logging-py -r requirements.txt

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":3000", "web:app"]
