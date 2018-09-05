## Builtin
import bs4
import csv
import json
import os, os.path
import re
import traceback
import urllib.request as urequest
import xml.etree.ElementTree as ElementTree
## This Module
## from aldb2.Core import modules as coremodules ## TODO: Fix This
from aldb2.Core import sql

ANN_APIURL=r"http://www.animenewsnetwork.com/encyclopedia/reports.xml?id=155&search={series}"
ANN_ENCYCURL=r"http://www.animenewsnetwork.com/encyclopedia/anime.php?id={identification}"

ANN_VOTERE=re.compile('''(?P<votetype>[^:]+)\s*:\s*(?P<count>\d+)''')

ANNRATINGSDICT={"masterpiece":None,"excellent":None,
              "very good":None,"good":None,"decent":None,"so-so":None,
              "not really good":None,"weak":None,"bad":None,"awful":None,
              "worst ever":None}
ANNRATINGSORDER=["masterpiece","excellent","very good","good","decent",
                 "so-so","not really good","weak","bad","awful","worst ever"]

def annapi_search(searchvalue):
    if not searchvalue: return
    url=ANN_APIURL.format(series=searchvalue)
    req=urequest.urlopen(url)
    if req.getcode()!=200:
        return False
    root=ElementTree.fromstring(req.read().decode())
    items=root.findall("item")
    return items

def GatherLoop(conn,queryseasons,outfile):
    animes=sql.complexsearchanime(conn,animeseasons=queryseasons)
    stats=getstats(animes)
    out={stat['rowid']:stat for stat in stats}
    outputstats(outfile,out)
 
def getstats(animes):
    out=[]
    for anime in animes:
        print("Getting Votes for: ",anime.title)
        stats=getvotes(anime)
        out.append({"rowid":anime.rowid,"ratings":stats})
    return out
 
def getvotes(anime):
    url=ANN_ENCYCURL.format(identification=anime.annid)
    html=getpage(url)
    soup=bs4.BeautifulSoup(html.read(),'html.parser')
    votedict=dict(ANNRATINGSDICT)
    ## Get Ratings Table by id "ratingsbox"
    ratingsdiv=soup.find("div",attrs={"id":"ratingbox"})
    ## Each rating has a div with class "one-rating"
    for div in ratingsdiv.find_all("div",attrs={"class":"one-rating"}):
        ## Rating has only one direct-child span which holds numbers
        numberspan=div.find("span")
        ## Span has a subspan that contains vote breakdown; we'll chuck that
        subspan=numberspan.find("span")
        if subspan:
            subspan.decompose()
        ## Use regex to pull vote type and
        research=ANN_VOTERE.search(numberspan.text)
        if research:
            votedict[research.group("votetype").strip().lower()]=int(research.group("count").strip())
    return votedict
 
def getpage(url,attempt=0):
    html=urequest.urlopen(url)
    if html.getcode()!=200:
        print("> Time Out On {}".format(url))
        if attempt<1:
            time.sleep(5)
            return getpage(url,attempt=1)
        else:
            raise TimeoutError("Could not load url %s" % url)
    return html
 
def outputstats(outputfile,stats):
    with open(outputfile,'w') as f:
        json.dump(stats,f)
 
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
            shows.append(seriesstats)
        seasons=dict()
        for season in queryseasons:
            seashows=sorted([show for show in shows if season in show['show'].animeseason],key=lambda show: show['show'].series)
            series=[[show['show'].title,rating,show['ratings'][rating]] for show in seashows for rating in sorted(show['ratings'],key=ANNRATINGSORDER.index)]
            seasons[coremodules.seasonstring(season)]=series
        for season,stats in seasons.items():
            seriesfilepath="{}/ANN_{} Series Stats.csv".format(outdirectory,season)
            if not overwrite and os.path.exists(seriesfilepath):
                raise IOError("%s already exists!" % filepath)
            if not overwrite and os.path.exists(episodefilepath):
                raise IOError("%s already exists!" % filepath)
            with open(seriesfilepath,'w',newline="") as f: ## csv.writer already inserts /n... Not sure why???
                writer=csv.writer(f)
                writer.writerows(stats)
    except:
        traceback.print_exc()
        noerrorflag=False
    finally:
        conn.close()
    return noerrorflag