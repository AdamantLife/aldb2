## Builtin
import copy
import csv
import datetime
import functools
import json
import re
## Custom Module
from alcustoms import web
from alcustoms.web import requests as alrequests
from aldb2 import SeasonCharts

CHARTNAME = "AniChart"

APIURL = r"http://anichart.net/api/browse/anime?season={season}&year={year}&sort=-score&full_page=true&airing_data=true&page=1"

## For conversion of youtube_id API value
YOUTUBELINK = "www.youtube.com/watch?v={youtube_id}"

## Ordered for desired output
APIDATAHEADERS = ['title_japanese', 'title_romaji', 'title_english', 'first episode', 'airing', 'hashtag', 'image', 'airing_status', 'anilist_link', 'average_score', 'description', 'duration', 'end_date', 'external_links', 'genres', 'id', 'mal_link', 'popularity', 'rankings', 'season', 'source', 'start_date', 'studio', 'synonyms', 'tags', 'total_episodes', 'type', 'youtube_id']

sessiondecorator = alrequests.session_decorator_factory(useragent = True, referrer = "http://anichart.net")

def checkcsrf(func):
    """ Decorator for functions that require anichart's csrf token ("X-CSRF-TOKEN"; i.e.- API calls) """
    @functools.wraps(func)
    @sessiondecorator
    def wrapper(*args, session = None, **kw):
        if "X-CSRF-TOKEN" not in session.cookies:
            getcsrf(session)
        return func(*args,session = session, **kw)
    return wrapper

def getcsrf(session):
    """ Adds a csrf token to the session """
    session.get("http://anichart.net")

class Show(dict):
    """ A simple container used to facilitate cleaning API data """
    def __hash__(self):
        return self['id']
    def serialize(self):
        out = copy.deepcopy(self)
        if out.get("airing"):
             out['airing'] = out['airing']['time'].strftime("%I:%M %p")
        return out

@checkcsrf
def getshowsbyseason(season,year, session = None):
    """ Queries the API for the given season-year and returns the API information """
    url = APIURL.format(season=season, year = year)
    headers = {"X-CSRF-TOKEN":session.cookies['X-CSRF-TOKEN']}
    data = alrequests.GET_json(url,session = session, headers=headers)
    return {cat:[Show(**show) for show in shows] for cat,shows in data.items()}

def consolidate_data(data):
    """ Consolidates the API data into a single list
    
    The original root value (i.e.- tv, leftovers) is added as the "category" key and title()'d.
    """
    out = list()
    ## API data is organized in {category (tv,tvshort,movie,etc.):[list of show dicts]}
    for cat,shows in data.items():
        for show in shows:
            show['category'] = cat.title()
            out.append(show)
    return out

def test_rawdata(data):
    """ Checks if the data has been consolidated, returning True if it has not, otherwise False """
    base = list(data)[0]
    if base in ["tv","leftovers","tv short","movie","OVA / ONA / Special"]:
        return True
    return False

def check_rawdata(data):
    """ Checks if the data has been consolidated using test_rawdata; if it hasn't, this function will consolidate the data """
    if test_rawdata(data):
        return consolidate_data(data)
    return data

def fixstartdate(startdate):
    """ Converts startdate default "yyyymmdd" to "dd/mm/yyyy"
    
    If startdate is falsey, returns a default value of "01/01/2017"
    """
    if not startdate: return "01/01/2017"
    s = str(startdate)
    d,m,y = [max(dt,1) for dt in [int(s[6:8]),int(s[4:6]),int(s[:4])]]
    return f"{d:0>2}/{m:0>2}/{y:0>4}"

def getseason(data):
    """ Tries to determine the season that an anime aired based on its season value and it's ratings """
    ## Season key is the most reliable
    season = data.get("season")
    if season:
        ## Season key is an integer formatted "YYS" and is 2000-based (i.e.- 171 == 2017-Winter)
        season = str(season)
        year = int(f"20{season[:2]}")
        ## Anichart Season key is 1-indexed
        season = int(season[2]) - 1
        ## This should normally pass; if it consistently does not, we'll have to investigate why
        try: return SeasonCharts.buildseason(season,year)
        ## If something goes wrong, we'll try another method
        except: print(f"Failed to parse season: {data['season']}")
    ## Next, we'll iterate over rankings to try to determine the season/year
    ## There are multiple types of rankings based on season, year, and both combined,
    ## so we'll piece it together based on whatever we come across first
    season,year = None,None
    for ranking in data.get("rankings",list()):
        ## Quicker exit (without just making this loop its own function)
        if season and year: continue
        ## We'll ignore stuff we've already gotten and assume that nothing in
        ## rankings contradicts eachother
        if not season:
            ## Defaults to None one way or another if it's not supplied
            season = ranking.get("season")
        if not year: year = ranking.get("year")
    ## Check if we made it
    if season and year:
        ## As above, this should always work out-of-the-box
        try: return SeasonCharts.buildseason(season,year)
        except: print(season,year)
    ## Welp, we're stumped...
    return None


