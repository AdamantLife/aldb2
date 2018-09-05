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



## EnhancedTable.todicts() keyfactory for converting Headers to attribute names
keyfactory = lambda key: key.lower().replace(" ","")

WBNAME = '''^(?:(?!~\$).)*?(?P<season>[a-zA-Z]+)\s*(?P<year>\d+)'''
WBNAMERE=re.compile(WBNAME)
## WBNAME[1:] -> Remove start-of-line marker
FILENAMERE = re.compile(f"""^__Record\s+{WBNAME[1:]}\s*.xlsx?""",re.IGNORECASE)
## WEEKRE is currently used on tables (which cannot have spaces) but accepts spaces for use with Workbook names
WEEKRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)""", re.IGNORECASE)
## See WEEKRE note
HYPERE = re.compile("""^Hype(?:\s|_)*Week(?:\s|_)*(?P<number>\d+)""", re.IGNORECASE)

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
        print(out)
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
        tables = excel.get_all_tables(xlsx)
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
        self._showstats = self._showstats=ShowStats(table = table, record = self)
                
        self._weeks={}
        weektables = {int(WEEKRE.search(name).group("number")):table for name,table in tables.items() if WEEKRE.match(name)}
        hypetables = {int(HYPERE.search(name).group("number")):table for name,table in tables.items() if HYPERE.match(name)}
        for week,table in weektables.items():
            hypetable = hypetables.get(week)
            s=RankingSheet(table,hypetable,self)
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
        tableref = excel.gettablesize(sheet,startcolumn = column, startrow = row)
        table = excel.EnhancedTable(worksheet = sheet, displayName = "RecordStats", ref = tableref)
        return table
    def __init__(self,table,record):
        self._table = table
        self._record = record
        ## todicts returns keys() at index 1 (also note that this should also only 
        ## return 1 actual row if the RecordStats is properly formatted)
        self.stats = {key.lower():v for key,v in self.table.todicts()[1].items()}
        self.season,self.year = None,None
        if "season" in self.stats:
            self.season = self.stats['season']
        if "year" in self.stats:
            self.year = self.stats['year']

        if not self.season or not self.year:
            season = extractseasonfromfilename(self.record.file)
            if not self.season: self.season = season.season
            if not self.year: self.year = season.year

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

    def __init__(self, table = None, record = None, *lookupvalues):
        self._table = table
        self.record = record
        shows = table.todicts(keyfactory = keyfactory)
        ## Remove headers
        headers = shows.pop(0)
        lookupvalue = None
        for lookup in lookupvalues:
            klookup = keyfactory(lookup)
            if klookup in headers:
                lookupvalue = klookup
                break
        if not lookupvalue:
            for lookup in [self.SHOWIDVALUE,self.MASTERIDVALUE,self.NAMEVALUE,self.ONAMEVALUE]:
                klookup = keyfactory(lookup)
                if klookup in headers:
                    lookupvalue = klookup
                    break
        if not lookupvalue:
            raise ValueError("Could not determine lookup value for Show Stats")
        ## check for originalid (required)
        if "originalid" not in headers:
            for show in shows: show['originalid'] = show[lookupvalue]
        shows = {show[lookupvalue]:Show(self,**show) for show in shows if show[lookupvalue]}
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

class RankingSheet():
    RANKHEADER="rank"
    NEWRANKHEADER="newrank"
    EPISODEHEADER="totalepisodes"
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
        if hypelist:
            self.hypelist = HypeList(hypelist,self)
        else: self.hypelist = None
        #print(self.weeknumber,self.hypelist)

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
            hypelistrank = None
            if name:
                show = Episode(originalid=originalid,seasonid = seasonid, name=name,week=self,
                                         rank=rank,ranktotal=ranktotal,episode=episode,
                                         hypelistocc=hypelistocc)
                self.shows[name] = show
            if self.hypelist:
                show.hypelistrank = self.hypelist.rank(show)
                if show.hypelistrank:
                    show.hypelistocc += 1
        #if self.hypelist:
        #    print([(show,show.hypelistrank) for show in self.shows.values() if self.hypelist.rank(show)])

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

class HypeList():
    NAMEHEADER = "name"
    LASTHEADER = "lastlist"
    def __init__(self,table,week):
        self._table = table
        self.week = week

        ## First index is keys()
        rows = self.table.todicts(keyfactory = keyfactory)[1:]
        self.hypelist = [row[self.NAMEHEADER] for row in rows if row[self.NAMEHEADER]]
        #print("Full Hypelist: ", self.hypelist)
        self.history = [row[self.LASTHEADER] for row in rows if row[self.LASTHEADER]]

    @property
    def table(self):
        return self._table

    def rank(self,show):
        """ Returns the Rank on the current HypeList of the given show (None if the show is not on the hypelist) """
        if isinstance(show,Episode):
            show = show.name
        if show in self.hypelist: return self.hypelist.index(show)+1
        return None


class Episode():
    def __init__(self,originalid,name,week,rank,ranktotal,episode,hypelistocc=0,hypelistrank=None, seasonid = None):
        self.originalid = originalid
        self.seasonid = seasonid
        self.name=name
        self.week = week
        self.rank=rank
        self.ranktotal=ranktotal
        self.episodenumber=episode
        self.hypelistocc=hypelistocc
        self.hypelistrank=hypelistrank

    @property
    def normalizedrank(self):
        return self.week.getepisodenormalize(self)

    def to_dict(self):
        return dict(originalid = self.originalid, name = self.name, week = self.week, rank = self.rank, ranktotal = self.ranktotal, episodenumber = self.episodenumber, hypelistocc = self.hypelistocc, hypelistrank = self.hypelistrank)

    def __repr__(self):
        return f"Episode {self.name}:{self.episodenumber}"