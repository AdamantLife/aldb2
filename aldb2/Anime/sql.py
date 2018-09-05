from aldb2.Core.sql import util

from aldb2.Anime import anime

SQLCONFIG = util.loadsqljson(__file__)

############### Database Setup
def setmediums(connection):
    """ Sets up the Mediums table """
    connection.execute("""INSERT INTO mediums (mediumid,medium) VALUES (1,'Anime'), (2, 'OVA'), (3, 'Movie');""")

######################

def getseasonallookup(connection):
    """ Returns a dictionary of {seasonname:rowid} for the yearseason table (Spring,Summer,Fall,Winter) """
    results = connection.execute("""SELECT yearseasonid,season FROM yearseason;""").fetchall()
    return {r[1]:r[2] for r in results}

def getseasonindex(year,season):
    """ Returns the correct seasonindex for the given year and season """
    return year + season/10

def addseason(connection, seasonname, subseriesid, mediumid = None, episodes = 0): ## Tested: SeasonCase_Base.test_addseason/bad
    """ Adds a new season, returning the rowid """
    if not isinstance(seasonname,str): raise ValueError("seasonname must be str.")
    result = connection.execute("""
INSERT INTO "season" (subseriesid, season, mediumid, episodes) VALUES (
:season, :subseriesid, :mediumid, :episodes;""", dict(season=seasonname, subseriesid = subseriesid, mediumid = mediumid, episodes = episodes))
    return result.lastrowid

@util.row_factory_saver
def getseason(connection, seasonname): ## Tested: seasonCase.test_getseason
    """ Returns a list of season objects that matches the seasonname in the database's season and aliases_season tables """
    if not isinstance(seasonname, str): raise AttributeError("seasonname must be str.")
    season = connection.execute(
"""SELECT "season".seasonid, season, "subseries".seriesid, series, "season".subseriesid, subseries, "season".mediumid, medium, episodes
    FROM "season"
    LEFT JOIN "aliases_season" ON "aliases_season".seasonid = "season".seasonid
    LEFT JOIN "subseries" ON "subseries".subseriesid = "season".subseriesid"
    LEFT JOIN "series" on "series".seriesid = "season".seriesid
    LEFT JOIN "mediums" ON "mediums".mediumid = "season".mediumid
    WHERE season = :season or seasonalias = :season;""", dict(season = seasonname)).fetchall()
    return [anime.Season(seasonid = seasonid,season = season, seriesid = seriesid, series = series, subseriesid = subseriesid, mediumid = mediumid, medium = medium, episodes = episodes)
            for (seasonid, season, seriesid, series, subseriesid, subseries, mediumid, medium, episodes)
            in season]

@util.row_factory_saver
def getseasonlike(connection, seasonname): ## Tested: seasonCase.test_getseasonlike
    """ Returns a list of season objects that matches the seasonname in the database's season and aliases_season tables """
    if not isinstance(seasonname, str): raise ValueError("seasonname must be str.")
    season = connection.execute(
"""SELECT "season".seasonid, season, "subseries".seriesid, series, "season".subseriesid, subseries, "season".mediumid, medium, episodes
    FROM "season"
    LEFT JOIN "aliases_season" ON "aliases_season".seasonid = "season".seasonid
    LEFT JOIN "subseries" ON "subseries".subseriesid = "season".subseriesid"
    LEFT JOIN "series" on "series".seriesid = "season".seriesid
    LEFT JOIN "mediums" ON "mediums".mediumid = "season".mediumid
    WHERE season LIKE :season or seasonalias LIKE :season
    GROUP BY "season".seasonid;""", dict(season = f"%{seasonname}%")).fetchall()
    return [anime.Season(seasonid = seasonid,season = season, seriesid = seriesid, series = series, subseriesid = subseriesid, mediumid = mediumid, medium = medium, episodes = episodes)
            for (seasonid, season, seriesid, series, subseriesid, subseries, mediumid, medium, episodes)
            in season]

@util.row_factory_saver
def getaliasesforseason(connection,seasonid): ## Tested: seasonCase.test_getaliasesforseason
    """ Returns all aliases registered for the given seasonid as a list of tuples (seasonaliasid, seasonalias) """
    aliases = connection.execute(
"""SELECT seasonaliasid, seasonalias
FROM aliases_season
WHERE seasonid = :seasonid;""",dict(seasonid = seasonid)).fetchall()
    return aliases

def addseasonalias(connection, seasonid, seasonalias): ## Tested: seasonCase.test_addseasonalias/bad/multiple
    """ Adds a new season alias, returning the rowid """
    if not isinstance(seasonalias,str): raise ValueError("alias must be str.")
    result = connection.execute("""
INSERT INTO "aliases_season" (seasonalias, seasonid) VALUES (
:seasonalias, :seasonid);""", dict(seasonalias=seasonalias, seasonid = seasonid))
    return result.lastrowid


def QS_getseasonindex():
    """ Returns the sql to get a seasonindex for a given seasonid """
    return f""" SELECT seasonindex FROM seasonindex WHERE season = :seasonid """

def QS_gettitle():
    """ Returns the Query column String for a formatted Anime Title ( "{Series}- {Subseries}: {Season}" ).
    
        Note  that it ONLY returns the column string; you must place it inside of a valid SELECT statement
        with tables named "series", "subseries", and "season".
    """
    return """( series.series || (CASE WHEN subseries.subseries IS NOT NULL THEN "- "||subseries.subseries ELSE "" END) || (CASE WHEN season.season IS NOT NULL THEN ": "||season.season ELSE "" END) ) AS title """