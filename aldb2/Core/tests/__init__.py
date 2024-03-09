## Test Framework
import unittest
## Module to Test
from aldb2.Core import sql

## Builtin
import datetime
import filecmp
import random
import shutil
import string
import time

## This Module
from aldb2 import filestructure
from aldb2.Core.sql import util
from aldb2.Core.sql import security

################### HELPER FUNCTIONS
""" Miscilaneous Helper Functions """

def getrandomfile(directory = None, extension = "sqlite"):
    """ Helper function to generate random file names that do not already exist """
    if directory is None: directory = filestructure.DATABASEPATH
    file = None
    while not file:
        path = directory / "testdatabase{tempcode}.{extension}".format(tempcode = "".join(random.choices(string.ascii_lowercase,k = 10)),
                                                                                        extension = extension)
        if not path.exists():
            file = path
    return file

def unlinkfile(fileobj):
    """ Helper cleanup function to make sure file is unlinked """
    try:
        fileobj.unlink()
    except FileNotFoundError: pass

def backupgeneralfile(file):
    """ Backs up any given file in it's parent directory and returns the backup's pathlib object (based on backupdatabase). """
    parent = file.parent
    timecode = time.time()
    backup  = parent / f"backup_{timecode}_{file.name}"
    while backup.exists():
        timecode = time.time()
        backup = file.parent / f"backup_{timecode}_{file.name}"
    shutil.copy2(str(file), str(backup))
    if not backup.exists():
        raise FileNotFoundError(f"Failed to backup file")
    filecmp.clear_cache()
    if not filecmp.cmp(str(file),str(backup), shallow = False):
        raise OSError("File backup not identical to original")
    return backup

def restorefile(target,source):
    """ Restores a file at target to backup source and unlinks the backup source if the restoration is successful """
    if not source.exists():
        raise OSError("Backup not accessable for restoration!")
    if target.exists(): target.unlink()
    shutil.copy2(str(source),str(target))
    filecmp.clear_cache()
    if not filecmp.cmp(str(source),str(target), shallow = False):
        raise OSError(f"File backup restoration not identical to original; you may need to restore it yourself:\nTarget Location: {target}\nBackup File: {source}")
    source.unlink()

def closedatabase(database):
    """ Helper function to catch errors when closing (for example, if it was closed manually by the test function) """
    try:
        database.close()
    except:
        pass

def registeruser(connection, userid = 1234567890, username = "Firo Prochainezo", password = "Advena Avis", salt = "1234"):
    """ Helper Function that registers a user into the provided database; returns the information used to register the user as a mapping """
    salt = salt.encode()
    myhash = security.gethash(salt,password.encode())
    inp = dict(userid = userid, username = username, salt = salt, hash = myhash)
    connection.execute("""INSERT INTO \"users\" (userid, name, salt, hash) VALUES (:userid, :username, :salt, :hash);""", inp)
    inp["password"] = password
    return inp


################# TEST SETUPS
""" Common setup sequences """

def backupconfig(testcase):
    """ Backs up the config file, and sets a Cleanup method to restore the original """
    ## Make sure that config actually exists before testing
    util.getconfig()
    ## Backups
    testcase.configfile = util.getconfigfilepath()
    testcase.assertTrue(testcase.configfile.exists())
    testcase.backup = backupgeneralfile(testcase.configfile)
    testcase.addCleanup(restorefile,testcase.configfile,testcase.backup)
    testcase.config = util.getconfig()

def setuptestfile(testcase):
    """ Creates a new database file """
    testcase.testfile = getrandomfile()
    testcase.testfile.touch()
    testcase.addCleanup(unlinkfile,testcase.testfile)

def connecttesttable(testcase):
    """ Creates and Connects a blank test database """
    ## Note that repeating this should not cause any issues as
    ## Cleanup does not require the attribute
    setuptestfile(testcase)
    testcase.connection = util.connectdatabase(testcase.testfile.name)
    testcase.addCleanup(closedatabase,testcase.connection)

def createtesttable(testcase):
    """ Creates a basic, valid database """
    testcase.testfile = getrandomfile()
    util.createdatabase(testcase.testfile)
    testcase.connection = util.connectdatabase(testcase.testfile)
    testcase.addCleanup(unlinkfile,testcase.testfile)
    testcase.addCleanup(closedatabase,testcase.connection)

