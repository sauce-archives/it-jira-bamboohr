from .shared import db

class Client(db.Model):
    clientKey = db.Column(db.String(50), primary_key=True)
    baseUrl = db.Column(db.String(100))
    sharedSecret = db.Column(db.String(100))
    bamboohrApi = db.Column(db.String(40))
    bamboohrSubdomain = db.Column(db.String(40))


    def __repr__(self):
        return 'Client(clientKey="%s", baseUrl="%s", sharedSecret="%s", bamboohrApi="%s", bamboohrSubdomain="%s")' % (
            self.clientKey, self.baseUrl, self.sharedSecret, self.bamboohrApi, self.bamboohrSubdomain
        )

    def __str__(self):
        return 'Client:\n\tclientKey=%s\n\tbaseUrl=%s\n\tsharedSecret=%s\n\bamboohrApi=%s\n\bamboohrSubdomain=%s\n' % (
            self.clientKey, self.baseUrl, self.sharedSecret, self.bamboohrApi, self.bamboohrSubdomain
        )

    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, k):
        return getattr(self, k)

    def __iter__(self):
        for c in self.__table__.columns:
            yield c.name, getattr(self, c.name)

    @staticmethod
    def load(clientKey):
        """Loads a Client from the database"""
        return Client.query.filter_by(clientKey=clientKey).first()

    @staticmethod
    def save(client):
        """Save a client to the database"""
        existing_client = Client.load(client['clientKey'])
        if existing_client:
            for k, v in dict(client).items():
                setattr(existing_client, k, v)
        else:
            client = Client(client)
            db.session.add(client)
        db.session.commit()
