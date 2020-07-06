## Test Framework
import unittest
## Module to test
from aldb2 import webmodules
from aldb2.webmodules import sql

## Dependencies
import aldb2.Anime.tests.test_sql as animetests

def setup_database():
    """ Helper function to create a basic database """


class SQL_Test_Setup(unittest.TestCase):
    """ Tests for the SQL module """
    
