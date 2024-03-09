## Builtin
import unittest
## Tested Module
from aldb2.Anime import sql

## Sister Module
from aldb2.Core import tests
from aldb2.Core.sql import util

## Builtin 
import datetime

def basesetup(testcase):
    """ Helper function to setup the basic requirements for this module.

        Runs Core.tests.fullsetuptestdatabase
    """
    tests.memory_setuptestdatabase(testcase)
    module,config = util.loadapp("Anime")
    util.loadtables(module,config,testcase.connection)

def fullsetup(testcase):
    """ Does the basic database setup as well as populating Anime-module tables with sample data. """
    basesetup(testcase)
    populate_all(testcase)

def populate_all(testcase):
    """ Populates all Anime-Module tables with test values """
    populate_season(testcase)
    populate_aliases_season(testcase)
    populate_genrelist_season(testcase)
    populate_animeseasons(testcase)

def populate_season(testcase):
    """ Populates the Season table with test values """
    for seasonid, series, season, medium, episodes in [
        (0  , 0 , None                  , 1 , 13),
        (1  , 1 , "Season the First~"   , 1 , 12),
        (2  , 2 , "X"                   , 1 , 24),
        (3  , 3 , None                  , 3 , 1),
        (4  , 1 , "Season! Zwei!"       , 1 , 12),
        (5  , 4 , None                  , 1 , 14),]:
        testcase.connection.execute(""" INSERT INTO season (seasonid,series,season,medium,episodes) VALUES (
        :seasonid, :series, :season, :medium, :episodes
        );""", dict(seasonid = seasonid, series = series, season = season, medium = medium, episodes = episodes))

def populate_aliases_season(testcase):
    """ Populates the sesaon_alieases table with test values """
    for seasonaliasid, seasonalias, season, language in [
        (0  , "First Season"                    , 1 ,"English"),
        (1  , "Season 1"                        , 1 , "English"),
        (2  , "Hissatasu Waza: First Season!"   , 1 , "English"),
        (3  , "Cross"                           , 2 , "Romaji")]:
        testcase.connection.execute("""INSERT INTO aliases_season (seasonaliasid,seasonalias,season,language) VALUES (
        :seasonaliasid, :seasonalias, :season, :language
        );""", dict(seasonaliasid = seasonaliasid, seasonalias = seasonalias, season = season, language = language))

def populate_genrelist_season(testcase):
    """ Populates the genrelist_season table with test values """
    for genrelistid, genre, season in [
        (0, 1 , 4),
        (1, 5 , 4),
        (2, 28, 4)
        ]:
        testcase.connection.execute("""INSERT INTO genrelist_season (genrelistid, genre, season) VALUES (
        :genrelist, :genre, :season
        );""", dict(genrelist = genrelistid, genre = genre, season = season))

def populate_animeseasons(testcase):
    """ Populates the animeseasons table with test values """
    for animeseasonid, seasonid, season, year in [
        (0, 0, 1, 2000),
        (1, 1, 2, 2000),
        (2, 2, 3, 2000),
        (3, 2, 0, 2001),
        (4, 3, 0, 2002),
        (5, 4, 2, 2003),
        (6, 5, 2, 2003),]:
        testcase.connection.execute("""INSERT INTO animeseasons (animeseasonid, seasonid, season, year) VALUES(
        :animeseasonid, :seasonid, :season, :year
        );""", dict(animeseasonid = animeseasonid, seasonid = seasonid, season = season, year = year))

def populate_simialr_anime(testcase):
    """ Populates the similar_anime table with test values """
    for similarid, season1, season2 in [
        (0, 0, 4),]:
        testcase.connection.execute("""INSERT INTO similar_anime (similarid, season1, season2) VALUES (
        :similarid, :season1, :season2
        );""", dict(similarid = similarid, season1 = season1, season2 = season2))

def populate_airinginfo(testcase):
    """ Populates the airinginfo table with test values """
    for airinginfoid, animeseason, firstepisode, time in [
        (0, 0, datetime.date(2000,4,1), datetime.time(16,0,0)),
        (1, 1, datetime.date(2000,6,11), datetime.time(12,30,0)),
        (2, 2, datetime.date(2000,8,31), datetime.time(0,0,0)),
        (3, 3, datetime.date(2001,1,1), datetime.time(0,0,0)),
        (4, 4, datetime.date(2002,1,16), datetime.time(1,0,0)),
        (5, 5, datetime.date(2003,6,1), datetime.time(12,30,0)),
        ]:
        testcase.connection.execute("""INSERT INTO airinginfo (airinginfoid, animeseason, firstepisode, time) VALUES (
        :airinginfoid, :animeseason, :firstepisode, :time
        );""",dict(airinginfoid = airinginfoid, animeseason = animeseason, firstepisode = firstepisode, time = time))

