## Testing Framework
import unittest
from aldb2.Core import tests
## Module to test
from aldb2.Core import sql

## Builtin
import json
import sqlite3

## This Module
from aldb2 import filestructure
from aldb2.Core import core
from aldb2.Core.sql import util

class BaseCase(unittest.TestCase):

    def setUp(self):
        tests.createtesttable(self)
        return super().setUp()
    
    def test_getinstalledapps(self):
        """ Tests that getinstalledapps retuns no Apps """
        apps = sql.getinstalledapps(self.connection)
        self.assertFalse(apps)

    def test_core_genresloaded(self):
        """ Tests that the genres table is prepopulated with the base genre info """
        genrefile = (filestructure.PROGRAMPATH / "Core/sql/genres.json").resolve()
        self.assertTrue(genrefile.exists())
        with open(genrefile,'r') as f:
            genres = json.load(f)
        dbgenres = sql.getgenres(self.connection)
        for genre in dbgenres: genre.pop("genreid")
        self.assertEqual(genres,dbgenres)

    def test_core_getgenrebyname(self):
        """ Tests hat getgenrebyname returns every default genre with the correct stats """
        genrefile = (filestructure.PROGRAMPATH / "Core/sql/genres.json").resolve()
        self.assertTrue(genrefile.exists())
        with open(genrefile,'r') as f:
            genres = json.load(f)
        for genre in genres:
            with self.subTest(genre=genre):
                dbgenre = sql.getgenrebyname(self.connection,genre['name'])
                dbgenre.pop("genreid")
                self.assertEqual(dbgenre,genre)

    def test_core_getgenrebyabbreviation(self):
        """ Tests hat getgenrebyabbreviation returns every default genre with the correct stats """
        genrefile = (filestructure.PROGRAMPATH / "Core/sql/genres.json").resolve()
        self.assertTrue(genrefile.exists())
        with open(genrefile,'r') as f:
            genres = json.load(f)
        for genre in genres:
            with self.subTest(genre=genre):
                dbgenre = sql.getgenrebyabbreviation(self.connection,genre['abbreviation'])
                dbgenre.pop("genreid")
                self.assertEqual(dbgenre,genre)

    def test_core_yearseasonsloaded(self):
        """ Tests that the yearseasons table is prepopulated with the all the seasons with the correct indices """
        dbseasons = sql.getseasons(self.connection)
        self.assertEqual(dbseasons,["Winter","Spring","Summer","Fall"])

class UserBaseCase(unittest.TestCase):
    def setUp(self):
        tests.createtesttable(self)
        tests.setuptestuser(self,self.connection)
        return super().setUp()

    def testgetuserapps(self):
        """ Tests that getuserapps returns no apps """
        apps = sql.getuserapps(self.connection, self.testuserinfo['userid'])
        self.assertFalse(apps)


class AppsCase(unittest.TestCase):
    def setUp(self):
        tests.fullsetuptestdatabase(self)
        return super().setUp()

    def test_installapp(self):
        """ Tests that TestApp was successfully installed and populated """
        apps = sql.getinstalledapps(self.connection)
        self.assertTrue({"app":self.appname,"version":"1.5.6"} in apps)
        tablecheck = util.checktables(self.connection,self.appconfig)
        self.assertTrue(tablecheck.version)
        self.assertEqual(tablecheck.missing,[])
        self.assertEqual(tablecheck.different,[])
        self.assertEqual(len(tablecheck.passed),len(self.appconfig['tables']))
        t1rows = self.connection.execute("""SELECT * FROM \"test_table\";""").fetchall()
        t2rows = self.connection.execute("""SELECT * FROM \"test_table_2\";""").fetchall()
        self.assertEqual(len(t1rows),2)
        self.assertEqual(len(t2rows),1)
        self.assertEqual(t1rows[0],(1,"Hello",1.0))
        self.assertEqual(t1rows[1],(2,"World",2))
        self.assertEqual(t2rows[0],(1,1,"Foobar"))

    def test_getappname(self):
        """ Tests getappbyname """
        appinfo = sql.getappbyname(self.connection,self.appname)
        self.assertEqual(self.appconfig['appname'],appinfo['module'])
        self.assertEqual(self.appconfig['version'],appinfo['version'])

    def test_registerapp(self):
        """ Tests that the TestApp was successfully registered for the created user """
        apps = sql.getuserapps(self.connection,self.testuserinfo['userid'])
        self.assertTrue(self.appname in [app['app'] for app in apps])

