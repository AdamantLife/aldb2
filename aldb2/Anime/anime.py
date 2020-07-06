## Builtin
import datetime
import os
import time
import zipfile
## Third Party
import PIL.Image, PIL.ImageTk
## This Module
import aldb2.constants as constants
import aldb2.filestructure as filestructure
import aldb2.Core.core as core

def _raise_differenceerror(object):
    return 'Anime can only get difference from Animes and Dicts: received {objtype}'.format(objtype=type(object))

def getcurrentseason():
    """ Returns the current season """
    today = datetime.date.today()
    season= constants.SEASONS[today.month//4]
    year = today.year
    return dict(season = season, year = year)

def sortseasondicts(animeseasons): ## Tested: AnimeSeasonDictCase.test_sortseasons
    """ Chronologically sorts season dicts using getseasonhash
    
    (Note, it is normallly preferable to simply convert season dicts
    to AnimeSeasons, which will sort naturally)
    """
    return sorted(animeseasons, key = getseasonindex)

def getseasonindex(animeseason):
    """ Returns the standard SeasonIndex float value of the AnimeSeason (Year.seasonindex) """
    return float(f"{animeseason['year']}.{constants.SEASONS.index(animeseason['season'])}")

def getseasonhash(animeseason): ## Tested: AnimeSeasonDictCase.test_getseasonhash
    """ Returns a hashable identifier for an animeseason dict """
    return hash(getseasonindex(animeseason))

def sumseasons(animeseasons): ## Tested: AnimeSeasonCase.test_sumseasons
    """ Combines lists of animeseasons into a list of unique seasons """
    seasons=sum(animeseasons,[])
    return sorted(set(seasons))

def sumseasondicts(animeseasons): ## Tested: AnimeSeasonDictCase.test_sumseasondicts
    """ Combines lists of animeseason dicts into a list of unique seasons """
    seasons=sum(animeseasons,[])
    out = dict()
    for season in seasons:
        shash = getseasonhash(season)
        if shash not in out:
            out[shash] = season
    return [season for shash, season in sorted(out.items(), key = lambda season: season[0])]

def parseanimeseason(astring): ## Tested: AnimeSeasonDictCase.test_parseanimeseason_[good/bad]
    """ Parses and Validates a Season String and returns a Season Dict """
    
    if isinstance(astring,AnimeSeason):
        ## AnimeSeason Objects are already validated
        return astring

    if isinstance(astring,str):
        try: astring = float(astring)
        except: pass
        else: return parseanimeseason(astring)
        if len(astring.split())>1: return parseanimeseason(astring.split())         ## Convert whitespace-separated to list
        if len(astring.split("_"))>1: return parseanimeseason(astring.split("_"))   ## Convert underscore-separated to list
        if len(astring.split("-"))>1: return parseanimeseason(astring.split("-"))   ## Convert hyphen-separated to list
        raise ValueError("Not an AnimeSeason")                                      ## No handling for other format strings

    if isinstance(astring,list):
        if len(astring)>2: raise ValueError("Not an AnimeSeason")                   ## There should only be valid items for seasons
        a,b=astring
        try: int(a)                                                                 ## Check if first item is Year
        except ValueError:
            try: int(b)                                                             ## Else, check if second item is Year
            except ValueError: raise ValueError("Not an AnimeSeason")               ## Improper format if neither is Year
            else: year,season=b,a                                                   ## Assign roles
        else: year,season=a,b                                                       ## Assign roles
        return buildseasondict(year=year,season=season)

    if isinstance(astring,dict):
        try:
            return buildseasondict(**dict(season = astring['season'], year = astring['year']))
        except (TypeError, KeyError):
            raise ValueError("Not an AnimeSeason")

    if isinstance(astring,float):
        ## SeasonIndex representation (aka- AnimeSeason.__hash__ format)
        season = (astring - int(astring))
        year = int(astring - season)
        season = round(season*10,0)
        return parseanimeseason(dict(season = season, year = year))
    raise ValueError("Not an AnimeSeason")

def parseanimeseason_toobject(astring):
    """ Converts an Anime Season string into an AnimeSeason Object via parseanimestring """
    seasondict = parseanimeseason(astring)
    if isinstance(seasondict,AnimeSeason): return seasondict
    return AnimeSeason(**seasondict)

def stepanimeseasondict(animeseasondict,increment=1):
    """ Chronologically navigates a number of seasons (defualt 1) from the given season and returns the result"""
    animeseason = parseanimeseason_toobject(animeseasondict)
    new = stepanimeseason(animeseason, increment = increment)
    return new.as_dict()

def stepanimeseason(animeseason,increment = 1):
    """ Chronologically navigates a number of seasons (defualt 1) from the given season and returns the result"""
    newseason=animeseason.seasonnumber+increment
    year=animeseason.year
    seasonlen = len(constants.SEASONS)
    #if newseason >= seasonlen:
    year+= newseason // seasonlen
    newseason %= seasonlen
    #elif newseason<0:
    #    year-= // seasonlen
    #    newseason %= seasonlen
    return AnimeSeason(season=newseason,year=year)

def sortbyanimeseason(animelist,reverse=False):
    """ Sorts a list of animes by their first animeseason """
    return sorted(animelist, key = lambda anime: min(anime.animeseasons), reversed = reverse)

def buildseasondict(season,year):
    """ Creates a correctly formatted season dict.
   
    Accepts aliases for season (case-insensitive):
        Winter: 0   , "W"   , "Wi"  , "Win"
        Spring: 1           , "Sp"  , "Spr"
        Summer: 2           , "Su"  , "Sum"
        Fall:   3   , "F"   , "Fa"  , "Fal"
    """
    try:
        season = int(season)
    except: pass
    if isinstance(season,int):
        if season > 3:
            raise AttributeError("Season Index must be in range 0...3 inclusive.")
        season = str(season)
    if not isinstance(season,str):
        raise AttributeError("Season must be string, or integer season index")
    season = season.lower()
    if season in constants.SEASONALIASES:
        index = constants.SEASONALIASES.index(season)
        season = constants.SEASONALIASES[index // 6 * 6]
    season = season.capitalize()
    if season not in ("Winter","Spring","Summer","Fall"):
        print(season)
        raise AttributeError("Season must be 'Winter','Spring','Summer', or 'Fall', or an accepted alias")
    try:
        year = int(year)
    except:
        raise TypeError("Year must be an integer")
    return dict(season = season, year = year)

class AnimeSeason():
    """ The representation of a single cour during a specific year: e.g- Fall 2017 """
    def __init__(self,season,year):
        """ Creates a new Season.
        
        season can be the season name (case insensitive), it's index, or an accepted abbreviation.
        year should be an integer.
        """
        seasondict = buildseasondict(season,year)
        self.season = seasondict["season"]
        self.year = seasondict["year"]

    @property
    def seasonnumber(self):
        """ Returns the index of the AnimeSeasons's season """
        return constants.SEASONS.index(self.season)

    def as_dict(self):
        return dict(season = self.season, year = self.year)

    def previous(self):
        return stepanimeseason(self,-1)
    def next(self):
        return stepanimeseason(self,+1)

    @property
    def seasonindex(self):
        return getseasonindex(self.as_dict())

    def __hash__(self):
        return getseasonhash(self.as_dict())

    def __eq__(self,other):
        if isinstance(other,AnimeSeason):
            return hash(self) == hash(other)

    def __lt__(self,other):
        if isinstance(other,AnimeSeason):
            return self.seasonindex < other.seasonindex

    def __lte__(self,other):
        if isinstance(other,AnimeSeason):
            return self.seasonindex <= other.seasonindex

    def __float__(self):
        return self.seasonindex

    def __str__(self):
        return f"{self.season} {self.year}"

    def __repr__(self):
        return f"{self.__class__.__name__}: {self}"

class Season():
    def __init__(self, seasonid, season, seriesid = None, series = None, subseriesid = None, subseries = None,
                 mediumid = None, medium = None, episodes = 0):
        self.subseries = core.Subseries(subseriesid = subseriesid, subseries = subseries, seriesid = seriesid, series = series)
        self.seasonid = seasonid
        self.season = season
        self.medium = Medium(mediumid = mediumid, medium = medium)
        self.episodes = episodes

class Medium():
    def __init__(self, mediumid, medium):
        self.mediumid = mediumid
        self.medium = medium

    def __str__(self):
        return self.medium

class SeasonGenres():
    def __init__(self, genrelistid, genreid, seasonid):
        self.genrelistid = genrelistid
        self.genreid = genreid
        self.seasonid = seasonid

class SubseriesGenres():
    def __init__(self, genrelistid, genreid, subseriesid):
        self.genrelistid = genrelistid
        self.genreid = genreid
        self.subseriesid = subseriesid

class LibraryEntry():
    def __init__(self, libraryid, userid, seasonid, season = None, catrank = 2, rank = 250, locked = False, episodeswatched = 0, lastwatched = 0, bookmarked = False,
                 seriesid = None, series = None, subseriesid = None, subseries = None, medium = "TV", episodes = 0):
        self.libraryid = libraryid
        self.userid = userid
        self.seasonid = seasonid
        self.season = Season(seasonid, season,seriesid = seriesid, series = series, subseriesid=subseriesid,subseries=subseries, medium = medium, episodes = episodes)
        self.catrank = catrank
        self.rank = rank
        self.locked = locked
        self.episodeswatched = episodeswatched
        self.lastwatched = lastwatched
        self.bookmarked = bookmarked