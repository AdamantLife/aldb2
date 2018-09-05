## Builtin
import json
import pathlib
## This Module
from aldb2 import filestructure
from aldb2.Core import core
from aldb2.Core.sql import util

############### Database Setup
def setgenres(connection):
    """ Sets up the base genres """
    path = pathlib.Path(__file__).resolve().parent
    genrefile = path / "genres.json"
    with open(genrefile,'r') as f:
        genres = json.load(f)
    connection.executemany(""" INSERT INTO \"genres\" (name, abbreviation, heavy, spoiler) VALUES (:name,:abbreviation,:heavy,:spoiler);""",genres)

def setyearseasons(connection):
    """ Sets up the Seasons of the year """
    connection.execute(""" INSERT INTO yearseason (yearseasonid, season) VALUES (0,"Winter"),(1,"Spring"),(2,"Summer"),(3,"Fall");""")

###############  installed_apps
@util.row_factory_saver
def getinstalledapps(connection):
    """ Returns a list of apps registered with the database.

    The return is a list of dictionaries with keys "app" and "version".
    """
    installed = connection.execute("""SELECT module,version FROM "installed_apps";""").fetchall()
    return [dict(app=app[0],version=app[1]) for app in installed]

@util.row_factory_saver
def getappbyname(connection,appname):
    """ Returns an app's information based on app name """
    result = connection.execute("""SELECT * FROM "installed_apps" WHERE module = :appname;""",dict(appname=appname)).fetchone()
    if result:
        return {"installid":result[0],"module":result[1],"version":result[2]}
    return None


def installapp(connection,app):
    """ Registers a new app with the database. Returns module and config """
    try:
        module,config = util.loadapp(app)
    except:
        raise FileNotFoundError("Could not locate App in Program Directory")
    if not module or not config:
        raise AttributeError("Could not load App's module or configuration file.")
    util.loadtables(module,config,connection)
    connection.execute("""INSERT INTO "installed_apps" (module, version) VALUES (:app, :version);""",dict(app = app, version = config['version']))
    return module,config

############## user_apps

def getuserapps(connection,userid):
    """ Returns a list of installed apps that the user has elected to use.

    Returns a list of dictionaries with keys: "installation id", "app", and "version".
    """
    userapps = connection.execute("""
SELECT "installed_apps".installid, "installed_apps".module, "installed_apps".version
FROM "user_apps"
LEFT JOIN "installed_apps" ON "user_apps".installid = "installed_apps".installid
WHERE userid = :userid;""",
dict(userid=userid) ).fetchall()
    return [ { "installation id":uapp[0], "app":uapp[1], "version":uapp[2]} for uapp in userapps]


def registeruserapp(connection,installationid,userid):
    """ Registers an app for a user's account using the installationid and userid. """
    connection.execute("""INSERT INTO "user_apps" (userid, installid) VALUES (:userid, :installationid);""",dict(userid=userid, installationid = installationid))


############# genres

@util.row_factory_saver
def getgenres(connection):
    """ Returns all genres as a list of mappings with keys: genreid, name, abbreviation, heavy, spoiler. """
    genres = connection.execute("""SELECT * FROM \"genres\";""").fetchall()
    return [{"genreid":gen[0], "name":gen[1],"abbreviation":gen[2], "heavy":gen[3],"spoiler":gen[4]} for gen in genres]

@util.row_factory_saver
def getgenrebyname(connection, name):
    """ Returns the stats for the supplied genre as a mapping with keys: genreid, name, abbreviation, heavy, spoiler. If the name is invalid, returns None. """
    genre = connection.execute("""SELECT * FROM \"genres\" WHERE name = :name;""",dict(name=name)).fetchone()
    if not genre: return None
    return {"genreid":genre[0], "name":genre[1],"abbreviation":genre[2], "heavy":genre[3],"spoiler":genre[4]}

@util.row_factory_saver
def getgenrebyabbreviation(connection, abbreviation):
    """ Returns the stats for the supplied genre abbreviation as a mapping with keys: genreid, name, abbreviation, heavy, spoiler. If the abbreviation is invalid, returns None. """
    genre = connection.execute("""SELECT * FROM \"genres\" WHERE abbreviation = :abbreviation;""",dict(abbreviation=abbreviation)).fetchone()
    if not genre: return None
    return {"genreid":genre[0], "name":genre[1],"abbreviation":genre[2], "heavy":genre[3],"spoiler":genre[4]}

############ yearseasons

@util.row_factory_saver
def getseasons(connection):
    """ Returns a list of yearseasons [Winter, Spring, Summer, Fall] """
    seasons = connection.execute("""SELECT season FROM yearseason;""").fetchall()
    return [season[0] for season in seasons]

############ Series

def addseries(connection, seriesname): ## Tested: SeriesCase_Base.test_addseries/bad
    """ Adds a new series, returning the rowid """
    if not isinstance(seriesname,str): raise ValueError("seriesname must be str.")
    result = connection.execute("""
INSERT INTO "series" (series) VALUES (
:series);""", dict(series=seriesname))
    return result.lastrowid

@util.row_factory_saver
def getseries(connection, seriesname): ## Tested: SeriesCase.test_getseries
    """ Returns a list of series objects that matches the seriesname in the database's series and aliases_series tables """
    if not isinstance(seriesname, str): raise AttributeError("seriesname must be str.")
    series = connection.execute(
"""SELECT "series".seriesid,series.series
    FROM "series"
    LEFT JOIN "aliases_series" ON "aliases_series".series = "series".seriesid
    WHERE series.series = :series or seriesalias = :series;""", dict(series = seriesname)).fetchall()
    return [core.Series(seriesid,sers) for (seriesid,sers) in series]

