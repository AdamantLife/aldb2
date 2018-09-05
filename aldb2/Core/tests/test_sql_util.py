## Modules to test
from aldb2.Core.sql import util
## Testing Module
import unittest

## Builtin
import hashlib
import filecmp
import json
import pathlib
import sqlite3
## This Module
from aldb2 import filestructure
from aldb2.Core import tests

def hashfile(file, chunksize = 4096):
    """ Helper function to compare files """
    hasher = hashlib.sha256()
    with open(file,'rb') as f:
        for chunk in iter(lambda: f.read(chunksize),b""):
            hasher.update(chunk)
    return hasher.hexdigest()

########### SUBCLASSING METHODS
"""
Subclassing doesn't work well with unittest (all subclasses inherit all test methods as well :-/)
so, we need basic setup methods that can be inherited instead
"""

def setupcorerun(testcase):
    """ Makes sure that the config file and default database are available and assigns them as attributes """
    testcase.config = util.getconfig()
    testcase.defaultconnection = util.getdefaultdatabase(testcase.config, create = True)
    testcase.addCleanup(tests.closedatabase,testcase.defaultconnection)

############# Unit Tests

class ConfigCase(unittest.TestCase):
    """ System Configuration File related Tests """

    def setUp(self):
        tests.backupconfig(self)
        return super().setUp()
    
    def test_getconfig(self):
        """ Asserts that getconfig returns the same file that is at getconfigfilepath """
        with open(util.getconfigfilepath(),'r') as f:
            config2 = json.load(f)
        self.assertEqual(config2,util.getconfig())

class NoConfigCase(unittest.TestCase):
    """ Wipes the config file (was backed up in ConfigCase)"""

    def setUp(self):
        tests.backupconfig(self)
        self.configfile.unlink()
        return super().setUp()

    def test_getconfig_missing(self):
        """ Asserts that getconfig returns a config file matching basicconfig by default when
        the System Configuration File is missing
        """
        config2 = util.basicconfig()
        self.assertEqual(config2,util.getconfig())

    def test_getconfig_missing_nocreate(self):
        """ Tests that getconfig raises a FileNotFoundError when create is false and the file is missing """
        self.assertRaisesRegex(FileNotFoundError,"System Configuration File does not exist!",util.getconfig,create = False)


class NewConfigCase(unittest.TestCase):
    """ Replaces the config file with a fresh one (was backed up in ConfigCase) """

    def setUp(self):
        tests.backupconfig(self)
        self.configfile.unlink()
        self.config = util.getconfig()
        return super().setUp()

    def test_updatedatabaseaccess(self):
        """ Tests that databases are properly preserved via updatedatabaseaccess in order """
        util.updatedatabaseaccess(self.config,"db1.sqlite")
        util.updatedatabaseaccess(self.config,"db2.sqlite")
        util.updatedatabaseaccess(self.config,"db1.sqlite")
        util.updatedatabaseaccess(self.config,"db3.sqlite")
        ## Should have 3 databases (each database name is unique, so db1 appears only onces)
        self.assertEqual(len(self.config['databases']),3)
        ##  Order should be LIFO
        dbnames = [db['name'] for db in self.config['databases']]
        self.assertEqual(dbnames,["db3.sqlite","db1.sqlite","db2.sqlite"])
        ## Timestamps should also be in order (reversed, since LIFO)
        dbtimestamps = [db['recent'] for db in self.config['databases']]
        self.assertEqual(dbtimestamps,sorted(dbtimestamps,reverse=True))

