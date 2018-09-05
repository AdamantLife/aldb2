## Builtin
import csv
import json
import os,os.path
import pathlib
import re
import time
import traceback
import xml.etree.ElementTree as ElementTree
## Third Party
import bs4
import requests
## This Module
from aldb2 import filestructure
from aldb2.Core import core as coremodules
from aldb2.Core import sql

MALRATINGSDICT={i:0 for i in range(1,11)}

MAL_APIURL=r"http://myanimelist.net/api/anime/search.xml?q={search}"
MAL_URL=r"http://myanimelist.net/anime/{identification}"
SCORERE=re.compile('''Score Stats''')
VOTESRE=re.compile('''\((?P<count>\d+) votes\)''')

OUTPUTLOCATION= (filestructure.DATAPATH / "mal").resolve()
STATSARCHIVELOCATION= str(OUTPUTLOCATION) + "votes {malid}.html"
if not OUTPUTLOCATION.exists(): OUTPUTLOCATION.mkdirs(parents=True)

DEFAULTDATA={'username':'','password':''}

MALRE = re.compile(MAL_URL.replace("http:","https?:").replace(r"{identification}",r"(?P<identification>\w+)"))
def parseidfromurl(url):
    search = MALRE.search(url)
    if not search: return False
    return search.group("identification")

def createdata():
    with open(MALDATLOCATION,'w') as f:
        json.dump(DEFAULTDATA,f)

def getdata():
    with open(MALDATLOCATION,'r') as f:
        return json.load(f)
def updatedata(key,value):
    current=getdata()
    if key not in current: raise AttributeError("Invalid AniDB Data Key")
    current[key]=value
    savedata(current)

def savedata(newdata):
    current=getdata()
    out=dict(current)
    for key,value in newdata.items():
        if key in current:
            out[key]=value
    with open(MALDATLOCATION,'w') as f:
        json.dump(out,f)

MALDATLOCATION=(filestructure.DATAPATH / "extra data" / "mal.data").resolve()
if not MALDATLOCATION.exists(): createdata()
olddata=getdata()
for key,value in DEFAULTDATA.items():
    if key not in olddata:
        olddata[key]=value
savedata(olddata)
del olddata


def getcredentials():
    data=getdata()
    return data['username'],data['password']
def updatecredentials(username,password):
    data=getdata()
    data['username']=username
    data['password']=password
    savedata(data)

def malapi_search(searchvalue,username=None,password=None):
    if not username or not password:
        username,password=getcredentials()
        if not username or not password: return None
        updateflag=False
    else: updateflag=True
    if not searchvalue: return False
    url=MAL_APIURL.format(search=searchvalue)
    req=requests.get(url, auth=(username,password))
    if req.status_code!=200:
        return False
    if updateflag:
        updatecredentials(username,password)
    root=ElementTree.fromstring(req.text)
    entries=root.findall("entry")
    return entries

def gettitles(db,animeseasons):
    '''Query Database for AniDB-link shows'''
    titles=sql.complexsearchanime(db,animeseasons=animeseasons)
    titles=list({title for title in titles if title.malid})
    return titles

def gethomepage(malid):
    '''Get BSoup for MAL Homepage based on MALID'''
    url=MAL_URL.format(identification=malid)
    req=requests.get(url)
    print(req.status_code)
    ## MAL will timeout rapid requests
    if req.status_code==429:
        print("extra sleep")
        time.sleep(5)
        return gethomepage(malid)
    soup=bs4.BeautifulSoup(req.text,'html.parser')
    return soup

def getstatsurlfromhomesoup(soup):
    '''Find the URL for MAL Show Stats Page'''
    ## navbar is div with id "horiznav_nav"
    navbar=soup.find("div",attrs={"id":"horiznav_nav"})
    if not navbar: print(soup)
    ## Stat's link is a with text "Stats"
    statslink=navbar.find("a",string="Stats")
    return statslink['href']

def downloadstatspage(url,malid,outputlocation=None):
    '''Download Stats Page for future use'''
    if outputlocation is None: outputlocation=STATSARCHIVELOCATION.format(malid=malid)
    req=requests.get(url)
    ## MAL will timeout rapid requests
    if req.status_code==429:
        print("extra sleep")
        time.sleep(5)
        return downloadstatspage(url,malid,outputlocation=outputlocation)
    with open(outputlocation,'w',encoding='utf-8') as f:
        f.write(req.text)

def getstats(shows):
    '''Get Stats for Show from MAL'''
    out=dict()
    for show in shows:
        showdict=dict(rowid=show.rowid)
        showdict['ratings']=getseriesrating(show.malid)
        out[show.rowid]=showdict
    return out
        
def getseriesrating(malid):
    file=STATSARCHIVELOCATION.format(malid=malid)
    print(file)
    if not os.path.exists(file): raise FileNotFoundError("%s Does Not Exist!" % file)
    statdict=dict(MALRATINGSDICT)
    with open(file,'r',encoding='utf-8') as f:
        soup=bs4.BeautifulSoup(f.read(),'html.parser')
    ## Series Ratings is in an "unmarked" table; we'll find the h2 with text "Score Stats"
    scorehead=soup.find("h2",string="Score Stats")
    ## The next table should be the ratings table
    table=scorehead.find_next_sibling('table')
    ## Then iterate over table rows
    for row in table.find_all('tr'):
        ## First td is the rating and the second wraps the count
        ratingtd,counttd=row.find_all('td')
        ## rating is simply text of ratingtd
        rating=int(ratingtd.text)
        ## Extract votes using re
        research=VOTESRE.search(' '.join(counttd.stripped_strings))
        if research:
            count=research.group('count')
            statdict[rating]=int(count)
    return statdict

def outputstats(filelocation,stats):
    loc=pathlib.Path(filelocation)
    if not loc.parent.exists(): loc.parent.mkdir(parents=True)
    with open(filelocation,'w') as f:
        json.dump(stats,f)

def GatherLoop(conn,queryseasons,outfile,pipe=None):
    shows=gettitles(conn,queryseasons)
    #for show in shows:
    #    if pipe: pipe("Getting:", show.title)
    #    soup=gethomepage(show.malid)
    #    statsurl=getstatsurlfromhomesoup(soup)
    #    downloadstatspage(statsurl,show.malid)
    #    ## MAL will timeout rapid requests
    #    time.sleep(2)
    stats=getstats(shows)
    outputstats(outfile,stats)
    
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
            seashows=sorted([show for show in shows if season in show['show'].animeseason],key=lambda show: show['show'].title)
            series=[[show['show'].title,rating,show['ratings'][rating]] for show in seashows for rating in sorted(show['ratings'],key=lambda rating:int(rating))]
            seasons[coremodules.seasonstring(season)]=series
        for season,stats in seasons.items():
            seriesfilepath="{}/MAL_{} Series Stats.csv".format(outdirectory,season)
            if not overwrite and os.path.exists(seriesfilepath):
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