def overwrite_season(function):
    """ A wrapper to allow a function to accept a season and overwrite all data entries with the given season using replace_season

    If season is provided, it must be a string that conforms to the standard Season format found in SeasonCharts.
    The season parameter accepted by this decorator will NOT be passed on to the function.
    season is updated on the output, but in many cases will mutate the input as well due to the way this module
    handles data.
    """
    @functools.wraps(function)
    def inner(*args, season = None, **kw):
        data = function(*args,**kw)
        if season:
            replace_season(data,season)
        return data
    return inner

def replace_season(data,season):
    """ Replaces the season value of a list of Show objects or data dicts
    
    Mutates the objects in-place.
    """
    if not SeasonCharts.matchseason(season):
        raise SeasonCharts.SeasonError
    ## Check data format
    if test_rawdata(data):
        for cat,shows in data.items():
            for show in shows: show['season'] = season
    else:
        for show in data: show['season'] = season


@overwrite_season
def cleanapidata_csv(data):
    """ Cleans the API data for use in a CSV and returns a list of headers along with the clean data.
    
    Converts startdate to EST startdate.
    Adds firstepisode date.
    Adds EST_airing time.
    Features overwrite_season decorator
    Returns ([list of Headers (strs)],[list of Shows (dicts)])
    """

    out = list()
    siteheaders = []
    data = check_rawdata(data)
    for show in data:
        if show.get("airing"):
            ## Convert airing to datetime for utility
            show['airing']['time'] = datetime.datetime.fromtimestamp(show['airing']['time']).replace(tzinfo = web.JST)

        ## Format start_date to Day/Month/Year
        if show.get("start_date"):
            ## start_date is an integer representing yyyymmdd
            startdate = fixstartdate(show['startdate'])
            startdt = None
            ## Test that start_date is a valid date
            try:
                startdt = datetime.datetime.strptime(startdate, "%d/%m/%Y")
            except:
                ## If not, use "airing" 
                if show.get("airing"):
                    ## If we're multiple weeks in, compensate (next_episode = 1 means we're on the first week)
                    startdt = show['airing']['time'] - datetime.timedelta(weeks = show['airing']['next_episode']-1)
                ## If "airing" doesn't work, the month and year are normally correct
                ## so we'll just replace the day
                else:
                    s = str(show['startdate'])
                    startdate = f"{s[4:6]}/01/{s[:4]}"
            ## If we ended up using a dt object, convert it back out
            if startdt:
                startdate = startdt.strftime("%d/%m/%Y")
            ## Set clean data
            show['start_date']= startdate
        ## Remove breaks from "description" (Excel isn't escaping newline characters)
        if show.get('description'):
            ## <br> characters sometimes sneak in as well
            show['description'] = show['description'].replace("\n"," ").replace("<br>","")
        ## Convert studio from object dict to simply name
        if show.get("studio"):
            show['studio'] = show['studio']['name']
        ## Convert "tags" from object dicts to a string of names, and remove all spoiler tags
        show['oldtags'] = []
        if show.get('tags'):
            show['tags'] = ", ".join(sorted([tag['name'] for tag in show['tags'] if not tag['spoiler']]))
        ## If "tags" list is empty, replace it with empty string
        else:
            show['tags'] = ""
        ## Convert "youtube_id" to url
        if show.get('youtube_id'):
            show['youtube_id'] = YOUTUBELINK.format(youtube_id = show["youtube_id"])
            
        ######### Generated Data

        ## Set the first episode's date (used for sorting purposes)
        show['first_episode'] = None
        ## Requires "airing" and "start_date"
        if show.get('airing') and show.get('start_date'):
            ## Create full datetime
            airtime = f"{show['airing']['time'].strftime('%H:%M')} {show['start_date']}"
            dt = datetime.datetime.strptime(airtime,"%H:%M %d/%m/%Y")
            ## Convert to EST
            dt = dt.replace(tzinfo = web.JST).astimezone(web.EST)
            show['first_episode'] = dt.strftime("%d/%m/%Y")

        ## Airing time in EST
        show['EST_airing'] = ""
        ## Use "airing" to get the airtime in EST as HH:MM apm
        if show.get('airing'):
            dt = show['airing']['time'].astimezone(web.EST)
            ## Set clean data
            show['EST_airing'] = dt.strftime("%H:%M")

        ## Convert sites in "external_sites" to their own header
        ## There may be multiple sites in each site category
        ## (Official Site, Twitter, etc.), so we'll keep track
        ## of duplicates locally using enumeration and at the
        ## method scope using "siteheaders"

        ## Get a master list of external site names
        sitenames = list(set([site['site'] for site in show['external_links']]))
        ## For each unique site name
        for name in sitenames:
            ## Collect all occurrences
            count = [site for site in show['external_links'] if site['site'] == name]
            ## Enumerate so we can't create additional, unique headers as necessary
            ## Example Headers: Twitter[, Twitter 2, Twitter 3, ...])
            for i,site in enumerate(count,start=1):
                ## The first occurence simply goes by the category of site
                if i == 1: duplicatename = name
                ## Otherwise append the occurence count
                else: duplicatename = f"{name} {i}"
                ## Keep track at the method level so that we can
                ## output data correctly
                if duplicatename not in siteheaders:
                    siteheaders.append(duplicatename)
                ## Add to show dict
                show[duplicatename] = site['url']
        ## Remove "external_links" because it is now redundant
        del show['external_links']

        out.append(show)

    headers = list(APIDATAHEADERS)
    ## Added during cleaning and updating
    headers.insert(0,'category')
    headers.insert(4,"first_episode")
    headers.insert(5,"EST_airing")
    headers.extend(sorted(siteheaders)) 
    ## Removed during cleaning and updating
    headers.remove("external_links")

    return headers,out

