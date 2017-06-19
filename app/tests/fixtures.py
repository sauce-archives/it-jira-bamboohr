import json
from os import listdir
from os.path import isfile, join, dirname, splitext

_dir = join(dirname(__file__), 'fixtures')
for f in listdir(_dir):
    _file = join(_dir, f)
    if isfile(_file):
        with open(_file) as data_file:
            locals()[splitext(f)[0]] = json.load(data_file)

jira_client = dict(
    baseUrl='https://gavindev.atlassian.net',
    clientKey='clientKey123',
    publicKey='public123',
    sharedSecret='this_is_my_shared_Secret123')