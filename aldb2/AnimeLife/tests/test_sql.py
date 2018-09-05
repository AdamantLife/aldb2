## Framework
import unittest
## Test Target
from aldb2.AnimeLife import sql

## Sister Module
from aldb2 import AnimeLife
from aldb2.Core.sql import util

## Builtin
import json
import pathlib

TESTDATAFILE = (pathlib.Path(__file__).resolve().parent / "testdata.json").resolve()
def gettestdata():
    with open(TESTDATAFILE,'r') as f:
        return json.load(f)

def basicsetup(testcase):
    """ Basic Table Setup for tests
    
        Note that AnimeLife does not use the test values from the Anime App.
    """
    testcase.connection = util.generatedatabase(":memory:")
    for app in ["Core","Anime","AnimeLife"]:
        module,config = util.loadapp(app)
        util.loadtables(module,config,testcase.connection)

    populate_tables(testcase)

def fullsetup(testcase):
    """ Fully populate tables for tests """
    basicsetup(testcase)
    populate_al_weeklyranking(testcase)

def populate_tables(testcase):
    """ Custom test values for this App """
    populate_series(testcase)
    populate_subseries(testcase)
    populate_season(testcase)
    populate_animeseasons(testcase)
    
def populate_series(testcase):
    testdata = gettestdata()
    testcase.connection.executemany("""INSERT INTO series (seriesid,series) VALUES (?,?);""",testdata['setup']['series'])

def populate_subseries(testcase):
    testdata = gettestdata()
    testcase.connection.executemany("""INSERT INTO subseries (subseriesid,series,subseries) VALUES (?,?,?);""",testdata['setup']['subseries'])

def populate_season(testcase):
    testdata = gettestdata()
    testcase.connection.executemany("""INSERT INTO season (seasonid,subseries,season,medium,episodes) VALUES (?,?,?,1,?);""",testdata['setup']['season'])

def populate_animeseasons(testcase):
    testdata = gettestdata()
    testcase.connection.executemany("""INSERT INTO animeseasons (animeseasonid,seasonid,season,year) VALUES (?,?,?,?);""",testdata['setup']['animeseasons'])

def populate_al_weeklyranking(testcase):
    """ Adds test values to the al_weeklyranking table """
    testdata = gettestdata()
    testcase.connection.executemany("""INSERT INTO al_weeklyranking (animeweekid,week,animeseason,episodenumber,rank,hyplistrank,bookmarked) VALUES (?,?,?,?,?,?,?);""",testdata['setup']['weeklyranking'])
    
class Case(unittest.TestCase):
    def setUp(self):
        basicsetup(self)
        return super().setUp()

    def test(self):
        pass


if __name__ == "__main__":
    unittest.main()