def setuptestuser(testcase, connection):
    """ Creates a user using registeruser's defaults. Requires the desired connection object. """
    testcase.testuserinfo = registeruser(connection)

def fullsetuptestdatabase(testcase):
    """ Fully sets up a test database with TestApp installed for the testuser """
    createtesttable(testcase)
    testcase.appname = "TestApp"
    setuptestuser(testcase,testcase.connection)
    testcase.appmodule, testcase.appconfig = sql.installapp(testcase.connection, testcase.appname)
    installinfo = sql.getappbyname(testcase.connection, testcase.appname)
    sql.registeruserapp(testcase.connection,installinfo['installid'],testcase.testuserinfo['userid'])

def setupfranchise(testcase):
    """ Inserts default franchise into the database, settings a dict of id:name as self.franchise """
    testcase.franchise = dict()
    for ser in ["The Awesome Anime; ザアニメ！", "GSS: Generic Shounen Show", "This Show is as Chuuni as My Dark Soul","This Season's Idol Show"]:
        sid = sql.addfranchise(testcase.connection, ser)
        testcase.franchise[sid] = ser

def memory_setuptestdatabase(testcase):
    """ Sets up a new database in-memory, loading the Core App into it.

        fullsetuptestdatabase creates a "physical" database on the disk which is useful
        for a few tests that it runs; for other tests, however, this is overkill so this
        method is available for implementing a prepopulated database containing the Core App.
    """
    testcase.connection = conn = util.generatedatabase(":memory:")
    populate_all(testcase)

def populate_all(testcase):
    """ Populates all tables in the Core App with values. """
    conn = testcase.connection
    setuptestuser(testcase,conn)
    setuptestusersession(testcase)
    setupfranchise(testcase)
    setupseries(testcase)
    setupseries_aliases(testcase)
    setupsubseries_aliases(testcase)
    setupsubseries_genrelist(testcase)

def setuptestusersession(testcase):
    """ Populates the sessions table """
    testcase.connection.execute("""INSERT INTO sessions (userid,authtoken,authtime) VALUES
(:userid,:token1,:time1),
(:userid,:token2,:time2);""",dict(
    userid = 1234567890,
    token1 = "lvm7xBme-WyBZ1pwKM4mFmmHNd2BeVzciEz_wWWt86g",
    time1 = datetime.datetime(1,1,1,0,0,0),
    token2 = "WfWv6LuKaMxIv3MSapyBTUra4srs8I6--7sBwNk9fSk",
    time2 = datetime.datetime.now()
    ))
    
def setupseries(testcase):
    """ Populates the series Table. """
    for franchise,series in [(0,None),(1,"First franchise"),(2,None),(2,"Ura"), (4,None),]:
        sql.addseries(testcase.connection,franchise,series)

def setupseries_aliases(testcase):
    for franchisealias,franchise,language in [("GSS",1,"enlish"),("その名前は偽物だ！",2,"japanese"),("バカメ",1,"japanese")]:
        sql.addseriesalias(testcase.connection, franchiseid = franchise, franchisealias = franchisealias, language = language)

def setupsubseries_aliases(testcase):
    for seriesalias,series,language in [("franchise The First",1,"japanese"),("あたしは天使だよ！ペロ:P",2,"japanese")]:
        sql.addsubseriesalias(testcase.connection, seriesid = series, seriesalias = seriesalias, language = language)

def setupsubseries_genrelist(testcase):
    for series,genres in [(0,(13,5,4)),
                             (1,(22,)),
                             (2,(3,2,17)),
                             (3,(12,28,24)),
                             (4,(10,))]:
        sql.addsubseriesgenres(testcase.connection,series,*genres)

################# OTHER RESOURCES
""" Miscellaneous resources for testing """

class RandomObject():
    """ A Random Object class """
    def __init__(self,*args, **kw): pass
    def __callable__(self,*args,**kw): pass
    def __enter__(self): return self
    def __exit__(self): pass

RANDOMLAMBDA = lambda *args, **kw: 0

if __name__ == "__main__":
    import unittest
    import pathlib
    path = pathlib.Path.cwd().parent.parent
    tests = unittest.TestLoader().discover(path)
    #print(tests)
    unittest.TextTestRunner().run(tests)