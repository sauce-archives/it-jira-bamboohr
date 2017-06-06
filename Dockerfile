FROM python:2.7-slim

COPY gunicorn.conf logging.conf requirements.txt tasks.py templates tasks.py web.py /
RUN pip install gunicorn json-logging-py -r requirements.txt

EXPOSE 3000

ENTRYPOINT ["/usr/local/bin/gunicorn", "--config", "/gunicorn.conf", "--log-config", "/logging.conf", "-b", ":3000", "web:app"]
