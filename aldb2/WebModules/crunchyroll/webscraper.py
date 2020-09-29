## Builtin
import bs4
import csv
import json
import os
import os.path
import re
import traceback
import urllib.request as urequest
## This Module
from AnimeDatabase.core import modules as coremodules
from AnimeDatabase.core import sql
from AnimeDatabase import webmodules

CR_URL=r"http://www.crunchyroll.com"

CR_RATINGCOUNTRE=re.compile('''\((?P<count>\d+)\)''')
CR_EPISODENUMBERRE=re.compile('''Episode (?P<number>\w+)''')
CR_EPISODERATINGRE=re.compile('''Rating.SetStars\((?P<rating>[\w.]+)''')
CR_SPACINGRE=re.compile('''(\s{2,})''')

class CREpisode():
    '''Represent an Episode according to data from Crunchyroll'''
    KEYS=['url','season','number','title','rating','blurb']
    def __init__(self,url,season=None,number=None,title="",rating=None,blurb=""):
        self.url=url
        self.season=season
        self.number=number
        self.title=title
        self.rating=rating
        self.blurb=blurb
    def getinfo(self):
        info=getepisodeinfo(self.url)
        self.rating,self.blurb=info['rating'],info['blurb']
    def __getitem__(self,key):
        if key in self.KEYS:
            return getattr(self,key)
        raise KeyError("Invalid Key")
    def __setitem__(self,key,value):
        if key in self.KEYS:
            return setattr(self,key,value)
        raise KeyError("Invalid Key")
    def __delitem__(self,key):
        if key in self.KEYS:
            setattr(self,key,None)
            return
        raise KeyError("Invalid Key")
    def keys(self):
        return self.KEYS
    def values(self):
        return [getattr(self,key) for key in self.KEYS]
    def items(self):
        return zip(self.keys(),self.values())
    def pop(self,key):
        if key in self.KEYS:
            value=self[key]
            del self[key]
            return value
        raise KeyError("Invalid Key")
    def __str__(self):
        return "{season}Episode {number}: {title}".format(season=self.season+" " if self.season else "",
                                                          number=self.number,
                                                          title=self.title)

def getstats(conn,animeseasons):
    '''Compiles Stats for Crunchyroll Shows based on animeseasons'''
    shows=gettitles(conn,animeseasons=animeseasons)
    out=dict()
    for show in shows:
        seriespage=WebModules.getseriespage(show)
        seriessoup=bs4.BeautifulSoup(seriespage,"html.parser")
        seriesratings=getseriesratings(seriessoup)
        episodes=getepisodeobjects(seriessoup)
        for episode in episodes:
            print("Episode ",episode.number)
            episode.getinfo()
        out[show.series]={'ratings':seriesratings,'episodes':episodes}
    return out

def gettitles(db,animeseasons):
    '''Query Database for Crunchyroll Shows, only keep one show per Homepage to avoid repeats'''
    titles=sql.complexsearchanime(db,animeseasons=animeseasons)
    titles=[title for title in titles if "crunchyroll" in title.homepage]
    ## Anime Database divides shows by Seasons, which Crunchyroll doesn't do
    out=[]
    outhomepage=[]
    for title in titles:
        if title.homepage not in outhomepage:
            out.append(title)
            outhomepage.append(title.homepage)
    return out

def getseriesratings(soup):
    '''Finds Series Ratings (Star Ratings) on Crunchyroll Series Homepage'''
    ## Find table based on class
    divtable=soup.find("ul",attrs={"class":"rating-histogram"})
    ## Iterate over 1...5 stars to find lines (li) and save
    ratings={i:None for i in range(1,6)}
    for stars in range(1,6):
        li=divtable.find("li",attrs={"class":"{}-star cf".format(stars)})
        ## Vote number is third div
        countli=li.find_all("div")[3]
        research=CR_RATINGCOUNTRE.search(countli.text)
        ## If re-successful: add rating count to dict
        if research:
            ratings[stars]=research.group('count')
    return ratings

def getepisodeobjects(soup):
    '''Get all Episode links on CR Homepage and return URLs'''
    ## Pages come in 2 Formats: Separated into Seasons, and Not Separated:
    ## if separate, we'll capture the Season Name and pass it to the "actual" episode finder

    ## Seasons are listed in reverse order, so we'lll reverse the ourselves
    seasonlines = reversed(soup.find_all("li",attrs={"class":"season"}))
    if seasonlines:
        episodes = []
        for seasonline in seasonlines:
            season = getseasonfromseasonline(seasonline)
            episodes.extend(parseepisodeobjects(seasonline,season=season))
    else:
        episodes = parseepisodeobjects(soup)
    return episodes

def getseasonfromseasonline(soup):
    link=soup.find("a",attrs={"class":"season-dropdown"})
    if link:
        return link['title']
    return ""

