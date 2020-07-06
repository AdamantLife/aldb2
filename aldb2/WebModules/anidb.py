## Builtin
import datetime
import json
import os.path
import random
import re
import time
import traceback
import xml.etree.ElementTree as ElementTree
import urllib.error as uerror, urllib.request as urequest
## Third Party
import bs4
import selenium.webdriver as webdriver
## Custom Module
import alcustoms.subclasses as aclasses
## This Module
from aldb2 import filestructure
## from aldb2.Core import modules as coremodules ## TODO: This needs to be fixed at some point
from aldb2.Core import sql

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME = "anidb"

def match_url(url):
    return bool(re.search("""anidb\.net""",url))

def parse_siteid(url):
    result = re.search("""(https?://)?anidb.net/(?P<siteid>a?\d+)""",url)
    if result:
        return result.group("siteid")
    return False

##########################################################################
###################    AnimeDatabase AniDB Settings    ###################
##########################################################################
ANIDBDATALOCATION=(filestructure.DATAPATH / 'extra data' / 'anidbdata.dat').resolve()
DEFAULTDATA={"LASTANIDBDUMP":0,"LANGUAGES":None,"username":"","password":""}

def createdata():
    if not ANIDBDATALOCATION.parent.exists():
        ANIDBDATALOCATION.parent.mkdir(parents = True)
    with open(ANIDBDATALOCATION,'w') as f:
        json.dump(DEFAULTDATA,f)

def getdata():
    if not ANIDBDATALOCATION.exists(): return {}
    with open(ANIDBDATALOCATION,'r') as f:
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
    with open(ANIDBDATALOCATION,'w') as f:
        json.dump(out,f)

if not os.path.exists(ANIDBDATALOCATION):createdata()
olddata=getdata()
for key,value in DEFAULTDATA.items():
    if key not in olddata:
        olddata[key]=value
savedata(olddata)
del olddata

##########################################################################
###########################    Titles Index    ###########################
##########################################################################
ANIDB_TITLEDUMPURL=r"http://anidb.net/api/anime-titles.xml.gz"
ANIDB_TITLEFILELOCATION=filestructure.DATAPATH / 'extra data' / 'anidb_title_list.xml'

def downloadtitledump(data=None):
    if not data: data=getdata()
    today,previous=datetime.datetime.today(),datetime.datetime.fromtimestamp(data['LASTANIDBDUMP'])
    if today<previous+datetime.timedelta(days=1): raise ValueError("Per AniDB, cannot fetch title list more often than once a day")
    req=urequest.urlopen(ANIDB_TITLEDUMPURL)
    if req.getcode!=(): raise uerror.HTTPError("Failed Fetch")
    xml=req.read()
    data['LASTANIDBDUMP']=today.timestamp()
    with open(ANIDB_TITLEFILELOCATION,'w') as f:
        f.write(xml)
    updatetitlelanguages(data=data)
    return True

def updatetitlelanguage(data=None):
    if not data: data=getdata()
    if not os.path.exists(ANIDB_TITLEFILELOCATION):
        return downloadtitledump(data=data)
    root=ElementTree.parse(ANIDB_TITLEFILELOCATION).getroot()
    languages=[]
    for anime in root.iter('anime'):
        for lang in anime.iterfind("title"):
            language=lang.attrib[r'{http://www.w3.org/XML/1998/namespace}lang'].replace("-","")
            if language not in languages:
                languages.append(language)
    languages=sorted(languages)
    data['LANGUAGES']=languages
    savedata(data)
    return True

def getalltitlesfromxml(data=None):
    if not data: data=getdata()
    if not os.path.exists(ANIDB_TITLEFILELOCATION):
        return downloadtitledump(data=data)
    root=ElementTree.parse(ANIDB_TITLEFILELOCATION).getroot()
    out=[]
    for anime in root.iter('anime'):
        anidict=dict(anidbid=anime.attrib['aid'])
        languages=dict()
        for lang in anime.iterfind("title"):
            language=lang.attrib[r'{http://www.w3.org/XML/1998/namespace}lang'].replace("-","")
            if language not in languages:
                languages[language]=lang.text
            else:
                languages[language]=languages[language]+" "+lang.text
        anidict.update(languages)
        out.append(anidict)
    return out
##########################################################################
###########################    Web Scraping    ###########################
##########################################################################
HOMEPAGE=r"http://anidb.net/perl-bin/animedb.pl?show=main"
ANIMEURL=r"http://anidb.net/{identification}"
VOTESURL=r"http://anidb.net/perl-bin/animedb.pl?show=votes&aid={identification}"
EPISODEVOTESURL=r"http://anidb.net/perl-bin/animedb.pl?show=votes&eid={episodeid}"
OUTPUTLOCATION= (filestructure.DATAPATH / r"anidb").resolve()
STATSARCHIVELOCATION= str(OUTPUTLOCATION) + "votes {anidbid}.html"
if not OUTPUTLOCATION.exists(): OUTPUTLOCATION.mkdir(parents=True)

