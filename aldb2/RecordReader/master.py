""" aldb2.RecordReader.master

    This module is used to compile and load compiled "master" records.
    These records transcribe all information from SeasonRecords into minimally-formatted CSV files.
    It produces two types of files: masterstats and masterweeks.
    A masterstats csv file compiles SeasonRecord.stats information
    The masterweeks csv file compiles all weeks rankings into a single file.
"""

## Builtin
import csv
import pathlib
import warnings

## This module
from aldb2.Anime import anime
from aldb2.RecordReader import classes

from alcustoms.methods import isiterable, testfileobj

root = pathlib.Path.cwd().resolve()
DEFAULTSTATFILE = (root / "master_stats.csv").resolve()
DEFAULTEPISODEFILE = (root / "master_episodes.csv").resolve()
del root

def load_masterstats(file):
    """ Loads a masterstats csv file """
    file = testfileobj(file)
    with open(file,'r', encoding = "utf-8") as f:
        reader = csv.DictReader(f)
        seasons = list(reader)
    return [MasterStat(**season) for season in seasons]

def save_masterstats(output,file):
    """ Saves a masterstats file with the given list of MasterStat objects """
    file = pathlib.Path(file).resolve()
    if not isiterable(output) or not all(isinstance(obj,MasterStat) for obj in output):
        raise ValueError("output must be a list of MasterStat objects")
    with open(file,'w', newline = "", encoding = "utf-8") as f:
        fieldnames = MasterStat(None,None).to_dict().keys()
        writer = csv.DictWriter(f,fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows([stat.to_dict() for stat in output])

class MasterStat(classes.Show):
    def list_from_SeasonRecord(seasonrecord:classes.SeasonRecord):
        """ Creates a list of MasterStats from the SeasonRecord's ShowStats """
        stats = list(seasonrecord.showstats.shows.values())
        stats = [stat.to_dict() for stat in stats]
        seasonindex = seasonrecord.recordstats.animeseason.seasonindex
        for stat in stats:
            stat["seasonindex"] = seasonindex
        return [MasterStat(**stat) for stat in stats]
    def __init__(self, originalid, seasonindex, seasonid = None, watching = None, include = None, originalname = None, name = None,
                 channel = None, day = None, firstepisode = None, group = None,
                 channelhomepage = None, image = None, rssfeedname = None, hashtag = None, website = None, pv = None,
                 showboyid = None, annid = None, anilistid = None, malid = None, anidbid = None,
                 renewal = None, lastepisode = None, totalepisodes = None, lastnormalize = None, lastaverage = None, lasthypelist = None,
                 notes = None, lastseason = None, **kw):
        super().__init__(statssheet= None, originalid = originalid, seasonid = seasonid, 
                                watching = watching, include = include, originalname = originalname, name = name, channel = channel, day = day, firstepisode = firstepisode,
                                group = group, channelhomepage = channelhomepage, image = image, rssfeedname = rssfeedname, hashtag = hashtag, website = website, pv = pv,
                                showboyid = showboyid, annid = annid, anilistid = anilistid, malid = malid, anidbid = anidbid,
                                notes = notes, **kw)
        self.seasonindex = seasonindex

    def to_dict(self):
        base = super().to_dict()
        for stat in ["renewal", "lastepisode","totalepisodes", "lastnormalize", "lastaverage", "lasthypelist"]:
            del base[stat]
        base['seasonindex'] = self.seasonindex
        return base

def load_masterepisodes(file):
    """ Loads a masterepisodes csv file """
    file = testfileobj(file)
    with open(file,'r', encoding = "utf-8") as f:
        reader = csv.DictReader(f)
        seasons = list(reader)
    return [MasterEpisode(**season) for season in seasons]

def save_masterepisodes(output,file):
    """ Saves a masterepisodes file with the given list of MasterEpisode objects """
    file = pathlib.Path(file).resolve()
    if not isiterable(output) or not all(isinstance(obj,MasterEpisode) for obj in output):
        raise ValueError("output must be a list of MasterStat objects")
    with open(file,'w', newline = "", encoding = "utf-8") as f:
        fieldnames = MasterEpisode(None,None,1.0,None,None,None,None).to_dict().keys()
        writer = csv.DictWriter(f,fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows([stat.to_dict() for stat in output])

class MasterEpisode():
    """ The Master Ranking Sheet is a bit different from the normal Ranking Sheet """
    def list_from_SeasonRecord(seasonrecord:classes.SeasonRecord):
        """ Converts a SeasonRecord into a list of MasterEpisodes.
        
        This function cannot take an Episode object directly because it needs knowledge of the whole scope of the SeasonRecord.
        """
        season = seasonrecord.recordstats.animeseason
        out = []
        for week in seasonrecord.weeks.values():
            for episode in week.shows.values():
                if episode.rank:
                    out.append(MasterEpisode(seasonid = episode.seasonid, originalid = episode.originalid, seasonindex = season.seasonindex, week = week.weeknumber, rank = episode.rank, episodenumber = episode.episodenumber, hypelistrank = episode.hypelistrank))
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



def compile_directory(directory, statsfile = None, episodesfile = None, recurse = False):
    """ Compiles a directory of SeasonRecords into masterstats and masterepisodes files
    
        statsfile and episodesfile should be valid filename paths if they are provided.
        If not provided, they will be the module defaults (in the current work directory).
        If recurse is True, will search each subdirectory for SeasonRecords (default is False).
    """
    directory = testfileobj(directory)
    if not directory.is_dir():
        raise ValueError("directory must a directory")
    if statsfile is None:
        statsfile = DEFAULTSTATFILE
    if episodesfile is None:
        episodesfile = DEFAULTEPISODEFILE

    outstats = list()
    outepisodes = list()

    def check_directory(directory):
        recordfiles = classes.listvalidfilenames(directory)

        ## Due to the potential memory overhead, we'll be doing records One-at-a-time (so we can close the file afterwards)
        for file in recordfiles:
            print(file)
            record = classes.SeasonRecord(file)
            ## Old versions of RecordReader (pre-aldb2) used the OriginalID instead of the SeasonID
            ## SeasonID is preferred in aldb2, so we're going to attempt to find and update the seasonid
            serieslookup = MasterStat.list_from_SeasonRecord(record)
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
        save_masterstats(outstats, statsfile)
    if episodesfile:
        save_masterepisodes(outepisodes, episodesfile)

def compile_firstepisodes(directory, output, recurse = False):
    results = []
    for record in classes.SeasonRecord.load_directory(directory, recurse = recurse):
        if record.recordstats.version < 3:
            continue
        for week in record.weeks.values():
            week: classes.RankingSheetV3
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