@util.row_factory_saver
def getserieslike(connection, seriesname): ## Tested: SeriesCase.test_getserieslike
    """ Returns a list of series objects that matches the seriesname in the database's series and aliases_series tables """
    if not isinstance(seriesname, str): raise ValueError("seriesname must be str.")
    series = connection.execute(
"""SELECT "series".seriesid,series.series
    FROM "series"
    LEFT JOIN "aliases_series" ON "aliases_series".series = "series".seriesid
    WHERE series.series LIKE :series or seriesalias LIKE :series
    GROUP BY "series".seriesid;""", dict(series = f"%{seriesname}%")).fetchall()
    return [core.Series(seriesid,sers) for (seriesid,sers) in series]

@util.row_factory_saver
def getaliasesforseries(connection,seriesid): ## Tested: SeriesCase.test_getaliasesforseries
    """ Returns all aliases registered for the given seriesid as a list of tuples (seriesaliasid, seriesalias) """
    aliases = connection.execute(
"""SELECT seriesaliasid, seriesalias
FROM aliases_series
WHERE series = :series;""",dict(series = seriesid)).fetchall()
    return aliases

def addseriesalias(connection, seriesid, seriesalias,language = None): ## Tested: SeriesCase.test_addseriesalias/bad/multiple
    """ Adds a new series alias, returning the rowid """
    if not isinstance(seriesalias,str): raise ValueError("alias must be str.")
    result = connection.execute("""
INSERT INTO "aliases_series" (seriesalias, series, language) VALUES (
:seriesalias, :seriesid, :language);""", dict(seriesalias=seriesalias, seriesid = seriesid, language = language))
    return result.lastrowid

def addsubseries(connection, seriesid, subseries):
    """ Adds a new subseries to "subseries" """
    if subseries is not None and not isinstance(subseries,str): raise ValueError("subseries must be str or None.")
    result = connection.execute(
""" INSERT INTO "subseries" (series, subseries) VALUES
(:seriesid,:subseries);""",dict(seriesid = seriesid, subseries=subseries))
    return result.lastrowid

@util.row_factory_saver
def getsubseriesforseries(connection, seriesid):
    """ Returns all subseries as SubseriesObjects for the given seriesid """
    result = connection.execute(
"""SELECT"subseries".subseriesid,subseries,"series".seriesid,series.series
FROM "series"
LEFT JOIN "subseries" ON "series".seriesid = "subseries".seriesid
WHERE "series".seriesid = :seriesid;""",
dict(seriesid = seriesid)).fetchall()
    return [core.Subseries(subseriesid,subseries,seriesid,series) for subseriesid,subseries,seriesid,series in result]

def addsubseriesalias(connection, subseriesid, subseriesalias, language = None):
    """ Adds an alias for the given subseries """
    if not isinstance(subseriesalias,str): raise ValueError("alias must be str.")
    result = connection.execute(
"""INSERT INTO "aliases_subseries" (subseries, subseriesalias, language) VALUES
(:subseriesid, :subseriesalias, :language);""",
dict(subseriesid = subseriesid, subseriesalias = subseriesalias, language = language))
    return result.lastrowid

@util.row_factory_saver
def getaliasesforsubseries(connection,subseriesid):
    """ Returns all aliases registered for the given subseriesid as a list of tuples (subseriesaliasid, subseriesalias) """
    aliases = connection.execute(
"""SELECT subseriesaliasid, subseriesalias
FROM aliases_subseries
WHERE subseriesid = :subseriesid;""",dict(subseriesid = subseriesid)).fetchall()
    return aliases

@util.row_factory_saver
def getsubseries(connection, subseriesname):
    """ Returns a list of Subseries objects that matches the subseriesname in the database's subseries and aliases_subseries tables """
    if not isinstance(subseriesname, str): raise AttributeError("subseriesname must be str.")
    subseries = connection.execute(
"""SELECT "subseries".subseriesid, "subseries".subseries, "subseries".subseriesid, subseries
    FROM "subseries"
    LEFT JOIN "aliases_subseries" ON "aliases_subseries".subseriesid = "subseries".subseriesid
    WHERE subseries = :subseriesname or subseriesalias = :subseriesname;""", dict(subseriesname = subseriesname)).fetchall()
    return [core.Series(seriesid,sers) for (seriesid,sers) in series]

@util.row_factory_saver
def getsubserieslike(connection, subseriesname): ## Tested: SeriesCase.test_getserieslike
    """ Returns a list of series objects that matches the subseriesname in the database's series and aliases_series tables """
    if not isinstance(subseriesname, str): raise ValueError("subseriesname must be str.")
    series = connection.execute(
"""SELECT "subseries".subseriesid,subseries
    FROM "subseries"
    LEFT JOIN "aliases_subseries" ON "aliases_subseries".subseriesid = "subseries".subseriesid
    WHERE subseries LIKE :subseriesname or subseriesalias LIKE :subseriesname
    GROUP BY "subseries".subseriesid;""", dict(subseriesname = f"%{subseriesname}%")).fetchall()
    return [core.Series(seriesid,sers) for (seriesid,sers) in series]

def addsubseriesgenres(connection,subseries,*genres):
    """ Adds a number of genres to the given subseries """
    inp = []
    for genre in genres:
        if isinstance(genre,str):
            genre = getgenrebyname(connection,genre)
            if not genre:
                genre = getgenrebyabbreviation(connection,genre)
            if isinstance(genre,dict):
                genre = genre['genreid']
        if isinstance(genre,int):
            inp.append(genre)
    insert = ",\n".join([f"({genre},{subseries})" for genre in inp])
    connection.execute(
f"""INSERT INTO genrelist_subseries (genre,subseries) VALUES
{insert};""")