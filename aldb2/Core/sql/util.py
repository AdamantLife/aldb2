## Builtin
import collections
import filecmp
import functools
import importlib
import json
import pathlib
import re
import shutil
import sqlite3
import time
## This Module
from aldb2 import filestructure
from aldb2.Core import sql as Core

""" CORE SQL FUNCTIONS


This module defines the core sql tables as well as a series of functions to help maintain the tables in the database.

When creating an sql module for use with this aldb2, the module should contain separate json file named "sql.json"
which configures the module's datbase tables and settings. It should have the following keys:
    "version"- the version of the app
    "tables"- a list of mappings, keys:
        "name"- the table name as it is will appear in the database.
        "sql"- the "CREATE TABLE" statement used to create the table.
        "setup" (Optional)- a mapping of table names with keys as lists representing a number of methods necessary
                            to setup the table (i.e.- prepopulate it with default values).
        "updates" (Optional)- a mapping of previous version numbers paired with a list of method names
                  that can be used to upgrade to the current version. Previous version numbers can use * wildcards
                  to include minor versions (i.e.- 2.*.* would provide an upgrade path from any subversion of major
                  version 2 to the current version.
    "views"- a list of mappings with the same keys as "tables" (except concerning views).
        

All configuration files must run the compatibletables function successfully (this will be done automatically when the app is loaded by
Core.sql's setupapps function).
"""

DEFAULTDATABASE = filestructure.DATABASEPATH / "aldb.sqlite"

class IntegrityError(Exception): pass

def row_factory_saver(function):
    """ A decorator to capture the connection's row_factory, clear it before the function, and safely restore it afterwards """
    @functools.wraps(function)
    def inner(connection,*args,**kw):
        rowfactory = connection.row_factory
        try:
            connection.row_factory = None
            return function(connection,*args,**kw)
        finally:
            connection.row_factory = rowfactory
    return inner

################## Extension Functions
def loadsqljson(file,filename = "sql.json"):
    """ Loads sql configuratoin json; file should be the module's __file__ attribute. 
    
    By default, assumes that the sql file is located in the module's root directory and is named
    "sql.json;" to change this behavoir supply filename as a string relative to the module's root directory.
    """
    path = pathlib.Path(file).resolve()
    parent = path.parent
    definitions = (parent / filename).resolve()
    try:
        definitions.relative_to(parent)
    except:
        raise ValueError("sql configuration file must be located relative to the module's root file!")
    with open(definitions,'r') as f:
        data = json.load(f)
    return data

def compatibletables(configuration):
    """ A test-function to run to ensure that all VALIDTABLES work with the helper functions of this module
   
    Failure will raise an Exception.
    """
    validtables = configuration['tables']
    for table in validtables:
        if not table.get("name"): raise ValueError(f"Missing Table Name for table: {table}")
        if not table.get("sql"): raise ValueError(f"Missing Table SQL for table: {table}")
        if not table.get("version"): raise ValueError(f"Missing Table Version for table: {table}")

def setuptable(configuration, connection, table):
    """ Executes the table creation sql provided (must be sql provided by this library) """
    validtables = configuration['tables']
    if table not in validtables: raise ValueError("setuptable can only execute CREATE TABLE statements from this library.")
    return connection.execute(table['sql'])

CheckTableResults = collections.namedtuple("tablevalidation","version, missing, different, passed")
@row_factory_saver
def checktables(connection,configuration): ## Tested- SetupNewDatabase,
    """ Checks that all tables are present and in the form specified by the factory.

    Retuns a "tablevalidation" namedtuple with the following attributes:
    * version: True if the registered app's version matches the configuration file supplied. If it differs,
                version will be False. If the app's registration cannot be located, version will be None.
    * missing: table configurations whose name is not in the database;
    * different: table configurations whose creation sql differs from what is in the database
    * passed: table configurations that are correctly implemented.

    All values will be None if checktables fails to execute properly.
    Most often a app version mismatch will result in tables being listed in "different"; when properly defined,
    the configuration file can be used to safely update the "different" tables so that they match. If the
    configuration file does not provide a way to upgrade from the current version of the table to the new version,
    it will be necessary to procure other tools or otherwise update the table manually.
    """
    version,missing,different,passed = None,list(),list(),list()
    try:
        connection.row_factory = None
        try: ver = connection.execute("""SELECT version FROM "installed_apps" WHERE module = :appname;""",dict(appname=configuration['appname'])).fetchone()
        except: ver = None
        if not ver: version = None
        elif ver[0] != configuration['version']: version = False
        else: version = True
        dbtables = getdatabasetables(connection)
        for table in configuration['tables']:
            if table['name'] not in dbtables: missing.append(table)
            elif dbtables[table['name']] != table['sql']:
                different.append(table)
            else: passed.append(table)
    except Exception as e:
        return CheckTableResults(None,[],[],[])
    return CheckTableResults(version,missing,different,passed)

