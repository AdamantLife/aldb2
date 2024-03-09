## Builtin
import datetime
import typing
## This Module
import aldb2.constants as constants
import aldb2.Core.core as core

def _raise_differenceerror(object):
    return 'Anime can only get difference from Animes and Dicts: received {objtype}'.format(objtype=type(object))

def getcurrentseason()-> constants.AnimeSeasonDict:
    """ Returns the current season """
    today = datetime.date.today()
    season= constants.SEASONS[today.month//4]
    year = today.year
    return {"season" : season, "year" : year}

def sortseasondicts(animeseasons: list[constants.AnimeSeasonDict])->list[constants.AnimeSeasonDict]: ## Tested: AnimeSeasonDictCase.test_sortseasons
    """ Chronologically sorts season dicts using getseasonhash
    
    (Note, it is normallly preferable to simply convert season dicts
    to AnimeSeasons, which will sort naturally)
    """
    return sorted(animeseasons, key = getseasonindex)

def getseasonindex(animeseason: constants.AnimeSeasonDict)-> float:
    """ Returns the standard SeasonIndex float value of the AnimeSeason (Year.seasonindex) """
    return float(f"{animeseason['year']}.{constants.SEASONS.index(animeseason['season'])}")

def getseasonhash(animeseason: constants.AnimeSeasonDict)->int: ## Tested: AnimeSeasonDictCase.test_getseasonhash
    """ Returns a hashable identifier for an animeseason dict """
    return hash(getseasonindex(animeseason))

def sumseasons(animeseasons: "list[list[AnimeSeason]]"): ## Tested: AnimeSeasonCase.test_sumseasons
    """ Combines lists of animeseasons into a list of unique seasons """
    seasons=sum(animeseasons,[])
    return sorted(set(seasons)) #type: ignore ## TODO: Fix this type ignore, is tested so should be valid and may be the type checker

def sumseasondicts(animeseasons: list[list[constants.AnimeSeasonDict]])-> list[constants.AnimeSeasonDict]: ## Tested: AnimeSeasonDictCase.test_sumseasondicts
    """ Combines multiple lists of animeseason dicts into a consolidated list of unique seasons """
    seasons=sum(animeseasons,[])
    out = dict()
    for season in seasons:
        shash = getseasonhash(season)
        if shash not in out:
            out[shash] = season
    return [season for shash, season in sorted(out.items(), key = lambda season: season[0])]

ParseableSeason = typing.Union[str, float, tuple, constants.AnimeSeasonDict, "AnimeSeason", constants.ANIMESEASONDESCRIPTOR]

def parseanimeseason(astring: ParseableSeason)->"AnimeSeason": ## Tested: AnimeSeasonDictCase.test_parseanimeseason_[good/bad]
    """ Parses and Validates a Season String and returns a Season Dict """
    
    if isinstance(astring,AnimeSeason):
        ## AnimeSeason Objects are already validated
        return astring
    
    if isinstance(astring,float):
        ## SeasonIndex representation (aka- AnimeSeason.__hash__ format)
        season = (astring - int(astring))
        year = int(astring - season)
        season = round(season*10,0)
        astring = buildseasondict(season = int(season), year = year)

    if isinstance(astring,str):

        try: fstring = float(astring)
        except: pass
        else: return parseanimeseason(fstring)
        astring = tuple(astring.split())
        if len(astring) == 1:
            astring = tuple(astring[0].split("_"))
        if len(astring) == 1:
            astring = tuple(astring[0].split("-"))

    if isinstance(astring,tuple):
        if len(astring)>2: raise ValueError("Not an AnimeSeason")                   ## There should only be valid items for seasons
        a,b=astring
        try: int(a)                                                                 ## Check if first item is Year
        except ValueError:
            try: int(b)                                                             ## Else, check if second item is Year
            except ValueError: raise ValueError("Not an AnimeSeason")               ## Improper format if neither is Year
            else: year,season=b,a                                                   ## Assign roles
        else: year,season=a,b                                                       ## Assign roles
        astring = buildseasondict(year=int(year),season=season)

    if isinstance(astring,dict):
        try:
            return AnimeSeason(**buildseasondict(**{"season" : astring['season'], "year" : int(astring['year'])}))
        except (TypeError, KeyError):
            raise ValueError("Not an AnimeSeason")
    raise ValueError("Not an AnimeSeason")

def parseanimeseason_toobject(astring: ParseableSeason)-> "AnimeSeason":
    """ Converts an Anime Season string into an AnimeSeason Object via parseanimestring """
    seasondict = parseanimeseason(astring)
    if isinstance(seasondict,AnimeSeason): return seasondict
    return AnimeSeason(**seasondict)

def stepanimeseason_todict(animeseasondict: ParseableSeason,increment: int=1)-> constants.AnimeSeasonDict:
    """ Chronologically navigates a number of seasons (defualt 1) from the given season and returns the result"""
    animeseason = parseanimeseason_toobject(animeseasondict)
    new = stepanimeseason(animeseason, increment = increment)
    return new.as_dict()

def stepanimeseason(animeseason: "AnimeSeason",increment: int = 1)-> "AnimeSeason":
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
    return AnimeSeason(season=constants.SEASONS[newseason],year=year)

def sortbyanimeseason(animelist,reverse: bool=False): ## TODO: Figure out what anime list this is (Season does not have an AnimeSason attribute)
    """ Sorts a list of animes by their first animeseason """
    animelist.sort(key = lambda anime: min(anime.animeseasons), reverse = reverse)
    return animelist

def buildseasondict(season: str|int|constants.SEASONALIASESTYPE, year: int)->constants.AnimeSeasonDict:
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
    season = season.capitalize() # type: ignore ## season from the previous line is always a value from SEASONS.lower() but the type checker doesn't know that
    if season not in constants.SEASONS:
        raise AttributeError("Season must be 'Winter','Spring','Summer', or 'Fall', or an accepted alias")
    try:
        year = int(year)
    except:
        raise TypeError("Year must be an integer")
    return {"season" : season, "year" : int(year)} # type: ignore ## TODO: Pretty sure this wil be fixed by adding Capitalized Season name
                                                    ## to SEASONS and changing the above index //6 * 6 to index 7

class AnimeSeason():
    """ The representation of a single cour during a specific year: e.g- Fall 2017 """
    def __init__(self,season: constants.SEASONSTYPE, year: int):
        """ Creates a new Season.
        
        season can be the season name (case insensitive), it's index, or an accepted abbreviation.
        year should be an integer.
        """
        seasondict: constants.AnimeSeasonDict = buildseasondict(season,year)
        self.season: constants.SEASONSTYPE = seasondict["season"]
        self.year:int = int(seasondict["year"])

    @property
    def seasonnumber(self)-> int:
        """ Returns the index of the AnimeSeasons's season """
        return constants.SEASONS.index(self.season)

    def as_dict(self)-> constants.AnimeSeasonDict:
        return {"season" : self.season, "year" : self.year}

    def previous(self)-> "AnimeSeason":
        return stepanimeseason(self,-1)
    def next(self) -> "AnimeSeason":
        return stepanimeseason(self,+1)

    @property
    def seasonindex(self)-> float:
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
    def __init__(self, seasonid: int, seriesid: int, franchiseid: int,
                 season: str, series: str, franchise: str,
                 mediumid: int, medium: str, episodes: int = 0):
        self.series: core.series = core.Franchise(seriesid = seriesid, series = series, franchiseid = franchiseid, franchise = franchise)
        self.seasonid: int = seasonid
        self.season: str = season
        self.medium: Medium = Medium(mediumid = mediumid, medium = medium)
        self.episodes: int = episodes

class Medium():
    def __init__(self, mediumid: int, medium: str):
        self.mediumid: int = mediumid
        self.medium: str = medium

    def __str__(self):
        return self.medium

class SeasonGenres():
    def __init__(self, genrelistid, genreid, seasonid):
        self.genrelistid: int = genrelistid
        self.genreid: int = genreid
        self.seasonid: int = seasonid

class seriesGenres():
    def __init__(self, genrelistid: int, genreid: int, seriesid: int):
        self.genrelistid: int = genrelistid
        self.genreid: int = genreid
        self.seriesid: int = seriesid

class LibraryEntry():
    def __init__(self, libraryid: int, seasonid: int, seriesid:int, franchiseid: int,
                 season: str, series:str, franchise: str,
                 mediumid: int, medium: str, episodes: int = 0,
                 catrank: int = 2, rank: int = 250, locked: bool = False, episodeswatched: int = 0,
                 lastwatched: int = 0, bookmarked: bool = False):
        self.libraryid: int = libraryid
        self.seasonid: int = seasonid
        self.season: Season = Season(seasonid=seasonid, seriesid=seriesid, franchiseid = franchiseid,
                                     season = season, series=series, franchise = franchise,
                                     mediumid=mediumid, medium = medium, episodes = episodes)
        self.catrank: int  = catrank
        self.rank: int = rank
        self.locked: bool = locked
        self.episodeswatched: int = episodeswatched
        self.lastwatched: int = lastwatched
        self.bookmarked: bool = bookmarked