def outputapidata_csv(filename, data, headers=None):
    """ Creates a CSV file with filename using data and headers (if supplied) """
    with open(filename,'w',encoding='utf-8',newline = "", ) as f:
        if headers:
            writer = csv.DictWriter(f,fieldnames = headers)
            writer.writeheader()
        else:
            writer = csv.DictWriter(f)
        writer.writerows(out)

def serializeshows(file,shows):
    """ Creates a json file containing the shows """
    with open(file,'w', encoding = 'utf-8') as f:
        json.dump([show.serialize() for show in shows],f)

def convertshowstostandard(data, season = None, showfactory = SeasonCharts.Show):
    """ Converts a full collection of API data to a list of standard Show Objects (via converttostandard)
    
    If season is provided, replace_season will be called before converting.
    """
    data = check_rawdata(data)
    out = list()
    if season: replace_season(data)
    for show in data: out.append(converttostandard(show, showfactory = showfactory))
    return out

def converttostandard(show, showfactory = SeasonCharts.Show):
    """ Converts an AniChart Show to a standard Show Object """
    if not isinstance(show,Show):
        raise TypeError("converttostandard requires an AniChart Show Object.")
    chartsource = [(CHARTNAME,show['id']),]

    if show.get("season") is None or not SeasonCharts.matchseason(show.get("season")):
        show['season'] = getseason(show)
    season = show['season']
    japanese_title = show['title_japanese']
    romaji_title = show['title_romaji']
    english_title = show['title_english']
    additional_titles = show['synonyms']
    medium = show['type']
    continuing = show['category'].lower() == "leftovers"
    summary = f"(From {CHARTNAME})\n{show.get('description')}"

    tags = []
    for tag in show['tags']:
        tags.append((tag['name'],tag['spoiler']))
    for genre in show['genres']:
        ## AniChart... generates "" Genres??? O.o
        if genre:
            tags.append((genre,False))

    
    airingtime = show.get('airing')
    if not airingtime: airingtime = datetime.datetime(1,1,1)
    else: airingtime = datetime.datetime.fromtimestamp(airingtime['time'])
    startdate = fixstartdate(show.get("start_date"))
    startdate = f"{startdate}  {airingtime.strftime('%H:%M')} +0900"

    episodes = show['total_episodes']
    images = [show['image'],]

    studios = []
    if show.get('studio'):
        studios = [show['studio']['name'],]

    links = []
    if show.get('youtube_id'):
        links.append(("Youtube",YOUTUBELINK.format(youtube_id = show["youtube_id"])))
    if show.get("anilist_link"):
        links.append(("Anilist",show['anilist_link']))
    if show.get("mal_link"):
        links.append(("MAL",show['mal_link']))
    for link in show.get("external_links",list()):
        links.append((link["site"],link["url"]))

    return showfactory(chartsource = chartsource, season = season,
                             japanese_title = japanese_title, romaji_title = romaji_title,
                             english_title = english_title, additional_titles = additional_titles,
                             medium = medium, continuing = continuing, summary = summary,
                             tags = tags, startdate = startdate, episodes = episodes, images = images,
                             studios = studios, links = links)
    
LINKRE = re.compile("""(?P<name>(?:\w| )+?)(?:\s+\d+|$)""")
def checklink(key,value):
    """ Checks if a key,value pair is a website link, and strips any enumeration created by cleanapidata_csv """
    try:
        if not value.startswith(("http","www")): return False, False
    ## Value is not string, so it can't be website link
    except: return False, False
    linkresearch = LINKRE.search(key)
    ## In normal practice this really shouldn't happen :-/
    if not linkresearch: return False, False
    return linkresearch.group("name"), value


if __name__ == "__main__":
    season,year = "Fall",2017
    
    print("getting data")
    data = getshowsbyseason(season = season, year = year)
    data = consolidate_data(data)
    with open("data-anichart.json", 'w',encoding = 'utf-8') as f:
        json.dump(data,f)
    with open("data-anichart.json",'r', encoding = 'utf-8') as f:
        data = json.load(f)
    replace_season(data, f"{season}-{year}")
    data = [Show(**show) for show in data]
    #print("cleaning data")
    #headers,shows = cleanapidata(data, season = SeasonCharts.buildseason(season,year))
    #print("serilizing")
    #serializeshows("output-anichart.json",shows)
    print("Converting to Standard")
    print(convertshowstostandard(data))
    print('done')
