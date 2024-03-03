import collections
import pathlib
import typing
import warnings
from aldb2.Anime import anime

ShowName = str
ShowOriginalID = int
ShowSeasonID = int
ShowSubseriesID = int
ShowSeriesID = int
ShowIdentifier = typing.Union[ShowName,ShowOriginalID,ShowSeasonID,ShowSubseriesID,ShowSeriesID]
ShowLookup = collections.OrderedDict[ShowIdentifier, "ShowBase"]
WeekLookup = collections.OrderedDict[int, "RankingSheet"]
EpisodeDict = typing.Dict[ShowIdentifier, "Episode"]

class RecordStatsDict(typing.TypedDict):
    season: str
    year: int
    version: float
    ## TypedDicts do not normally allow additional fields
    ## This was implemented in favor of creating RecordStatsDict subclasses
    extras: dict[str, typing.Any]

class SeasonRecord():
    def __init__(self,file:pathlib.Path, recordstats: "RecordStats", showstats: "ShowStats", weeks: WeekLookup):
        self._file=file
        self._recordstats = recordstats
        self._showstats = showstats
        self._weeks = weeks
        
    @property
    def file(self)->pathlib.Path:
        return self._file
    @property
    def weeks(self)->typing.Dict[int,"RankingSheet"]:
        return self._weeks
    def week(self,weeknumber: int)->"RankingSheet":
        """ Returns the RankingSheet for the given week number """
        return self.weeks[weeknumber]
    @property
    def recordstats(self)->"RecordStats":
        return self._recordstats
    @property
    def showstats(self)->"ShowStats":
        return self._showstats
    @property
    def animeseason(self)->anime.AnimeSeason|None:
        return self.recordstats.animeseason

    def getlastweek(self)->"RankingSheet|None":
        weeks = list(self.weeks.values())
        weeks.sort(key=lambda week: week.weeknumber, reverse=True)
        return weeks[0] if weeks else None
    
    def getlastcompletedweek(self)->"RankingSheet|None":
        weeks = list(filter(lambda week: week.episodes, list(self.weeks.values())))
        weeks.sort(key=lambda week: week.weeknumber, reverse=True)
        return weeks[0] if weeks else None
    
    def sumnormalize(self, episodes: list["Episode"], weeknumber: int|None = None)->dict[int,float]:
        """ Sums the normalized value for the given Show up to and including the given week. """
        showstats = {episode.originalid:self.showstats.getshowsbyoriginalid(episode.originalid) for episode in episodes}
        previousnormalize = {}
        for episode in episodes:
            previousnormalize[episode.originalid] = 0
            if showstats[episode.originalid]:
                showstats[episode.originalid][0].lastnormalize

        i = 1
        if not weeknumber:
            week = self.getlastcompletedweek()
            if not week: return previousnormalize
            weeknumber = week.weeknumber

        while i <= weeknumber:
            rankings = self.week(i).getepisoderanking()
            for episode in episodes:
                previousnormalize[episode.originalid]+=self.week(i).getepisodenormalize(episode,rankings)
            i+=1
        return previousnormalize

    def compileshows(self)->dict:
        """ Returns all shows as a series of dicts { showname: {Stats: ShowStatsObject, Weeks: [ EpisodeObjects ]}} """
        lookup = {showname:{"Stats":stats,"Weeks":[]} for showname,stats in self.showstats.shows.items()}
        for rankingsheet in self.weeks.values():
            rankedshows = rankingsheet.getepisoderanking()
            for episode in rankedshows:
                lookup[episode.originalid]['Weeks'].append(showepisode)  ## type: ignore If _id is not None, then _id is the value (str|int) of the originalid cell.
                                                          ## If _id is None, then showstats.originalid is garaunted to be an int
        return lookup
    
    def __eq__(self,other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex == other.recordstats.seasonindex
    
    def __lt__(self, other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex < other.recordstats.seasonindex
    
    def __gt__(self, other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex > other.recordstats.seasonindex
    
    def __repr__(self):
        return str(f"Season Record<{self.file.name}> {self.animeseason} {self.recordstats.version}")

class RecordStats():
    def __init__(self, record: SeasonRecord, stats: RecordStatsDict):
        self._record = record
        self.stats: RecordStatsDict = stats

    @property
    def season(self)->str:
        return self.stats.get("season")
    
    @property
    def year(self)->int:
        return self.stats.get("year")

    @property
    def version(self)->float:
        return self.stats.get("version")

    @property
    def animeseason(self)->anime.AnimeSeason:
        season, year = self.season, self.year
        return anime.AnimeSeason(self.season,self.year)
        
    @property
    def seasonindex(self)->float:
        return self.animeseason.seasonindex
        
    @property
    def record(self)->SeasonRecord:
        return self._record
    
class ShowStats():
    """ A Collection of Shows for a Season Record """
    def __init__(self, shows:ShowLookup, idvalue:str):
        self._shows = shows
        self.idvalue = idvalue

    def loadshows(self, shows: typing.Any):
        return

    @property
    def shows(self)->ShowLookup:
        return self._shows

    def getshowbyname(self, show: str)-> "ShowBase":
        """ Returns the Show Object for a show of the given name string.

        Returns the Show Object if name is in shows, else None.
        If more than one string is passed (positional args), returns a List of results (per this method).
        """
        if not isinstance(show,str):
            raise ValueError("Arguements to getshowbyname must be strings")
        shows = [s for s in self.shows.values() if (s.originalname and s.originalname.lower() == show.lower()) or (s.name and s.name.lower() == show.lower())]
        if shows:
            return shows[0]
        raise ValueError(f"Show '{show}' not found in ShowStats")
    
    def getshowsbyoriginalid(self, originalid: int)-> list["ShowBase"]:
        """ Returns a list of Show Objects for a show of the given originalid. """
        return [show for show in self.shows.values() if show.originalid == originalid]
    
class ShowBase:
    originalid = -1
    seasonid = None
    seriesid = None
    subseriesid = None
    watching = None
    include = None
    originalname = None
    name = ""
    channel = None
    day = None
    firstepisode = None
    group = None
    channelhomepage = None
    image = None
    rssfeedname = None
    hashtag = None
    website = None
    pv = None
    showboyid = None
    annid = None
    anilistid = None
    malid = None
    anidbid = None
    renewal = None
    lastepisode = None
    totalepisodes = None
    lastnormalize = None
    lastaverage = None
    lasthypelist = None
    notes = None
    lastseason = None
    
    
    def __init__(self,**kw):
        self.kw = kw
        if kw:
            extras = ", ".join(kw.keys())
            try: warnings.warn(f"Show received additional Keywords: {extras}",UserWarning)
            except: pass

    def to_dict(self)->dict:
        return dict(originalid = self.originalid, seasonid = self.seasonid, seriesid = self.seriesid, subseriesid = self.subseriesid,
                    watching = self.watching, include = self.include, originalname = self.originalname, name = self.name, channel = self.channel,
                 day = self.day, firstepisode = self.firstepisode, group = self.group, channelhomepage = self.channelhomepage, image = self.image,
                 rssfeedname = self.rssfeedname, hashtag = self.hashtag, website = self.website, pv = self.pv,
                 showboyid = self.showboyid,annid = self.annid,anilistid = self.anilistid, malid = self.malid, anidbid = self.anidbid,
                 renewal = self.renewal, lastepisode = self.lastepisode, totalepisodes = self.totalepisodes, lastnormalize = self.lastnormalize, lastaverage = self.lastaverage,
                 lasthypelist = self.lasthypelist, notes = self.notes, lastseason = self.lastseason)

    def __repr__(self):
        return str(self)
    def __str__(self):
        return f"Season Show: {self.name}"
    

class RankingSheet():
    def __init__(self, record: SeasonRecord, weeknumber: int, episodes: EpisodeDict, hypelist):
        self._record = record
        self.hypelist = hypelist
        self.episodes = episodes
        self.weeknumber = weeknumber

    @property
    def record(self):
        return self._record

    def getepisoderanking(self) -> typing.List["Episode"]:
        rankings=[episode for episode in self.episodes.values() if episode.rank is not None]
        return sorted(sorted(rankings,key=lambda episode:episode.name or ""),key=lambda episode: episode.rank)
    
    def getseasonranking(self) -> typing.List["Episode"]:
        shows = list(self.episodes.values())
        normalizedrankings = self.record.sumnormalize(shows,self.weeknumber)
        rankings = sorted(shows, key = lambda show: normalizedrankings[show.originalid])
        return rankings
    
    def gethypelistranking(self) -> typing.List["Episode"]:
        rankings=[episode for episode in self.episodes.values() if episode.hypelistrank is not None]
        rankings.sort(key=lambda episode:episode.name)
        rankings.sort(key=lambda episode: episode.hypelistrank if episode.hypelistrank else 10000)
        return rankings
    
    
    def getepisodenormalize(self,episode: "Episode", rankings: list["Episode"]|None = None)-> float:
        """ Returns the normalized value for the show's Ranking. """
        if not rankings:
            rankings = self.getepisoderanking()
        minrank = min(rankings, key = lambda ranking: ranking.rank).rank
        maxrank = max(rankings, key = lambda ranking: ranking.rank).rank
        BASE,CEIL = 0,1
        return BASE + ( (episode.rank - minrank) * (CEIL - BASE) ) / ( maxrank - minrank)
    
class Episode():
    def __init__(self, week:"RankingSheet", rank: int, show: ShowBase, date: str|None = None, episodenumber = None):
        self.week = week
        self.show = show
        self.rank = rank
        self.date = date
        self.episodenumber = episodenumber

    @property
    def name(self)->str:
        return self.show.name
    
    @property
    def originalid(self)->int:
        return self.show.originalid

    @property
    def hypelistrank(self)-> int|None:
        if self.week and self.week.hypelist:
            return self.week.hypelist.rank(self)

    @property
    def normalizedrank(self)-> float|None:
        return self.week.getepisodenormalize(self) if self.week else None

    def to_dict(self):
        return dict(week = self.week, rank = self.rank, date= self.date, episodenumber = self.episodenumber)

    def __repr__(self):
        return f"Episode {self.name or self.originalid}:{self.episodenumber}"