class SeriesCase_Base(unittest.TestCase):
    def setUp(self):
        tests.fullsetuptestdatabase(self)
        return super().setUp()

    def test_addseries(self):
        """ Simple test to add series """
        seriesname = "The Awesome Anime; ザアニメ！"
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        seriesid = sql.addseries(self.connection,seriesname)
        res = self.connection.execute(""" SELECT series FROM "series" WHERE seriesid = :seriesid;""",dict(seriesid = seriesid)).fetchall()
        self.assertTrue(res)
        res = res[0]
        self.assertEqual(res[0],seriesname)

    def test_addseries_bad(self):
        """ Simple test to make sure addseries throws errors for non-strings """
        for seriesname in [1234, .0123, True, False, None, tests.RANDOMLAMBDA, tests.RandomObject, tests.RandomObject() ]:
            with self.subTest(seriesname = seriesname):
                self.assertRaises(ValueError,sql.addseries,connection = self.connection, seriesname = seriesname)

class SeriesCase(unittest.TestCase):
    def setUp(self):
        tests.fullsetuptestdatabase(self)
        tests.setupseries(self)
        return super().setUp()

    def test_getseries(self):
        """ Tests that getseries returns all preloaded series """
        for seriesid, series in self.series.items():
            with self.subTest(seriesid = seriesid, series = series):
                result = sql.getseries(self.connection,series)
                self.assertEqual(seriesid, result[0].seriesid)

    def test_getserieslike(self):
        """ Tests that getserieslike returns accurate queries for exact, case-insensitive, and partial matches """
        seriesid = 1
        seriesname = self.series[seriesid]
        series = core.Series(seriesid,seriesname)
        for sname in [seriesname, seriesname.upper(), seriesname[2:-2]]:
            with self.subTest(sname = sname):
                result = sql.getserieslike(self.connection, seriesname)
                self.assertEqual(len(result),1)
                result = result[0]
                self.assertEqual(result.seriesid,series.seriesid)

    def test_addseriesalias(self):
        """ Test to ensure that aliases can be added for series """
        seriesid = 1
        seriesname = self.series[seriesid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for alias in aliases:
            sql.addseriesalias(self.connection, seriesid, alias)
        for alias in aliases:
            with self.subTest(alias = alias):
                sname = self.connection.execute(
""" SELECT series.series
FROM "series"
LEFT JOIN "aliases_series" ON "series".seriesid = "aliases_series".series
WHERE seriesalias = :seriesalias;""",
dict(seriesalias = alias)).fetchone()
                self.assertEqual(seriesname,sname[0])

    def test_addseriesalias_multiple(self):
        """ Test to ensure that aliases can be added for series more than once and doing so does not raise an Error """
        seriesid = 1
        seriesname = self.series[seriesid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for cpy in range(3):
            for alias in aliases:
                sql.addseriesalias(self.connection, seriesid, alias)
        als = sql.getaliasesforseries(self.connection, seriesid)
        self.assertEqual(len(aliases),len(als))

    def test_addseriesalias_bad(self):
        """ Simple test to make sure addseriesalias throws errors for non-strings as seriesalias """
        seriesid = 1
        for seriesalias in [1234, .0123, True, False, None, tests.RANDOMLAMBDA, tests.RandomObject, tests.RandomObject() ]:
            with self.subTest(seriesalias = seriesalias):
                self.assertRaises(ValueError,sql.addseriesalias,connection = self.connection, seriesid = seriesid, seriesalias = seriesalias)

    def test_getaliasesforseries(self):
        """ Tests that aliases can be fetched by seriesid """
        seriesid = 1
        seriesname = self.series[seriesid]
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        for alias in aliases:
            sql.addseriesalias(self.connection, seriesid, alias)
        als = sql.getaliasesforseries(self.connection, seriesid)
        self.assertEqual(len(als),len(aliases))
        aliasnames = [name for id,name in als]
        self.assertTrue(all(alias in aliasnames for alias in aliases))
        self.assertTrue(all(alias in aliases for alias in aliasnames))


if __name__ == "__main__":
    unittest.main()