from .shared import db


class Client(db.Model):
    clientKey = db.Column(db.String(50), primary_key=True)
    baseUrl = db.Column(db.String(100))
    sharedSecret = db.Column(db.String(100))
    bamboohrApi = db.Column(db.String(40))
    bamboohrSubdomain = db.Column(db.String(40))
    bamboohrSelectedFields = db.Column(
        'bamboohrSelectedFields',
        db.LargeBinary(),
        default="""["displayName","jobTitle","department","supervisor","location","workEmail","workPhone","mobilePhone"]"""
    )

    def __repr__(self):
        return 'Client(clientKey="%s", baseUrl="%s", sharedSecret="%s", bamboohrApi="%s", bamboohrSubdomain="%s")' % (
            self.clientKey, self.baseUrl, self.sharedSecret, self.bamboohrApi, self.bamboohrSubdomain
        )

    def __str__(self):
        return 'Client:\n\tclientKey=%s\n\tbaseUrl=%s\n\tsharedSecret=%s\n\tbamboohrApi=%s\n\tbamboohrSubdomain=%s\n' % (
            self.clientKey, self.baseUrl, self.sharedSecret, self.bamboohrApi, self.bamboohrSubdomain
        )

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