############### DATABASE FILE MANAGEMENT

def createdatabase(filename,overwrite = False): ## Tested- SetupNewDatabase
    """ Creates a new database in DATABASEPATH; apps should be installed separately.
    
    Raises a FileExists error if the file exists and overwrite is False (default); otherwise, if overwrite is True,
    will create a backup of the existing database and then replace it
    """
    backup = True
    filename = (filestructure.DATABASEPATH / filename).resolve()
    if filename.exists() and not overwrite is True:
        raise FileExistsError("Database already exists!")
    elif overwrite is True:
        backup = backupdatabase(filename.name)
        filename.unlink()
    filename.touch()
    conn = generatedatabase(filename)
    conn.close()
    return backup

def generatedatabase(filename):
    """ Attempts to setup up a new database (create all necessary tables) in the given file.
   
        Returns the connection (for use with :memory:)
    """
    conn = connectdatabase(filename)
    loadcoretables(conn)
    return conn

def updatedatabaseaccess(configuration, filename): ## Tested- NewConfigCase
    """ Updates the Configuration[databases] with the database and it's timestamp """
    dbs = configuration['databases']
    names = [db['name'] for db in dbs]
    if filename in names: dbs.pop(names.index(filename))
    dbs.insert(0,dict(name = filename, recent=time.time()))

def backupdatabase(filename): ## Tested- GeneralDatabase
    """ Creates a duplicate of the file named "backup{timecode}_{filename} and checks that the backup is identical. Returns the backup's filepath as a pathlib.Path instance. """
    dbfile = (filestructure.DATABASEPATH / filename).resolve()
    if not dbfile.exists():
        raise ValueError("File does not exist in the database directory.")
    timecode = time.time()
    backup  = dbfile.parent / f"backup_{timecode}_{filename}"
    while backup.exists():
        timecode = time.time()
        backup = dbfile.parent / f"backup_{timecode}_{dbfile.name}"
    shutil.copy2(str(dbfile), str(backup))
    if not backup.exists():
        raise FileNotFoundError(f"Failed to backup database")
    filecmp.clear_cache()
    if not filecmp.cmp(str(dbfile),str(backup), shallow = False):
        raise OSError("Database backup not identical to original")
    return backup

def connectdatabase(db): ## Tested- SetupNewDatabase
    """ The general connection method for databases. Takes the database's file name. """
    try:
        ## Allowing :memory: is an undocumented feature at the moment 
        ## as it seems best to remain as a dev-only usage
        if db != ":memory:":
            db = filestructure.DATABASEPATH / db
            db.resolve()
            assert db.exists()
        conn = sqlite3.connect(str(db))
    except Exception as e:
        raise FileNotFoundError(f"Could not open Database: {str(e)}")
    else:
        return conn

def getdefaultdatabase(configuration = None, create = False): ## Partially Tested- NoDatabase
    """ Returns a connection object for the default database.
    
    If create is True, will create the default database if it does not exist.
    Raises FileNotFound error if database cannot be connected to for any reason.
    """
    try:
        db = filestructure.DATABASEPATH / "aldb.sqlite"
        if not db.exists() and create:
            if not db.parent.exists():
                db.mkdir(parents=True,exist_ok = True)
            db.touch()
        db.resolve()
        conn = connectdatabase(db.name)
    except Exception as e:
        raise FileNotFoundError(f"Could not open default database: {str(e)}")
    else:
        if configuration is not None:
            updatedatabaseaccess(configuration, db.name)
        return conn

def getanydatabase(configuration):
    """ Returns the first functional database's connection object based on the configuration file's database history, or the defaultdatabase if no valid databases available.
   
    If no valid databases are available and the defaultdatabase cannot be created, a FileNotFound error will be raised.
    """
    dbs = getdbstats(configuration)
    dbs = [db for db in dbs if db['valid']]
    if not dbs:
        conn = getdefaultdatabase(configuration, create = True)
    else:
        dbname = dbs[0]['name']
        conn = connectdatabase(dbname)
        updatedatabaseaccess(configuration,dbname)
    return conn

###################### GENERAL FUNCTIONS
def basicconfig():
    """ A helper function to create valid System Configuration data """
    return dict(databases=[])

def coreconfig():
    """ Helper function to return the Core App's Config File """
    return loadsqljson(Core.__file__)

def getconfigfilepath():
    """ Convenience function for getting the appropriate location for the System
    Config file (makes no garauntee to its existence, file integrity, etc).
    """
    return (filestructure.DATAPATH / "config.json").resolve()