ANIDBRE = re.compile(ANIMEURL.replace("http:","https?:").replace(r"{identification}",r"(?P<identification>\w+)"))
def parseidfromurl(url):
    search = ANIDBRE.search(url)
    if not search: return False
    return search.group("identification")

def connect(username,password):
    data=getdata()
    if not username or not password:
        username,password=data['username'],data['password']
        if not username or not password:
            raise ValueError("No Username and/or Password Available")
    else:
        data['username'],data['password']=username,password
        savedata(data)
    driver=webdriver.Chrome("chromedriver.exe")
    login(driver,username,password)
    return driver

def login(driver,USERNAME,PASSWORD):
    driver.get(HOMEPAGE)
    nameinput=driver.find_element_by_name("xuser")
    driver.execute_script("arguments[0].value=arguments[1]",nameinput,USERNAME)
    passwordinput=driver.find_element_by_name("xpass")
    driver.execute_script("arguments[0].value=arguments[1]",passwordinput,PASSWORD)
    autologincheck=driver.find_element_by_name("xdoautologin")
    driver.execute_script("arguments[0].checked=false",autologincheck)
    submitbutton=driver.find_element_by_name("do.auth")
    driver.execute_script("arguments[0].click()",submitbutton)

def downloadvotespage(driver,anidbid,outputlocation=None):
    if outputlocation is None: outputlocation=OUTPUTLOCATION+"votes {anidbid}.html".format(anidbid=anidbid)
    ## We got flagged going straight to the votes page, despite sleep delays, so we'll be taking the scenic route
    driver.get(ANIMEURL.format(identification=anidbid))
    links=drier.find_elements_by_tag_name('a')
    ratinglink=None
    while not ratinglink:
        for link in links:
            if link.get_attribute('href')==r"animedb.pl?show=votes&amp;aid={anidbid}".format(anidbid=anidbid):
                ratinglink=link
                break
        raise ValueError("Could not find ratings link!")
    driver.execute_script("arguments[0].click()",ratinglink)
    with open(STATSARCHIVELOCATION.format(anidbid=anidbid),'w') as f:
        f.write(driver.page_source)

##########################################################################
################################    SQL    ###############################
##########################################################################
def updatesqlwithtitles(conn,tablename="anidbtitles"):
    if not os.path.exists(ANIDB_TITLEFILELOCATION):
        try:
            downloadtitledump()
        except ValueError or uerror.HTTPError:
            raise FileNotFoundError("No Title File at %s and Cannot Download" % ANIDB_TITLEFILELOCATION)
    setup=checksetupsqltitles(conn,tablename=tablename)
    if setup:
        titles=getalltitlesfromxml()
        addtitlestotitlestable(conn,*titles,tablename=tablename)
    return True

def checksetupsqltitles(conn,tablename='anidbtitles'):
    updatetitlelanguage()
    data=getdata()
    columnnames=['anidbid',]
    columnnames.extend(data['LANGUAGES'])
    tables=conn.execute(
'''SELECT name FROM sqlite_master
WHERE type='table';''').fetchall()
    tables=[table['name'] for table in tables]
    if tablename not in tables:
        createtitlestable(conn,tablename=tablename,columns=columnnames)
        return checksetupsqltitles(conn,tablename=tablename)
    columns=getcolumnsfromsqltitles(conn,tablename=tablename)
    if not all(cname in columns for cname in columnnames):
        return updatetitletable(conn,columnnames,tablename=tablename)
    return True

def createtitlestable(conn, tablename='anidbtitles',columns=None):
    if columns is None: columns=['anidbid','en','x-jat','ja']
    if not columns or not isinstance(columns,list): raise AttributeError("If Columns are supplied, they must be a list of non-zero length")
    conn.execute(
'''CREATE VIRTUAL TABLE {tablename} USING fts4
({columns})'''.format(
tablename=tablename,columns=",".join(["{} text".format(col) for col in columns])))
    return True

def updatetitletable(conn,columns,tablename='anidbtitles'):
    titles=getalltitlesfromsql(conn,tablename=tablename)
    deletetitlestable(conn,tablename=tablename)
    createtitlestable(conn,tablename=tablename,columns=columns)
    if titles:
        addtitlestotitlestable(conn,*titles,tablename=tablename)
    return True

def deletetitlestable(conn,tablename='anidbtitles'):
    conn.execute(
'''DROP TABLE {}'''.format(tablename))

def getcolumnsfromsqltitles(conn,tablename='anidbtitles'):
    columns=conn.execute(
'''PRAGMA table_info({})'''.format(tablename)).fetchall()
    return [column['name'] for column in columns]

def getalltitlesfromsql(conn,tablename='anidbtitles'):
    return conn.execute('''SELECT rowid,* FROM {}'''.format(tablename)).fetchall()

def gettitlebyrowid(conn,rowid,tablename='anidbtitles'):
    title=conn.execute(
'''SELECT rowid,* FROM ?
WHERE rowid=?''',
(tablename,rowid)).fetchone()
    return title

def gettitlebyanidbid(conn,anidbid,tablename='anidbtitles'):
    title=conn.execute(
'''SELECT rowid,* FROM ?
WHERE rowid=?''',
(tablename,anidbid)).fetchone()
    return title

