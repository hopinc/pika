from datetime import datetime
import unittest

from pika_id.pika import Pika, PikaPrefixDefinition

from freezegun import freeze_time

@freeze_time("2012-01-14")
def test_nice_datetime():
    assert datetime.now() == datetime(2012, 1, 14)


@freeze_time("2012-01-14")
class PikaTest(unittest.TestCase):
    def test_generation(self):
        print(datetime.now())

        prefixes = [
            PikaPrefixDefinition(prefix="u", description="User ID"),
            PikaPrefixDefinition(prefix="g", description="Group ID"),
            PikaPrefixDefinition(prefix="c", description="Channel ID"),
        ]
        
        pika = Pika(prefixes)

        self.assertEqual(pika.gen("u"), "u_LTEzMTkwOTE4MzA3ODM5OTk5OTk=")
        self.assertEqual(pika.gen("u"), "u_LTEzMTkwOTE4MzA3ODM5OTk5OTg=")
        self.assertEqual(pika.gen("u"), "u_LTEzMTkwOTE4MzA3ODM5OTk5OTc=")
        
        self.assertEqual(pika.gen("g"), "g_LTEzMTkwOTE4MzA3ODM5OTk5OTY=")
        self.assertEqual(pika.gen("g"), "g_LTEzMTkwOTE4MzA3ODM5OTk5OTU=")
        self.assertEqual(pika.gen("g"), "g_LTEzMTkwOTE4MzA3ODM5OTk5OTQ=")

        self.assertEqual(pika.gen("c"), "c_LTEzMTkwOTE4MzA3ODM5OTk5OTM=")
        self.assertEqual(pika.gen("c"), "c_LTEzMTkwOTE4MzA3ODM5OTk5OTI=")
        self.assertEqual(pika.gen("c"), "c_LTEzMTkwOTE4MzA3ODM5OTk5OTE=")

    def test_validation(self):
        prefixes = [
            PikaPrefixDefinition(prefix="u", description="User ID"),
            PikaPrefixDefinition(prefix="g", description="Group ID"),
        ]
        
        pika = Pika(prefixes)

        self.assertTrue(pika.validate("u_0"))
        self.assertTrue(pika.validate("u_1"))
        self.assertTrue(pika.validate("u_2"))
        
        self.assertTrue(pika.validate("g_0"))
        self.assertTrue(pika.validate("g_1"))
        self.assertTrue(pika.validate("g_2"))

        self.assertFalse(pika.validate("u"))
        self.assertFalse(pika.validate("g"))
        
        self.assertFalse(pika.validate("t_"))
        self.assertFalse(pika.validate("h_"))

        self.assertFalse(pika.validate("t_a"))
        self.assertFalse(pika.validate("h_a"))

        self.assertFalse(pika.validate(""))