def getconfig(create = True): ## Tested- ConfigCase, NoConfigCase
    """ Loads the sql module's configuration file.
    
    If create is Ture (default), the config file will automatically be created if it does not exist;
    otherwise a FileNotFoundError will be raised.
    """
    filepath = getconfigfilepath()
    if not filepath.exists() and create is True:
        with open(str(filepath),'w') as f:
            json.dump(basicconfig(),f)
    elif not filepath.exists():
        raise FileNotFoundError("System Configuration File does not exist!")
    with open(str(filepath),'r') as f:
        configuration = json.load(f)
    return configuration

def getdbstats(configuration): ## General Database
    """ Returns a list of dicts based on the databases listed in the configuration's settings.
   
    The results have keys:
        name: file name
        recent: last accessed (timestamp)
        valid: Whether the database can be successfully connected to via connectdatabase
    The results are sorted by last access time (newest first).
    """
    dbs = configuration['databases']
    out = []
    for dbsettings in dbs:
        db,recent = dbsettings['name'],dbsettings['recent']
        try:
            conn = connectdatabase(db)
        except:
            out.append(dict(name=db, recent = recent, valid = False))
        else:
            out.append(dict(name=db, recent = recent, valid = True))
    return sorted(out, lambda db: db['recent'], reverse = True)

def loadtables(module,configuration, connection, version = True, missing = True, different = True):
    """ Checks all tables across all apps
    
    configuration should be the sql module's configuration file.
    connection is a database connection.
    If version is True (default), any tables that are of the wrong version- and for
    which an upgrade path is available- will be updated according to the upgrade path.
    If missing is True (default), any tables defined by the app's sql config will be
    automatically added. Otherwise, an AttributeError will be raised.
    It is recommmended that you back up the database before running this method if
    version, missing or different are True.
    """
    tablecheck = checktables(connection,configuration)
    if not version is True and not tablecheck.version :
        raise IntegrityError(f"App version mismatch!")
    if not missing is True and tablecheck.missing:
        raise IntegrityError(f"Database missing tables: {','.join([table['name'] for table in tablecheck.missing])}")
    if not different is True and tablecheck.different:
        raise IntegrityError(f"Database tables differ: {','.join([table['name'] for table in tablecheck.different])}")
    sqlfile = loadmodulesql(configuration['appname'])
    setup = configuration.get("setup")
    for table in tablecheck.missing:
        tablesetup = setuptable(configuration,connection,table)
        if setup and table['name'] in setup:
            meths = setup[table['name']]
            for metho in meths:
                meth = getattr(sqlfile,metho)
                meth(connection)
    connection.commit()

def loadcoretables(connection):
    """ Executes the loadtables procedure, but for the Core App and using version and missing flags, but not different """
    module,config = loadapp("Core")
    loadtables(module,config,connection,missing=True,version=True, different = False)

def loadapp(app):
    """ Imports the App's module and opens its sql configuration file, returning both """
    _module = loadmodule(app)
    if not _module:
        return None, None
    if hasattr(_module,"SQLCONFIG"):
        appconfig = loadsqljson(_module.__file__, _module.SQLCONFIG)
    else:
        appconfig = loadsqljson(_module.__file__)
    return _module,appconfig

def loadmodule(app):
    """ aldb2-specificy wrapper for importlib.import_module """
    try:
        return importlib.import_module(f".{app}","aldb2")
    except:
        return None

def loadmodulesql(app):
    """ import.import_module wrapper for app.sql """
    try:
        return importlib.import_module(".sql",f"aldb2.{app}")
    except:
        return None

@row_factory_saver
def getdatabasetables(connection):
    """ A simple function to return a list of tables in the provided database. Returns a mapping {tablename:table creation sql} """
    dbtables = connection.execute("""SELECT tbl_name,sql FROM sqlite_master where type = "table" AND name NOT LIKE "sqlite_%";""").fetchall()
    return {db[0]: db[1] for db in dbtables}

def main(connection, userid = None, different = False, version = True, missing = True):
    """ Runs app database and app validation on the given connection. Returns a mapping with results.
    
    If userid is specified, will only install non-Core apps registered by that user
    (otherwise, will install all apps registed in the database).
    Accept's loadtables's different, missing, and version arguments and will pass them for every app loaded.
    """
    coremodule,coreconfig = loadapp("Core")
    loadtables(coremodule,coreconfig,connection,missing=missing,version=version)
    if userid is None:
        apps = Core.getinstalledapps(connection)
    else:
        apps = Core.getuserapps(connection,userid)
    apps = [app['app'] for app in apps]
    appsloaded = dict(apps={})
    for app in apps:
        module,config = loadapp(app)
        if not module:
            appsloaded['apps'][app] = None
            continue
        tables = loadtables(module,config,connection,missing=missing,version=version, different = different)
        appsloaded['apps'][app] = dict(module=module, tables = tables)
    return appsloaded


    

############## SECUITY FUNCTIONS
from aldb2.Core.sql.security import *
