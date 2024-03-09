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

class franchiseCase_Base(unittest.TestCase):
    def setUp(self):
        tests.fullsetuptestdatabase(self)
        return super().setUp()

    def test_addfranchise(self):
        """ Simple test to add franchise """
        franchisename = "The Awesome Anime; ザアニメ！"
        aliases = ["The Awesome Anime: The Animation", "Za Waruldo!","My Little Anime Can't Be This Cute"]
        franchiseid = sql.addfranchise(self.connection,franchisename)
        res = self.connection.execute(""" SELECT franchise FROM "franchise" WHERE franchiseid = :franchiseid;""",dict(franchiseid = franchiseid)).fetchall()
        self.assertTrue(res)
        res = res[0]
        self.assertEqual(res[0],franchisename)

    def test_addseries_bad(self):
        """ Simple test to make sure addseries throws errors for non-strings """
        for franchisename in [1234, .0123, True, False, None, tests.RANDOMLAMBDA, tests.RandomObject, tests.RandomObject() ]:
            with self.subTest(franchisename = franchisename):
                self.assertRaises(ValueError,sql.addseries,connection = self.connection, franchisename = franchisename)

class franchiseCase(unittest.TestCase):
    def setUp(self):
        tests.fullsetuptestdatabase(self)
        tests.setupfranchise(self)
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
""" SELECT franchise.franchise
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


if __name__ == "__main__":
    unittest.main()