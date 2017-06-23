from .. import Client
import unittest


class ClientTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_repr(self):
        client = Client()
        self.assertEquals("Client(bamboohrApi=None, "
                          "bamboohrSelectedFields=None, "
                          "bamboohrSubdomain=None, "
                          "baseUrl=None, "
                          "clientKey=None, "
                          "sharedSecret=None)",
                          repr(client))

    def test_str(self):
        client = Client()
        self.assertEquals("""Client:
\tbamboohrApi=None
\tbamboohrSelectedFields=None
\tbamboohrSubdomain=None
\tbaseUrl=None
\tclientKey=None
\tsharedSecret=None""", str(client))


if __name__ == '__main__':
    unittest.main()
