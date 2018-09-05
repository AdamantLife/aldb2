## This Module
from aldb2.RecordReader import *
## Backend
from alcustoms import sql

## Builtin
import collections
import pathlib
## Sister Module
from aldb2.Anime import anime
from aldb2.Anime import sql as animesql

""" Dependencies: Core, Anime, AnimeLife, WebModules """

class ImportResult():
    def __init__(self,result,reason,object):
        self.result = result
        self.reason = reason
        self.object = object
    @property
    def success(self):
        return bool(self.result)

def import_master(db, masterstats = None, masterepisodes = None, overwrite = False):
    """ Import masterstats and/or masterepisodes into the given database.

        In order to import stats and episodes with this method, the show/episode's SeasonID must
        be set. This method returns a 

        db should be a properly set up Database Connection for aldb2.
        By default, masterstats and masterepisodes refer to the module-default master file names
        in the current work directory. If provided, masterstats and/or masterepisodes should refer
        to existing files. If False, the file will not be imported into the database. If left as
        the default and the given file does not exist, the import for that filetype will be
        silently skipped.
        If overwrite is True, the database will be updated to match the provided files; existing
        records in the database that do not exist in the master file will not be removed or modified.
        By default (overwrite is False), this method will not update existing records and will only
        add missing ones.
    """
    if masterstats:
        masterstats = pathlib.Path(masterstats).resolve()
        if not masterstats.exists():
            raise ValueError("masterstats must be an existing file.")
    if masterepisodes:
        masterepisodes = pathlib.Path(masterepisodes).resolve()
        if not masterepisodes.exists():
            raise ValueError("masterepisodes must be an existing file.")
    if masterstats is None:
        masterstats = pathlib.Path(master.DEFAULTSTATFILE).resolve()
        if not masterstats.exists():
            masterstats = None
    if masterepisodes is None:
        masterepisodes = pathlib.Path(master.DEFAULTEPISODEFILE).resolve()
        if not masterepisodes.exists():
            masterepisodes = None

    stats = []
    if masterstats:
        stats = master.load_masterstats(masterstats)
    episodes = []
    if masterepisodes:
        episodes = master.load_masterepisodes(masterepisodes)

    ## Potential early exit to save time
    if not stats and not episodes: return

    ## TODO
    return
    ## Constant, Lookup, and Table Setup 
    ANIMEMEDIUM = db.getadvancedtable("mediums").quickselect(medium = "anime").first()
    if ANIMEMEDIUM is None:
        raise AttributeError("anime medium is not defined in the database")
    ANIMEMEDIUM = ANIMEMEDIUM.mediumid
    SEASONLOOKUP = animesql.getseasonallookup(db)

    ## Episodelookup is a lookup formatted: {"{seasonid}-{seasonindex}": [episodes],}
    episodelookup = collections.defaultdict(list)
    for episode in masterepisodes:
        if episode.seasonid and episode.seasonindex:
            episodelookup[f"{episodes.seasonid}-{episode.seasonindex}"].append(episode)
    
    seasontable = db.getadvancedtable("season")
    aliasestable = db.getadvancedtable("aliases_season")
    animeseasonstable = db.getadvancedtable("animeseasons")
    librarytable = db.getadvancedtable("animelibrary")
    linkstable = db.getadvancedtable("links_anime")
    imagestable = db.getadvancedtable("images_anime")
    sitestable = db.getadvancedtable("webmodules_siteids")

    """
        ### Stats
        # Season Table: seasonid 
        #
        # Aliases: originalname name	
        # AnimeLibrary: notes
        # AnimeSeasons: seasonindex
        # Images_Anime: image
        # Links_Anime: website channel/channelhomepage pv
        # WebModules_SiteIDs: showboyid annid anilistid malid anidbid 
        #
        # Unused: originalid seriesid subseriesid watching include day firstepisode group rssfeedname hashtag lastseason 
        #
        ## >seriesid and subseriesid should validate seasonid
            
        ### Episodes
        # Season Table seasonid
        #
        # AnimeLibrary: sum(episodes)
        # AnimeSeason: seasonindex
        # AL_WeeklyRanking: week rank episodenumber hypelistrank
        #
        # Unused: originalid
        #
        ## >seriesid and seasonindex should exist in Stats
    """

    if stats:
        for season in stats:
            ## We'll use continue to cut down on the indentation
            if not season.seasonid:
                outstats.append(ImportResult(False,"No seasonid",season))
                continue
            dbentry = seasontable.quickselect(seasonid = season.seasonid)
            
            if not dbentry: 
                outstats.append(ImportResult(False,"seasonid not in Database",season))
                continue

            ## English Alias
            if season.name:
                result = aliasestable.get_or_addrow(seasonid = season.seasonid, seasonalias = season.name).first()
                aliasestable.quickupdate(constraints = {"seasonaliasid":result}, language = "English")
            ## Japanese Alias
            if season.originalname:
                result = aliasestable.get_or_addrow(seasonid = season.seasonid, seasonalias = season.originalname).first()
                aliasestable.quickupdate(constraints = {"seasonaliasid":result}, language = "English")

            ## notes
            if season.notes:
                result = librarytable.get_or_addrow(season = season.seasonid).first()
                libraryentry = librarytable.quickselect(libraryid = result)
                notes = ""
                if libraryentry.notes: notes = libraryentry.notes
                librarytable.quickupdate(constraints ={"season":season.seasonid}, notes = notes + season.notes)

            ## Season
            animeseason = anime.parseanimeseason_toobject(season.seasonindex)
            animeseasonid = animeseasonstable.get_or_addrow(seasonid = dbentry, season = SEASONLOOKUP[animeseason.season], year = animeseason.year).first()


            ## image
            if season.image:
                imagestable.get_or_addrow(season = season.seasonid, url = season.image)
                
            ## website
            if season.website:
                linkstable.get_or_addrow(season = season.seasonid, url = season.website, identification = "homepage")

            ## stream
            if season.channelhomepage:
                linkstable.get_or_addrow(season = season.seasonid, url = season.channelhomepage, identification = "stream")

            ## siteids
            for kw in season.to_dict():
                if kw.endswith("id"):
                    site = kw.rstrip("id")
                