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
INSERT INTO "series" VALUES ();""")
    return result.lastrowid

def search_aliases(connection,searchterm):
    """ Searches all aliases for a searchterm """
    return