def gettitlesbytitle(conn,title,tablename='anidbtitles'):
    titles=conn.execute(
'''SELECT rowid,* FROM {tablename}
WHERE {tablename} MATCH '{title}' '''.format(tablename=tablename,title=title)).fetchall()
    return titles

def addtitlestotitlestable(conn,*titles,tablename='anidbtitles'):
    if not titles: return
    columns=getcolumnsfromsqltitles(conn,tablename=tablename)
    out=[]
    for title in titles:
        outdict={col:"" for col in columns}
        for key in outdict:
            if key in title:
                outdict[key]=title[key]
        out.append([outdict[col] for col in columns])
    conn.executemany(
'''INSERT INTO {} VALUES
({})'''.format(tablename,",".join(["?" for col in columns])),
out)

def removetitlebyrowid(conn,rowid,tablename='anidbtitles'):
    conn.execute(
'''DELETE FROM ?
WHERE rowid=?''',
(tablename,rowid))

def removetitlebyanidbid(conn,anidbid,tablename='anidbtitles'):
    conn.execute(
'''DELETE FROM ?
WHERE anidbid=?''',
(tablename,anidbid))


##########################################################################
############################    GatherLoop    ############################
##########################################################################
ANIDBRATINGSDICT={i:0 for i in range(1,11)}
ANIDBRATINGSRE=re.compile('''(?P<count>\d+) users voted (?P<rating>\d+)''')
PERMANENTRE=re.compile("Permanent")
TEMPORARYRE=re.compile("Temporary")

def GatherLoop(conn,queryseasons,outfile,pipe=None):
    data=getdata()
    shows=gettitles(conn,queryseasons)
    driver=connect(data['username'],data['password'])
    sucshows=successfulshows=downloadshowvotes(conn,driver,shows,pipe=pipe)
    failshows=[show for show in shows if show not in sucshows]
    stats=getstats(conn,sucshows)
    stats['failed']=[show.rowid for show in failshows]
    outputstats(outfile,stats)

def gettitles(db,animeseasons):
    '''Query Database for AniDB-link shows'''
    titles=sql.complexsearchanime(db,animeseasons=animeseasons)
    titles=list({title for title in titles if title.anidbid})
    return titles

def downloadshowvotes(conn,driver,shows,pipe=None):
    out=[]
    for show in shows:
        try:
            if pipe: pipe("Downloading: ",show.title)
            downloadvotespage(driver,show.anidbid)
        except:
            traceback.print_exc()
        else: out.append(show)
        finally:
            ## AniDB doesn't like webscrapers, so we'll be irregular about it
            time.sleep(random.randint(25,60))
    return out

def getstats(conn,shows):
    '''Compiles Stats for downloaded AniDB'''
    out=dict()
    for show in shows:
        showdict=dict(rowid=show.rowid)
        showdict['ratings']=getseriesrating(show.anidbid)
        out[show.rowid]=showdict
    return out

def getseriesrating(anidbid):
    file=STATSARCHIVELOCATION.format(anidbid=anidbid)
    print(file)
    if not os.path.exists(file): raise FileNotFoundError("%s Does Not Exist!" % file)
    with open(file,'r') as f:
        soup=bs4.BeautifulSoup(f.read(),'html.parser')
    ## Graph is div with class "g_section g_bubble graph"
    graphs=soup.find_all('div',attrs={'class':'g_section g_bubble graph'})
    ## Two tables we're getting ratings from, finding them by name (Permanent, Temporary) via regex
    permanent=[graph for graph in graphs if graph.find_all(string=PERMANENTRE)][0]
    temporary=[graph for graph in graphs if graph.find_all(string=TEMPORARYRE)][0]
    ## Pull Ratings from Graphs
    ratings=getvotesfromgraph(permanent)+getvotesfromgraph(temporary)
    ## Ratings is dict with ratings 1...10
    return ratings

def getvotesfromgraph(graph):
    graphdict=aclasses.SumDict(ANIDBRATINGSDICT)
    ## Each bar is within a div "column" class
    divs=graph.find_all("div",attrs={"class":"column"})
    ## Have to weed out table header: Has a "header" div with text "Vote"
    divs=[column for column in divs if not column.find("div",attrs={"class":"header"},string="Vote")]
    for div in divs:
        ## The div class with "bar" class contains all necessary info as "title" attr
        bardiv=div.find("div",attrs={"class":"bar"})
        research=ANIDBRATINGSRE.search(bardiv['title'])
        if research:
            count,rating=research.group('count'),research.group('rating')
            graphdict[int(rating)]=int(count)
    return graphdict

def outputstats(filelocation,stats):
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
            shows.append(seriesstats)
        seasons=dict()
        for season in queryseasons:
            seashows=sorted([show for show in shows if season in show['show'].animeseason],key=lambda show: show['show'].title)
            series=[[show['show'].title,rating,show['ratings'][rating]] for show in seashows for rating in sorted(show['ratings'])]
            seasons[coremodules.seasonstring(season)]=series
        for season,stats in seasons.items():
            seriesfilepath="{}/AniDB_{} Series Stats.csv".format(outdirectory,season)
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