from .. import Client
import unittest


class ClientTestCase(unittest.TestCase):

    def setUp(self):
        self.defaultFieldsStr = '[' + ", ".join([
            '"displayName"', '"jobTitle"',
            '"department"', '"supervisor"',
            '"location"', '"workEmail"',
            '"workPhone"', '"mobilePhone"'
        ]) + ']'
        pass

    def tearDown(self):
        pass

    def test_repr(self):
        client = Client()
        self.maxDiff = None
        self.assertEquals(", ".join([
            "Client(bamboohrApi=None",
            "bamboohrSelectedFields='{}'".format(self.defaultFieldsStr),
            "bamboohrSubdomain=None",
            "baseUrl=None",
            "clientKey=None",
            "sharedSecret=None)"]), repr(client))

    def test_str(self):
        client = Client()
        self.assertEquals("""Client:
\tbamboohrApi=None
\tbamboohrSelectedFields='{}'
\tbamboohrSubdomain=None
\tbaseUrl=None
\tclientKey=None
\tsharedSecret=None""".format(self.defaultFieldsStr), str(client))


if __name__ == '__main__':
    unittest.main()
