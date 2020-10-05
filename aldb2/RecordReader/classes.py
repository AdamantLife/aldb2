## Builtin
import csv
import itertools
import pathlib
import re
import warnings

## This Module
from aldb2.Anime import anime

## Custom Module
from alcustoms import excel, filemodules ## Extension of openpyxl
from alcustoms.excel import Tables



## EnhancedTable.todicts() keyfactory for converting Headers to attribute names
keyfactory = lambda key: key.lower().replace(" ","")

WBNAME = '''^(?:(?!~\$).)*?(?P<season>[a-zA-Z]+)\s*(?P<year>\d+)'''
WBNAMERE=re.compile(WBNAME)
## WBNAME[1:] -> Remove start-of-line marker
FILENAMERE = re.compile(f"""^__Record\s+{WBNAME[1:]}\s*.xlsx?""",re.IGNORECASE)
## WEEKRE is currently used on tables (which cannot have spaces) but accepts spaces for use with Workbook names
WEEKRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)\s*$""", re.IGNORECASE)
## See WEEKRE note
HYPERE = re.compile("""^Hype(?:\s|_)*Week(?:\s|_)*(?P<number>\d+)""", re.IGNORECASE)
HYPEHISTRE = re.compile("""^Hype_Week(?P<number>\d+)_PreviousWeek\s*$""", re.IGNORECASE)

def listvalidfilenames(dire):
    """ Compiles a list of all the validly named Record files (as pathlib.Path instances; does not garauntee that the files are correctly formatted) """
    dire = pathlib.Path(dire).resolve()
    if not dire.exists() or not dire.is_dir():
        raise ValueError("Invalid directory: must be a directory and must exist")
    return filemodules.iterdir_re(dire,FILENAMERE)

def extractseasonfromfilename(filename):
    res=WBNAMERE.search(str(filename))
    if res:
        season,year=res.group('season'),res.group('year')
        out=""
        if season:
            out+=season+" "
        if year: out+=year
        return anime.parseanimeseason_toobject(out)


class SeasonRecord():
    def __init__(self,file):
        self._file=file
        xlsx=self.xlsx=excel.load_workbook(filename=str(file),data_only=True)
        self._sheets={sheet:xlsx[sheet] for sheet in xlsx.sheetnames}
        self._recordstatssheet = None
        self._recordstats = None
        self._showstatssheet = None
        self._showstats = None
        tables = Tables.get_all_tables(xlsx)
        tables = {table.displayName:table for (ws,table) in tables}
        try:
            table = tables['RecordStats']
        except KeyError:
            table = RecordStats.parsesheet(self._sheets['Record Stats'])
        self._recordstats = RecordStats(table,self)
        try:
            table = tables['Stats']
        except KeyError:
            table = ShowStats.parsesheet(self._sheets['Show Stats'])
        self._showstats = ShowStats(table = table, record = self)
                
        self._weeks={}
        weektables = {int(WEEKRE.search(name).group("number")):table for name,table in tables.items() if WEEKRE.match(name)}
        hypetables = {int(HYPERE.search(name).group("number")):table for name,table in tables.items() if HYPERE.match(name)}
        historytables = {int(HYPEHISTRE.search(name).group("number")):table for name, table in tables.items() if HYPEHISTRE.match(name)}
        for week,table in weektables.items():
            hypetable = hypetables.get(week)
            if self.recordstats.version < 4:
                s=RankingSheetV1(table,hypetable,self)
            else:
                historytable = historytables.get(week)
                s = RankingSheetV4(table, hypetable, self, historytable)
            s.setshowstats(self.showstats.shows)
            self._weeks[week]=s
    @property
    def file(self):
        return self._file
    @property
    def sheets(self):
        return self._sheets
    @property
    def weeks(self):
        return self._weeks
    def week(self,weekname):
        return self.weeks[weekname]
    @property
    def recordstatssheet(self):
        return self._recordstatssheet
    @property
    def recordstats(self):
        return self._recordstats
    @property
    def showstatssheet(self):
        return self._showstatssheet
    @property
    def showstats(self):
        return self._showstats
    @property
    def animeseason(self):
        try:
            return self.recordstats.animeseason
        except:
            return None

    def close(self):
        self.xlsx.close()

    def getlastweek(self):
        weeks = [week for week in self.weeks.values() if week.shows]
        if not weeks: return None
        return weeks[0]

    def compileshows(self):
        """ Returns all shows as a series of dicts { showname: {Stats: ShowStatsObject, Weeks: [ EpisodeObjects ]}} """
        lookup = {showname:{"Stats":stats,"Weeks":[]} for showname,stats in self.showstats.shows.items()}
        for rankingsheet in self.weeks.values():
            rankedshows = rankingsheet.getepisoderanking()
            for showepisode in rankedshows:
                _id = showepisode.originalid
                if _id is None:
                    _id = self.showstats.getshowbyname(showepisode.name).originalid
                lookup[_id]['Weeks'].append(showepisode)
        return lookup

class RecordStats():
    def parsesheet(sheet):
        column = 1
        row = 1
        tableref = Tables.gettablesize(sheet,startcolumn = column, startrow = row)
        table = excel.EnhancedTable(worksheet = sheet, displayName = "RecordStats", ref = tableref)
        return table
    def __init__(self,table,record):
        self._table = table
        self._record = record
        ## todicts returns keys() at index 1 (also note that this should also only 
        ## return 1 actual row if the RecordStats is properly formatted)
        self.stats = {key.lower():v for key,v in self.table.todicts()[1].items()}
        

    @property
    def season(self):
        if "season" in self.stats and self.stats['season']:
            return self.stats['season']
        return extractseasonfromfilename(self.record.file).season
    @property
    def year(self):
        if "year" in self.stats and self.stats['year']:
            return self.stats['year']
        return extractseasonfromfilename(self.record.file).year

    @property
    def version(self):
        if "version" in self.stats and self.stats["version"] is not None:
            return float(self.stats['version'])

    @property
    def animeseason(self):
        try:
            return anime.AnimeSeason(self.season,self.year)
        except:
            return None

    @property
    def table(self):
        return self._table
    @property
    def record(self):
        return self._record

class ShowStats():
    SHOWIDVALUE = "SeriesID"
    MASTERIDVALUE = "originalid"
    ONAMEVALUE = "Original Name"
    NAMEVALUE = "Name"
    def load_masterstats(csvfile):
        """ Function for loading Stats from Master csv File (Rather than standard Excel Record) """
        with open(csvfile,'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return ShowStats(shows = list(reader), idvalue = MASTERIDVALUE)

    def __init__(self, table = None, record = None):
        self._table = table
        self.record = record
        shows = table.todicts(keyfactory = keyfactory)
        ## Remove headers
        headers = shows.pop(0)
        
        shows = {show[self.MASTERIDVALUE]:Show(self,**show) for show in shows if show[self.MASTERIDVALUE]}
        self._shows=shows
    @property
    def table(self):
        return self._table
    @property
    def shows(self):
        return self._shows
    def getshowbyname(self,*shows):
        """ Returns the Show Object for a show of the given name string.

        Returns the Show Object if name is in shows, else None.
        If more than one string is passed (positional args), returns a List of results (per this method).
        """
        if len(shows) > 1:
            return [self.getshowbyname(show) for show in shows]
        if len(shows) == 0:
            raise ValueError("getshowbyname requires at least one query")
        show = shows[0]
        if not isinstance(show,str):
            raise ValueError("Arguements to getshowbyname must be strings")
        shows = [show for show in self.shows.values() if show.originalname == show or show.name == show]
        if shows:
            return shows[0]
        ## For explicitness' sake
        return None

class Show():
    def __init__(self,statssheet, originalid, seasonid = None, seriesid = None, subseriesid = None,
                 watching = None, include = None, originalname = None, name = None, channel = None,
                 day = None, firstepisode = None, group = None, channelhomepage = None, image = None,
                 rssfeedname = None, hashtag = None, website = None, pv = None,
                 showboyid = None,annid = None,anilistid = None, malid = None, anidbid = None,
                 renewal = None, lastepisode = None, totalepisodes = None, lastnormalize = None, lastaverage = None,
                 lasthypelist = None, notes = None, lastseason = None, **kw):
        self.statssheet = statssheet
        self.originalid = originalid

        self.kw = kw
        if kw:
            extras = ", ".join(kw.keys())
            try: warnings.showwarning(f"Show received additional Keywords: {extras}",UserWarning)
            except: pass
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

        self.episodeurls=dict()
        self.seasonorder=list()

    @property
    def lastaverage(self):
        if not self.lastepisode: return 0
        return self.lastnormalize / self.lastepisode

    def setepisodeurls(self,*episodes):
        self.episodeurls={str(episode):episode for episode in episodes}
        ## build season order
        self.seasonorder=list()
        for episode in episodes:
            ## Can't use set() since it won't maintain order
            if episode.season and episode.season not in self.seasonorder:
                self.seasonorder.append(episode.season)

    def getepisodeurls(self):
        if self.seasonorder:
            episodesbyseason=[sorted([episode for episode in self.episodeurls.values() if episode.season==season],key=lambda episode: episode.number) for season in self.seasonorder]
            episodes=list(itertools.chain.from_iterable(episodesbyseason))
        else:
            episodes=sorted(self.episodeurls.values(),key=lambda episode: episode.number)
        return episodes

    def to_dict(self):
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

class HypeList():
    NAMEHEADER = "name"
    LASTHEADER = "lastlist"
    def __init__(self,table,week):
        self._table = table
        self.week = week

    @property
    def rows(self):
        ## First index is keys()
        return self.table.todicts(keyfactory = keyfactory)[1:]

    @property
    def table(self):
        return self._table

class HypeListV1(HypeList):
    """ HypeListV1:

        Used for Spreadsheet version prior to Version 4.

        Format:
            Last List           | Name              | Occurences
            -----------------------------------------------------
            Prev. Week Rank 1   | Curr. Week Rank 1 | Number of Prev. Occurences of Curr. Week Rank 1
            Prev. Week Rank 2   | Curr. Week Rank 2 | Number of Prev. Occurences of Curr. Week Rank 2
            ... etc

        When the table is read as a dict (using alcustoms.EnhancedTable.todicts()),the result is:
        [   ["Last List", "Name", "Occurences"], ## Table Keys
            {"Last List": "Prev. Week Rank 1", "Name": "Curr. Week Rank 1", "Occurences": "Number of Prev. Occurences of Curr. Week Rank 1"},
            {"Last List": "Prev. Week Rank 2", "Name": "Curr. Week Rank 2", "Occurences": "Number of Prev. Occurences of Curr. Week Rank 2"},
            ... etc
            ]

        Current Hypelist is therefore row comprehension for "Name" where the value is not Blank (None)
        Previous Hypelist is likewise row comprehension for "Last List" where the value is not Blank (None)
    """
    def __init__(self, table, week):
        super().__init__(table, week)

    @property
    def hypelist(self):
        return[row[self.NAMEHEADER] for row in self.rows if row[self.NAMEHEADER]]
        
    @property
    def history(self):
        return [row[self.LASTHEADER] for row in self.rows if row[self.LASTHEADER]]

    def rank(self,show):
        """ Returns the Rank on the current HypeList of the given show (None if the show is not on the hypelist) """
        if isinstance(show,Episode):
            show = show.name
        if show in self.hypelist: return self.hypelist.index(show)+1
        return None

class HypeListv4(HypeList):
    """ HypelistV4:

        Used for Spreadsheet Version 4 (current version). In this version, Hypelist and Hypelist
            History are split between two tables.

        Hypelist Format:
            OriginalID  | Name          | Occurences
            -------------------------------------------------------------------
            Rank 1 OID  | Rank 1 Name   | Number of Prev. Occurences of Rank 1
            Rank 2 OID  | Rank 2 Name   | Number of Prev. Occurences of Rank 2
            ... etc

        Hyplist History Format:
            OriginalID              | Name                      | This Week's Rank
            ----------------------------------------------------------------------------------------
            Prev. Week Rank 1 OID   | Prev. Week Rank 1 Name    | Episode Rank of Prev. Week Rank 1
            Prev. Week Rank 2 OID   | Prev. Week Rank 2 Name    | Episode Rank of Prev. Week Rank 2
            ... etc

        
    """
    OIDHEADER = "originalid"
    NAMEHEADER = "name" 
    LASTHEADER = None

    def __init__(self, table, week, historytable):
        super().__init__(table, week)
        self._historytable = historytable

    @property
    def hypelist(self):
        return self.rows

    @property
    def history(self):
        return self._historytable.todicts(keyfactory = keyfactory)[1:]

    def rank(self, show):
        if isinstance(show, Episode):
            show = int(show.originalid)
        if isinstance(show, int):
            show = str(show)
            header = self.OIDHEADER
        elif isinstance(show, str):
            header = self.NAMEHEADER
        for i,row in enumerate(self.hypelist, start=1):
            if row[header]==show:
                return i
        return None

class RankingSheet():
    RANKHEADER="rank"
    NEWRANKHEADER="newrank"
    EPISODEHEADER="episodes"
    HYPEOCCURENCEHEADER="hypelistoccurences"
    WEEKRE=re.compile('''.*week\s*(?P<week>\d+)''',re.IGNORECASE)
    def getheaderindex(columns,header):
            if isinstance(header,list):
                header=[head for head in header if head in columns]
                if not header: return None
                header=min(header,key=lambda head: columns.index(head.lower()))
            if isinstance(header,str):
                if header.lower() not in columns: return None
                return columns.index(header.lower())+1
            return None

    def __init__(self,table,hypelist, record):
        self._table = table
        self._record = record
        self.weeknumber=int(WEEKRE.search(table.displayName).group("number"))
        self.hypelist = None

        self.shows=dict()
        ## Index-0 of todicts is keys()
        shows = self.table.todicts(keyfactory = keyfactory)[1:]
        for show in shows:
            originalid = show.get("originalid",None)
            seasonid = show.get("seasonid",None)
            name = show['name']
            ## For old records
            if not originalid and not seasonid:
                ## Getting showstats preemptively
                showstat = None
                if name:
                    showstat = self.record.showstats.getshowbyname(name)
                ## Check for old alias first
                originalid = show.get("seriesid",None)
                ## Fill in if necessary/possible
                if showstat:
                    if not originalid:
                        originalid = showstat.originalid
                    if not seasonid:
                        seasonid = showstat.seasonid

            
            rank = show[self.RANKHEADER]

            ranktotal = show[self.NEWRANKHEADER]
            episode = show[self.EPISODEHEADER]
            hypelistocc = show[self.HYPEOCCURENCEHEADER]
            if name:
                show = Episode(originalid=originalid,seasonid = seasonid, name=name,week=self,
                                         rank=rank,ranktotal=ranktotal,episode=episode,
                                         hypelistocc=hypelistocc)
                self.shows[name] = show

    @property
    def table(self):
        return self._table
    @property
    def record(self):
        return self._record

    def setshowstats(self,showstats):
        for show,stats in showstats.items():
            if isinstance(show,int):
                show = stats.name
            if show in self.shows:
                thisshow = self.shows[show]
                thisshow.showstats = stats
                if thisshow.originalid is None:
                    thisshow.originalid = stats.originalid

    def getepisoderanking(self):
        rankings=[show for show in self.shows.values() if show.rank is not None]
        return sorted(sorted(rankings,key=lambda show:show.name),key=lambda show: show.rank)
    def getseasonranking(self):
        rankings=[show for show in self.shows.values() if show.ranktotal is not None]
        return sorted(sorted(rankings,key=lambda show:show.name),key=lambda show: show.ranktotal)
    def gethypelistranking(self):
        rankings=[show for show in self.shows.values() if show.hypelistrank is not None]
        return sorted(sorted(rankings,key=lambda show:show.name),key=lambda show: show.hypelistrank)
    def getepisodenormalize(self,episode):
        """ Returns the normalized value for the show's Ranking. """
        rankings = self.getepisoderanking()
        minrank = min(rankings, key = lambda ranking: ranking.rank).rank
        maxrank = max(rankings, key = lambda ranking: ranking.rank).rank
        BASE,CEIL = 0,1
        return BASE + ( (episode.rank - minrank) * (CEIL - BASE) ) / ( maxrank - minrank)