class GeneralDatabase(unittest.TestCase):
    """ Tests general-utility Database Functions """
    def setUp(self):
        tests.setuptestfile(self)
        tests.backupconfig(self)
        return super().setUp()

    def test_backupdatabase(self):
        """ Tests that backupdatabase properly backs up a database """
        with open(self.testfile,'w') as f:
            f.write("hello world")
        myhash = hashfile(self.testfile)
        backup = util.backupdatabase(self.testfile.name)
        self.assertTrue(isinstance(backup,pathlib.Path))
        self.assertEqual(hashfile(backup),myhash)
        ## backupdatabase do these tests iteslf
        self.assertTrue(backup.exists())
        filecmp.clear_cache()
        self.assertTrue(filecmp.cmp(str(self.testfile),str(backup), shallow = False))

    def test_connectdatabase(self):
        """ Checks that connectdatabase correctly returns an sqlite3 connection object """
        conn = util.connectdatabase(self.testfile.name)
        self.assertTrue(isinstance(conn,sqlite3.Connection))


class NoDatabase(unittest.TestCase):
    """ Tests functions that deal with no database """

    def setUp(self):
        tests.setuptestfile(self)
        tests.backupconfig(self)
        setupcorerun(self)
        return super().setUp()

    def test_getdefaultdatabase(self):
        """ Tests that getdefaultdatabase creates a new database if default database is missing """
        self.defaultconnection.close()
        backup = util.backupdatabase(util.DEFAULTDATABASE.name)
        self.addCleanup(tests.restorefile,util.DEFAULTDATABASE,backup)
        util.DEFAULTDATABASE.unlink()
        db = util.getdefaultdatabase(self.config, create = True)
        self.assertTrue(isinstance(db,sqlite3.Connection))
        self.assertTrue(self.config['databases'][0]['name'] == "aldb.sqlite")


class SetupNewDatabase(unittest.TestCase):
    """ Does Core Setup of a brand new Database """
    def setUp(self):
        tests.backupconfig(self)
        tests.connecttesttable(self)
        return super().setUp()

    def test_createdatabase(self):
        """ Tests that createdatabase creates a new file in the database directory and returns True """
        self.connection.close()
        self.testfile.unlink()
        self.assertFalse(self.testfile.exists())
        self.assertTrue(util.createdatabase(self.testfile.name))
        self.assertTrue(self.testfile.exists())

    def test_createdatabase_nooverwrite(self):
        """ Tests that createdatabase does not overwrite existing files by default """
        self.assertRaisesRegex(FileExistsError,"Database already exists!",util.createdatabase,self.testfile.name)

    def test_createdatabase_overwrite(self):
        """ Tests that createdatabase will backup before overwriting existing files and return the backup file """
        self.connection.close()
        with open(self.testfile,'w') as f:
            f.write("hello world")
        myhash = hashfile(self.testfile)
        backup = util.createdatabase(self.testfile.name, overwrite = True)
        self.assertTrue(isinstance(backup,pathlib.Path))
        self.assertTrue(backup.exists())
        self.addCleanup(tests.unlinkfile,backup)
        self.assertEqual(hashfile(backup),myhash)
        self.assertNotEqual(hashfile(self.testfile),myhash)

    def test_loadcoretables(self):
        """ Tests that createdatabase successfully creates the Core tables """
        util.loadcoretables(self.connection)
        tablenames = util.getdatabasetables(self.connection)
        basetables = {table['name']:table['sql'] for table in util.coreconfig()['tables']}
        self.assertDictEqual(tablenames,basetables)

    def test_checktables_allmissing(self):
        """ Tests that a brand new database results in all Core tables being missing """
        result = util.checktables(self.connection,util.coreconfig())
        self.assertEqual(result.version,None)
        self.assertEqual(len(result.different),0)
        self.assertEqual(len(result.passed),0)
        coretables = util.coreconfig()['tables']
        self.assertEqual(len(result.missing),len(coretables))

class LoadDatabaseCase(unittest.TestCase):
    """ Tests for loading an existing database """
    def setUp(self):
        tests.memory_setuptestdatabase(self)
    def test_main_good(self):
        """ Tests the main (loading) function when the database is valid """
        util.main(self.connection)
    def test_loadtables_good(self):
        """ Tests that laodtables functions properly """
        ## TODO: Need to figure out how to isolate and imitate a bare 
        
    
if __name__ == "__main__":
    unittest.main()