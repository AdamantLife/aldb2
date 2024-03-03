""" aldb2.RecordReader.master

    This module is used to compile and load compiled "master" records.
    These records transcribe all information from SeasonRecords into minimally-formatted CSV files.
    It produces two types of files: mastershows and masterweeks.
    A mastershows csv file compiles SeasonRecord.stats information
    The masterweeks csv file compiles all weeks rankings into a single file.
"""

## Builtin
import csv
import collections
import datetime
import pathlib
import typing
import warnings

## This module
from aldb2.Anime import anime
from aldb2.RecordReader.classes import ShowStats, ShowBase, SeasonRecord, ShowLookup
from aldb2.RecordReader import excel

root = pathlib.Path.cwd().resolve()
DEFAULTSTATFILE = (root / "master_stats.csv").resolve()
DEFAULTEPISODEFILE = (root / "master_episodes.csv").resolve()
del root

def load_mastershows(file):
    """ Loads a mastershows csv file """
    file = pathlib.Path(file).resolve()
    if not file.exists() or not file.is_file():
        raise FileNotFoundError(file)
    with open(file,'r', encoding = "utf-8") as f:
        reader = csv.DictReader(f)
        seasons = list(reader)
    return [MasterShow.parseshowfromcsv(season) for season in seasons]

def save_mastershows(output,file):
    """ Saves a mastershows file with the given list of MasterShow objects """
    file = pathlib.Path(file).resolve()
    if not all(isinstance(obj,MasterShow) for obj in output):
        raise ValueError("output must be a list of MasterShow objects")
    with open(file,'w', newline = "", encoding = "utf-8") as f:
        fieldnames = MasterShow(0,None).to_dict().keys()
        writer = csv.DictWriter(f,fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows([stat.to_dict() for stat in output])

class MasterShowStats(ShowStats):
    MASTERIDVALUE = "originalid"
    @staticmethod
    def load_masterstats(csvfile):
        """ Function for loading Shows from Master csv File (Rather than standard Excel Record) """
        with open(csvfile,'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            _shows = list(reader)
            shows: ShowLookup = collections.OrderedDict()
            for show in _shows:
                if (_id := show.get(MasterShowStats.MASTERIDVALUE)):
                    shows[_id] = MasterShow.parseshowfromcsv(show)
            return MasterShowStats(shows = shows, idvalue = MasterShowStats.MASTERIDVALUE)
    
    def __init__(self, shows: ShowLookup, idvalue: str):
        super().__init__(shows, idvalue)

    def loadshows(self, shows: list[dict[str, typing.Any]]):
        self._shows = {show[self.idvalue.lower()]:MasterShow(**show) for show in shows if show[self.idvalue.lower()]}

class MasterShow(ShowBase):
    @staticmethod
    def list_from_SeasonRecord(seasonrecord:SeasonRecord):
        """ Creates a list of MasterShows from the SeasonRecord's ShowStats """
        stats = list(seasonrecord.showstats.shows.values())
        stats = [stat.to_dict() for stat in stats]
        seasonindex = seasonrecord.recordstats.animeseason.seasonindex
        for stat in stats:
            stat["seasonindex"] = seasonindex
        return [MasterShow(**stat) for stat in stats]
    
    @staticmethod
    def parseshowfromcsv(show: dict[str|typing.Any, str|typing.Any])-> "MasterShow":
        """ Parses a show from a csv file """
        originalid = show.get("originalid")
        if not originalid:
            raise ValueError("Show must have an originalid")
        originalid = int(originalid)
        seasonid = show.get("seasonid", None)
        if seasonid is not None: seasonid = int(seasonid)
        seriesid = show.get("seriesid")
        if seriesid is not None: seriesid = int(seriesid)
        subseriesid = show.get("subseriesid")
        if subseriesid is not None: subseriesid = int(subseriesid)
        watching = show.get("watching")
        if watching is not None: watching = bool(watching)
        include = show.get("include")
        if include is not None: include = bool(include)
        originalname = show.get("originalname")
        name = show.get("name")
        channel = show.get("channel")
        day = show.get("day")
        firstepisode = show.get("firstepisode")
        if firstepisode is not None: firstepisode = datetime.datetime.fromisoformat(firstepisode)
        group = show.get("group")
        if group is not None: group = int(group)
        channelhomepage = show.get("channelhomepage")
        rssfeedname = show.get("rssfeedname")
        hashtag = show.get("hashtag")
        website = show.get("website")
        pv = show.get("pv")
        showboyid = show.get("showboyid")
        annid = show.get("annid")
        anilistid = show.get("anilistid")
        malid = show.get("malid")
        anidbid = show.get("anidbid")
        renewal = show.get("renewal")
        if renewal is not None: renewal = bool(renewal)
        lastepisode = show.get("lastepisode")
        if lastepisode is not None: lastepisode = int(lastepisode)
        totalepisodes = show.get("totalepisodes")
        if totalepisodes is not None: totalepisodes = int(totalepisodes)
        lastnormalize = show.get("lastnormalize")
        if lastnormalize is not None: lastnormalize = float(lastnormalize)
        lasthypelist = show.get("lasthypelist")
        if lasthypelist is not None: lasthypelist = int(lasthypelist)
        notes = show.get("notes")
        lastseason = show.get("lastseason")
        seasonindex = show.get("seasonindex")
        if seasonindex is not None: seasonindex = int(seasonindex)
        return MasterShow(originalid, seasonid, seriesid, subseriesid, watching, include, originalname, name, channel, day, firstepisode, group, channelhomepage, rssfeedname, hashtag, website, pv, showboyid, annid, anilistid, malid, anidbid, renewal, lastepisode, totalepisodes, lastnormalize, lasthypelist, notes, lastseason, seasonindex)
    
    def __init__(self, originalid: int, seasonid: int|None = None, seriesid: int|None = None, subseriesid: int|None = None,
                 watching: bool|None = None, include: bool|None = None, originalname: str|None = None, name: str|None = None, channel: str|None = None,
                 day: str|None = None, firstepisode: str|datetime.datetime|None = None, group: int|None = None, channelhomepage: str|None = None,
                 rssfeedname: str|None = None, hashtag: str|None = None, website: str|None = None, pv: str|None = None,
                 showboyid: str|None = None, annid: str|None = None,anilistid: str|None = None, malid: str|None = None, anidbid: str|None = None,
                 renewal: bool|None = None, lastepisode: int|None = None, totalepisodes: int|None = None, lastnormalize: float|None = None,
                 lasthypelist: int|None = None, notes: str|None = None, lastseason: str|None = None, seasonindex: int|None = None, **kw):
        super().__init__(**kw)

        self.originalid = originalid
        self.seasonid = seasonid
        self.seriesid = seriesid
        self.subseriesid = subseriesid
        if not watching: watching = False
        if not include: include = False
        self.watching = bool(watching)
        self.include = bool(include)
        self.originalname = originalname
        self.name = name
        self.channel = channel
        self.day  = day
        self.firstepisode = firstepisode
        if group: group = int(group)
        self.group = group
        self.channelhomepage = channelhomepage
        self.rssfeedname = rssfeedname
        self.hashtag = hashtag
        self.website = website
        self.pv = pv
        self.showboyid = showboyid
        self.annid = annid
        self.anilistid = anilistid
        self.malid = malid
        self.anidbid = anidbid
        self.image = None
        if not renewal: renewal = False
        self.renewal = bool(renewal)
        if not lastepisode: lastepisode = 0
        self.lastepisode = int(lastepisode)
        if not totalepisodes: totalepisodes = -1
        self.totalepisodes = int(totalepisodes)
        if not lastnormalize: lastnormalize = 0
        self.lastnormalize = float(lastnormalize)
        if not lasthypelist: lasthypelist = 0
        self.lasthypelist = int(lasthypelist)
        self.lastseason = lastseason
        self.notes = notes
        self.seasonindex = seasonindex

    def to_dict(self):
        base = super().to_dict()
        for stat in ["renewal", "lastepisode","totalepisodes", "lastnormalize", "lastaverage", "lasthypelist"]:
            if stat in base:
                del base[stat]
        base['seasonindex'] = self.seasonindex
        return base

def load_masterepisodes(file):
    """ Loads a masterepisodes csv file """
    file = pathlib.Path(file).resolve()
    if not file.exists() or not file.is_file():
        raise FileNotFoundError(file)
    with open(file,'r', encoding = "utf-8") as f:
        reader = csv.DictReader(f)
        seasons = list(reader)
    return [MasterEpisode(**season) for season in seasons]

def save_masterepisodes(output,file):
    """ Saves a masterepisodes file with the given list of MasterEpisode objects """
    file = pathlib.Path(file).resolve()
    if not all(isinstance(obj,MasterEpisode) for obj in output):
        raise ValueError("output must be a list of MasterShow objects")
    with open(file,'w', newline = "", encoding = "utf-8") as f:
        fieldnames = MasterEpisode(None,None,1.0,None,None,None,None).to_dict().keys()
        writer = csv.DictWriter(f,fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows([stat.to_dict() for stat in output])

class MasterEpisode():
    """ The Master Ranking Sheet is a bit different from the normal Ranking Sheet """
    @staticmethod
    def list_from_SeasonRecord(seasonrecord:SeasonRecord):
        """ Converts a SeasonRecord into a list of MasterEpisodes.
        
        This function cannot take an Episode object directly because it needs knowledge of the whole scope of the SeasonRecord.
        """
        season = seasonrecord.recordstats.animeseason
        out = []
        for week in seasonrecord.weeks.values():
            for episode in week.episodes.values():
                if episode.rank:
                    seasonid = -1
                    if hasattr(episode, "seasonid"):
                        seasonid = getattr(episode,"seasonid", -1)
                    out.append(MasterEpisode(seasonid = seasonid, originalid = episode.originalid, seasonindex = season.seasonindex, week = week.weeknumber, rank = episode.rank, episodenumber = episode.episodenumber, hypelistrank = episode.hypelistrank))
        return out

    def __init__(self,seasonid, originalid, seasonindex, week, rank, episodenumber, hypelistrank = None, **kw):
        self.seasonid = seasonid
        self.originalid = originalid
        self.seasonindex = seasonindex
        self.animeseason = anime.parseanimeseason_toobject(seasonindex)
        self.week = week
        self.rank = rank
        self.episodenumber = episodenumber
        self.hypelistrank = hypelistrank
        
        if kw:
            try:
                kws = ", ".join(kw.keys())
                warnings.warn(f"MasterEpisode received additional Keywords: {kws}")
            except: pass

    def to_dict(self):
        return dict(seasonid = self.seasonid, originalid = self.originalid, seasonindex = self.seasonindex, week = self.week, rank = self.rank, episodenumber = self.episodenumber, hypelistrank = self.hypelistrank)



def compile_excel_directory(directory, statsfile = None, episodesfile = None, recurse = False):
    """ Compiles a directory of ExcelSeasonRecords into mastershows and masterepisodes files
    
        statsfile and episodesfile should be valid filename paths if they are provided.
        If not provided, they will be the module defaults (in the current work directory).
        If recurse is True, will search each subdirectory for SeasonRecords (default is False).
    """
    directory = pathlib.Path(directory).resolve()
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(directory)
    if statsfile is None:
        statsfile = DEFAULTSTATFILE
    if episodesfile is None:
        episodesfile = DEFAULTEPISODEFILE

    outstats = list()
    outepisodes = list()

    def check_directory(directory: pathlib.Path):
        recordfiles = excel.listvalidfilenames(directory)

        ## Due to the potential memory overhead, we'll be doing records One-at-a-time (so we can close the file afterwards)
        for file in recordfiles:
            
            record = excel.ExcelSeasonRecord(file)
            ## Old versions of RecordReader (pre-aldb2) used the OriginalID instead of the SeasonID
            ## SeasonID is preferred in aldb2, so we're going to attempt to find and update the seasonid
            serieslookup = MasterShow.list_from_SeasonRecord(record)
            print("\tShows:",len(serieslookup))
            outstats.extend(serieslookup)
            serieslookup = {show.originalid:show for show in serieslookup}

            episodes = MasterEpisode.list_from_SeasonRecord(record)
            for episode in episodes:
                if not episode.seasonid and episode.originalid in serieslookup:
                    episode.seasonid = serieslookup[episode.originalid].seasonid
            print("\tEpisodes:", len(episodes))
            outepisodes.extend(episodes)
            record.xlsx.close()
        
    def recursion(directory):
        check_directory(directory)
        for child in directory.iterdir():
            if child.is_dir(): recursion(child)
    
    if recurse: recursion(directory)
    else: check_directory(directory)

    if statsfile:
        save_mastershows(outstats, statsfile)
    if episodesfile:
        save_masterepisodes(outepisodes, episodesfile)

def compile_excel_firstepisodes(directory, output, recurse = False):
    results = []
    for record in excel.ExcelSeasonRecord.load_directory(directory, recurse = recurse):
        if record.recordstats.version < 3:
            continue
        for week in record.weeks.values():
            if not isinstance(week, excel.RankingSheetV3): continue
            if not week.rounduptable: continue
            rows = week.rounduptable.todicts()[1:]
            seasonindex = record.recordstats.animeseason.seasonindex
            for row in rows:
                if row["OriginalID"]:
                    row['SeasonIndex'] = seasonindex
                    results.append(row)

    with open(output, 'w', encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["SeasonIndex", "OriginalID", "Show", "Animation", "Art/Aesthetics", "Character/Story Investment", "Plot/World Building"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return

def compile_excel_lastepisodes(directory, output, recurse = False):
    results = {}
    for record in excel.ExcelSeasonRecord.load_directory(directory, recurse = recurse):
        season = record.recordstats.animeseason.seasonindex
        last_week = max(record.weeks.keys())
        shows = len(record.weeks[last_week].episodes)
        while not shows and last_week > 0:
            last_week -= 1
            shows = len(record.weeks[last_week].episodes)
        if not shows:
            print(f"Season {season} has no shows")
            continue
        last_week = record.weeks[last_week]
        print(record.recordstats.animeseason.seasonindex, last_week.weeknumber, len(record.weeks), shows)
        for show in last_week.episodes.values():
            if show.originalid:
                if show.originalid not in results or results[show.originalid]["SeasonIndex"] < season:
                    results[show.originalid] = show.to_dict()
                    results[show.originalid]["SeasonIndex"] = season
    results = list(results.values())
    

    with open(output, 'w', encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["SeasonIndex", "originalid", "name", "ranktotal"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return