def parseepisodeobjects(soup,season=""):
    ## There are multiple Element wrappers around an episode, the lowest which is relevant is the Link Element

    ## Episodes are listed in reverse order, so we'll reverse them ourselves
    episodelinks=reversed(soup.find_all("a",attrs={"class":"episode"}))
    episodes=[]
    ## Building Episode Objects to encapsulate data
    for episode in episodelinks:
        ## Get Url
        url=CR_URL+episode['href']
        ## Get Episode Number from Span  (only one, but still using "series-title" class to identify)
        numberspan=episode.find("span",attrs={"class":"series-title"})
        numresearch=CR_EPISODENUMBERRE.search(numberspan.text)
        episodenumber=None
        if numresearch:
            episodenumber=numresearch.group("number")
        ## Getting Episode Title from Paragraph Element (again, only one but still using class) (For Future Use ???)
        titlepara=episode.find("p",attrs={"short-desc"})
        ## Since Whitespace and Punctuation may be relevant, just stripping whitespace from ends and calling it a day
        episodetitle=titlepara.text.strip()
        episodes.append(CREpisode(url=url,number=episodenumber,title=episodetitle,season=season))
    return episodes

def getepisodeinfo(url):
    '''Queries Crunchyroll Episode Page and extracts Episode Rating (Only Flat Score is Available) and Blurb'''
    html=urequest.urlopen(url).read()
    soup=bs4.BeautifulSoup(html,"html.parser")
    ## info in sidebar
    sidebar=soup.find("div",attrs={"id":"sidebar"})
    ## Rating Star Bar default value is in the Span widget with this id
    ratingwidget=sidebar.find("span",attrs={"id":"showmedia_about_rate_widget"})
    ## Default Rating has to be parsed from Widget onmouseout attr
    ratingresearch=CR_EPISODERATINGRE.search(ratingwidget['onmouseout'])
    rating=None
    if ratingresearch:
        rating=ratingresearch.group("rating")
    ## Description is in a 
    descpara=sidebar.find("p",attrs={"class":"description"})
    ## Description has extra tags for toggling, we remove those
    dotspan=descpara.find("span",attrs={"class":"more-dots"})
    if dotspan: dotspan.decompose()
    morelink=descpara.find("a")
    if morelink: morelink.decompose()
    ## Blurg Text
    blurb=descpara.text
    ## Blurb may have random spaces
    blurb=CR_SPACINGRE.sub(" ",blurb)
    return {"rating":rating,"blurb":blurb}

def outputstats(filelocation,shows,stats):
    out=dict()
    for show in shows:
        stat=stats[show.series]
        episodes=[dict(episode) for episode in stat['episodes']]
        out[show.rowid]=dict(rowid=show.rowid,ratings=stat['ratings'],episodes=episodes)
    with open(filelocation,'w') as f:
        json.dump(out,f)

def sortstatsbyseason(db,queryseasons,statfile,outdirectory,overwrite=True):
    conn=sql.setupconnection(db)
    noerrorflag=True
    try:
        if not os.path.exists(outdirectory):
            os.mkdir(outdirectory)
        with open(statfile,'r') as f:
            stats=json.load(f)
        shows=[]
        for rowid,seriesstats in stats.items():
            anime=sql.getanimebyrowid(conn,rowid)
            if not anime: raise ValueError("No Anime with Rowid %s" % rowid)
            seriesstats['show']=anime
            seriesstats['episodes']=[CREpisode(**episode) for episode in seriesstats['episodes']]
            shows.append(seriesstats)
        seasons=dict()
        for season in queryseasons:
            seashows=sorted([show for show in shows if season in show['show'].animeseason],key=lambda show: show['show'].series)
            episodes=[
                [show['show'].title,episode['number'],episode['rating']] for show in seashows
                 for episode in show['episodes']
                 ]
            series=[[show['show'].title,rating,show['ratings'][rating]] for show in seashows for rating in sorted(show['ratings'])]
            seasons[coremodules.seasonstring(season)]={'series':series,'episodes':episodes}
        for season,stats in seasons.items():
            seriesfilepath="{}/CR_{} Series Stats.csv".format(outdirectory,season)
            episodefilepath="{}/CR_{} Episode Stats.csv".format(outdirectory,season)
            if not overwrite and os.path.exists(seriesfilepath):
                raise IOError("%s already exists!" % filepath)
            if not overwrite and os.path.exists(episodefilepath):
                raise IOError("%s already exists!" % filepath)
            with open(seriesfilepath,'w',newline="") as f: ## csv.writer already inserts /n... Not sure why???
                writer=csv.writer(f)
                writer.writerows(stats['series'])
            with open(episodefilepath,'w',newline="") as f: ## csv.writer already inserts /n... Not sure why???
                writer=csv.writer(f)
                writer.writerows(stats['episodes'])
    except:
        traceback.print_exc()
        noerrorflag=False
    finally:
        conn.close()
    return noerrorflag

def GatherLoop(conn,queryseasons,outfile):
    stats=getstats(conn,animeseasons=queryseasons)
    titles=sql.complexsearchanime(conn,animeseasons=queryseasons)
    titles=[title for title in titles if "crunchyroll" in title.homepage]
    outputstats(outfile,titles,stats)