class RankingSheetV1(RankingSheet):
    """ Ranking Sheet for Record Versions prior to 4"""
    HYPELIST = HypeListV1
    def __init__(self, table, hypelist, record):
        super().__init__(table, hypelist, record)

        if hypelist:
            self.hypelist = self.HYPELIST(hypelist,self)

class RankingSheetV4(RankingSheet):
    """ Ranking Sheet for Record Version 4 (current version) """
    HYPELIST = HypeListv4
    def __init__(self,table,hypelist, record, hypehistory):
        super().__init__(table, hypelist, record)
        if hypelist:
            self.hypelist = self.HYPELIST(hypelist, self, hypehistory)

class Episode():
    def __init__(self,originalid,name,week,rank,ranktotal,episode,hypelistocc=0,seasonid = None):
        self.originalid = originalid
        self.seasonid = seasonid
        self.name=name
        self.week = week
        self.rank=rank
        self.ranktotal=ranktotal
        self.episodenumber=episode
        self.hypelistocc=hypelistocc

    @property
    def hypelistrank(self):
        if self.week.hypelist:
            return self.week.hypelist.rank(self)

    @property
    def normalizedrank(self):
        return self.week.getepisodenormalize(self)

    def to_dict(self):
        return dict(originalid = self.originalid, name = self.name, week = self.week, rank = self.rank, ranktotal = self.ranktotal, episodenumber = self.episodenumber, hypelistocc = self.hypelistocc, hypelistrank = self.hypelistrank)

    def __repr__(self):
        return f"Episode {self.name}:{self.episodenumber}"