class SeasonCase_Base(unittest.TestCase):
    def setUp(self):
        basesetup(self)
        return super().setUp()

    def test_addseason(self):
        """ Simple test to add season """
        seasonname = "Season the First~"
        aliases = ["First Season","Season 1", "Hissatsu Waza: First Season!"]
        seasonid = sql.addseason(self.connection,seasonname, 1, 1)
        res = self.connection.execute(""" SELECT season FROM "franchise" WHERE franchiseid = :franchiseid;""",dict(franchiseid = franchiseid)).fetchall()
        self.assertTrue(res)
        res = res[0]
        self.assertEqual(res[0],franchisename)

class franchiseCase(unittest.TestCase):
    def setUp(self):
        basesetup(self)
        return super().setUp()

    def test_getfranchise(self):
        """ Tests that getseries returns all preloaded franchise """
        for franchiseid, franchise in self.franchise.items():
            with self.subTest(franchiseid = franchiseid, franchise = franchise):
                result = sql.getfranchise(self.connection,franchise)
                self.assertEqual(franchiseid, result[0].franchiseid)

    def test_getserieslike(self):
        """ Tests that getserieslike returns accurate queries for exact, case-insensitive, and partial matches """
        franchiseid = 1
        franchisename = self.franchise[franchiseid]
        franchise = core.franchise(franchiseid,franchisename)
        for sname in [franchisename, franchisename.upper(), franchisename[2:-2]]:
            with self.subTest(sname = sname):
                result = sql.getserieslike(self.connection, franchisename)
                self.assertEqual(len(result),1)
                result = result[0]
                self.assertEqual(result.franchiseid,franchise.franchiseid)

    def test_addseriesalias(self):
        """ Test to ensure that aliases can be added for franchise """
        franchiseid = 1
        franchisename = self.franchise[franchiseid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for alias in aliases:
            sql.addseriesalias(self.connection, franchiseid, alias)
        for alias in aliases:
            with self.subTest(alias = alias):
                sname = self.connection.execute(
""" SELECT franchise
FROM "franchise"
LEFT JOIN "aliases_series" ON "franchise".franchiseid = "aliases_series".franchise
WHERE franchisealias = :franchisealias;""",
dict(franchisealias = alias)).fetchone()
                self.assertEqual(franchisename,sname[0])

    def test_addseriesalias_multiple(self):
        """ Test to ensure that aliases can be added for franchise more than once and doing so does not raise an Error """
        franchiseid = 1
        franchisename = self.franchise[franchiseid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for cpy in range(3):
            for alias in aliases:
                sql.addseriesalias(self.connection, franchiseid, alias)
        als = sql.getaliasesforfranchise(self.connection, franchiseid)
        self.assertEqual(len(aliases),len(als))

    def test_addseriesalias_bad(self):
        """ Simple test to make sure addseriesalias throws errors for non-strings as franchisealias """
        franchiseid = 1
        for franchisealias in [1234, .0123, True, False, None, tests.RANDOMLAMBDA, tests.RandomObject, tests.RandomObject() ]:
            with self.subTest(franchisealias = franchisealias):
                self.assertRaises(ValueError,sql.addseriesalias,connection = self.connection, franchiseid = franchiseid, franchisealias = franchisealias)

    def test_getaliasesforfranchise(self):
        """ Tests that aliases can be fetched by franchiseid """
        franchiseid = 1
        franchisename = self.franchise[franchiseid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for alias in aliases:
            sql.addseriesalias(self.connection, franchiseid, alias)
        als = sql.getaliasesforfranchise(self.connection, franchiseid)
        self.assertEqual(len(als),len(aliases))
        aliasnames = [name for id,name in als]
        self.assertTrue(all(alias in aliasnames for alias in aliases))
        self.assertTrue(all(alias in aliases for alias in aliasnames))



if __name__ == '__main__':
    unittest.main()
