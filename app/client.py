from .shared import db
from sqlalchemy.ext.hybrid import hybrid_property
from json import dumps


class Client(db.Model):
    clientKey = db.Column(db.String(50), primary_key=True)
    baseUrl = db.Column(db.String(100))
    sharedSecret = db.Column(db.String(100))
    bamboohrApi = db.Column(db.String(40))
    bamboohrSubdomain = db.Column(db.String(40))
    _bamboohrSelectedFields = db.Column(
        'bamboohrSelectedFields',
        db.LargeBinary(),
        default=dumps([
            "displayName", "jobTitle", "department",
            "supervisor", "location", "workEmail",
            "workPhone", "mobilePhone"])
    )

    @hybrid_property
    def bamboohrSelectedFields(self):
        return self._bamboohrSelectedFields or dumps([
            "displayName", "jobTitle", "department",
            "supervisor", "location", "workEmail",
            "workPhone", "mobilePhone"])

    @bamboohrSelectedFields.setter
    def bamboohrSelectedFields(self, value):
        if value is None:
            raise Exception("Something is setting this to none")
        self._bamboohrSelectedFields = value

    def __repr__(self):
        vals = map(
            lambda x: str(x).replace('client.', ''),
            self.__table__.columns
        )
        vals.sort()
        return 'Client({})'.format(
            ", ".join(map(lambda x: "%s=%s" % (x, repr(self[x])), vals)))

    def __str__(self):
        vals = map(
            lambda x: str(x).replace('client.', ''),
            self.__table__.columns
        )
        vals.sort()
        return "Client:\n\t{}".format(
            "\n\t".join(map(lambda x: "%s=%s" % (x, repr(self[x])), vals)))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, k):
        return getattr(self, k)

    def __iter__(self):
        for c in self.__table__.columns:
            yield c.name, getattr(self, c.name)

    @staticmethod
    def all():
        """Returns an iterator of all clients"""
        return Client.query.all()

    @staticmethod
    def load(clientKey):
        """Loads a Client from the database"""
        return Client.query.filter_by(clientKey=clientKey).first()

    @staticmethod
    def save(client):
        """Save a client to the database"""
        if isinstance(client, dict):
            client = Client(**client)

        existing_client = Client.load(client.clientKey)
        if existing_client:
            for k, v in dict(client).items():
                setattr(existing_client, k, v)
        else:
            db.session.add(client)
        db.session.commit()
