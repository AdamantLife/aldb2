## Builtin
import calendar
import datetime
import functools
import json
import re
import traceback
import warnings
## Third Party
import bs4
## Custom Module
from alcustoms import web
from alcustoms.web import requests as alrequests
from aldb2 import SeasonCharts

CHARTNAME = "Livechart"

## 1/2020 Update: changed from /all to /tv
URLFORMAT = r"https://www.livechart.me/{season}-{year}/tv"
MORELINKSAPI = r"https://www.livechart.me/api/v1/anime/{livechartid}/streams?country_code=AUTO"

ALTERNATETITLESRE = re.compile("(?:\"(.*?)\"[,\]])")
SEASONRE = re.compile("""(?P<season>\w+) (?P<year>\d+)""")
TAGIDRE = re.compile("""/tags/(?P<tagid>\d+)""")
DATERE = re.compile("""
(?P<month>[a-zA-Z]+)?\s*
(?:(?P<day>\d+),)?\s*
(?P<year>\d+)\s*
(?P<time>at\s*
    (?P<hour>\d{1,2}):
    (?P<minute>\d{2})
    (?P<apm>[a-zA-Z]+)
)?\s*
(?P<timezone>
      [a-zA-Z]+
    | [+-]?\d{4}
)?
""",re.VERBOSE)
EPISODESRE = re.compile("""(?P<episodes>(?:\d+|\?)) eps × (?P<runtime>(?:\d+|\?)) min""")
LINKRE = re.compile("""(?P<site>.*)-icon""")

MONTHNAME = list(calendar.month_name)
MONTHABBR = list(calendar.month_abbr)

sessiondecorator = alrequests.session_decorator_factory(useragent = True, referrer = "https://www.livechart.me")

def checkcsrf(func):
    """ Decorator for functions that require livechart's csrf token (_livechart_session; i.e.- API calls) """
    @functools.wraps(func)
    @sessiondecorator
    def wrapper(*args,session = None, **kw):
        if "_livechart_session" not in session.cookies: pass
        return func(*args,session = session, **kw)
    return wrapper

class ParserWarning(Warning):
    pass

class Show():
    """ A livechart.me Show Object """
    def __init__(self, japanese, romaji, english, alternatetitles, season, showtype, livechartid, tags, img, studios, startdate, episodes, runtime, notes, summary, links):
        self.japanese=japanese
        self.romaji=romaji
        self.english=english
        if alternatetitles is None: alternatetitles = []
        self.alternatetitles=alternatetitles
        self.season = season
        self.showtype=showtype
        self.livechartid=livechartid
        self.tags=tags
        self.img=img
        self.studios=studios
        self.startdate=startdate
        self.episodes = episodes
        self.runtime = runtime
        self.notes=notes
        self.summary=summary
        self.links=links
    def serialize(self):
        return {'japanese': self.japanese, 'romaji': self.romaji, 'english': self.english,
                'alternatetitles': self.alternatetitles, 'season': self.season, 'showtype': self.showtype,
                'livechartid': self.livechartid, 'tags': self.tags, 'img': self.img, 'studios': self.studios,
                'startdate': self.startdate.strftime("%H:%M %d/%m/%Y %z"), 'episodes': self.episodes, 'runtime': self.runtime,
                'notes': self.notes, 'summary': self.summary, 'links': self.links}
    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.japanese} ({__name__})"

def getshowsbyseason(season,year):
    """ Returns a list of Show objects for the given season and year """
    url = URLFORMAT.format(season = season.lower(), year = year)
    session = alrequests.getbasicsession(useragent = True)

    soup = alrequests.GET_soup(url, session = session)
    try:
        if soup.ok: pass
    except AttributeError: pass
    else:
        raise RuntimeError(f"Bad Response: {soup.status_code}: {soup.reason}")
    return parsesoup(soup, session = session)

@sessiondecorator
def parsesoup(soup, session = None):
    """ Parses the soup from a livechart.me page """
    ## Parse the Season
    titleele = soup.find(class_="page-header-box").find("h1")
    seasonresearch = SEASONRE.search(" ".join(titleele.stripped_strings))
    season,year = seasonresearch.group("season"),seasonresearch.group("year")
    season = SeasonCharts.buildseason(season,year)
    ## All articles are contained in the main element
    main = soup.find("main")
    shows = []
    for article in main("article"):
        ## Use helper function to convert to Show Object
        show = parsearticle(article,session = session, season = season)
        if show: shows.append(show)
    return shows

def convertmonth(month):
    """ Helper Function to determine month and convert it to one-index if necessary """
    if isinstance(month,int): return month
    if month in MONTHNAME: return MONTHNAME.index(month)
    if month in MONTHABBR: return MONTHABBR.index(month)
    ## For right now, if we can't parse it, we'll just return January
    return 1

## checkcsrf has sessiondecorator built-in
@checkcsrf
def getmorelinks(livechartid, session = None):
    """ Checks the morelinks API for more links """
    url = MORELINKSAPI.format(livechartid = livechartid)
    resp = alrequests.GET_json(url,session = session)
    links = []
    if isinstance(resp,dict):
        for link in resp['items']:
            links.append((link['display_name'],link['url']))
    return links
    
    
@sessiondecorator
def parsearticle(article, session = None, season = None):
    """ Parse an article into a Show Object """
    showtypes = list(article['class'])
    if "anime" not in showtypes:
        return None
    showtypes.remove("anime")
    try:
        titleele = article.find("h3",class_ = "main-title")
        taglistele = article.find("ol",class_="anime-tags")
        tageles = taglistele("li")
        body = article.find("div",class_="anime-card")
        imgele = body.find("div", class_="poster-container").find("img")
        detailsele = body.find("div", class_="anime-info")
        studiosele = detailsele.find("ul",class_="anime-studios")
        dtele = detailsele.find("div",class_="anime-date")
        episodesele = detailsele.find("div",class_="anime-episodes")
        extraele = body.find("div",class_="anime-extras")
        synopsisele = body.find("div", class_ = "anime-synopsis")
        relatedele = article.find("ul",class_="related-links")
        linkseles = relatedele("a")
    except Exception as e:
        exc = traceback.format_exc()
        if titleele:
            try:
                title = titleele.attrs.get('data-japanese')
            except:
                warnings.warn(f"Could not Parse the following element:\n{article}\n{exc}",ParserWarning)
            else:
                warnings.warn(f"Could not Parse {title}:\n{exc}",ParserWarning)
        else:
            warnings.warn(f"Could not Parse the following element:\n{article}\n{exc}",ParserWarning)
        return
    japanese = article.attrs.get('data-native')
    romaji = article.attrs.get('data-romaji')
    english = article.attrs.get('data-english')

    alt_titles = article.attrs.get('data-alternate')
    alternatetitles = ALTERNATETITLESRE.findall(alt_titles)

    showtype = " ".join(showtypes)
    livechartid = article.attrs.get("data-anime-id")
    tags = []
    for tagele in tageles:
        tagname = " ".join(tagele.stripped_strings)
        try:
            tagurl = tagele.find("a")['href']
            tagidresearch = TAGIDRE.search(tagurl)
            tagid = tagidresearch.group("tagid")
        except: tagid = None
        tags.append((tagid,tagname))
    img = imgele['src']
    studios = [" ".join(studioele.stripped_strings) for studioele in studiosele]
    dti = " ".join(dtele.stripped_strings)
    
    try:
        dateresearch = DATERE.search(dti)
        datedict = dateresearch.groupdict()
        ############### Validation
        ## Month
        if not datedict.get("month"): datedict['month'] = 1
        else: datedict['month'] = convertmonth(datedict['month'])
        ## Day
        if not datedict.get("day"): datedict['day'] = 1
        ## Year
        if not datedict.get("year"): datedict['year'] = datetime.MINYEAR
        ## Time
        if not datedict.get("time"):
            datedict['hour'] = 0
            datedict['minute'] = 0
        else:
            if datedict.get("apm"):
                if datedict['apm'].lower() == "pm":
                    ## + 11 because 24-hour clock is base 0, whereas 12-hour is base 1
                    datedict['hour'] = int(datedict['hour']) + 11
        ## Timezone
        ## TODO: THIS SECTION SHOULD BE UPDATED AT SOME POINT TO PROPERLY PARSE TZ
        if not datedict.get("timezone"): datedict["timezone"] = web.JST
        else:
            if datedict['timezone'] == "JST": datedict['timezone'] = web.JST
            else: datedict['timezone'] = web.EST
        startdate = datetime.datetime.strptime(f"{datedict['hour']}:{datedict['minute']} {datedict['day']}/{datedict['month']}/{datedict['year']}","%H:%M %d/%m/%Y")
        startdate = startdate.replace(tzinfo = datedict['timezone'])
    except:
        traceback.print_exc()
        startdate = datetime.datetime(datetime.MINYEAR,1,1).replace(tzinfo = web.JST)

    notes = ", ".join(" ".join(extra.stripped_strings) for extra in extraele("div",class_="anime-extra"))
    episodes = 0
    runtime = None
    if episodesele:
        episoderesearch = EPISODESRE.search(" ".join(episodesele.stripped_strings))
        if episoderesearch:
            episodes = episoderesearch.group("episodes")
            if episodes == "?": episodes = 0
            runtime = episoderesearch.group("runtime")
            if runtime == "?": runtime = None
            
    summary = "\n".join(" ".join(p.stripped_strings) for p in synopsisele("p"))

    links = []
    for link in linkseles:
        linktype = [LINKRE.search(clss).group("site") for clss in link['class'] if LINKRE.search(clss)]
        if not linktype: continue
        ## Since we're just blindly checking, we'll take the first, whichever it may be
        linktype = linktype[0]
        if linktype == "more":
            links.extend(getmorelinks(livechartid, session = session))
        else:
            links.append((linktype,link['href']))

    return Show(japanese=japanese, romaji=romaji, english=english, alternatetitles=alternatetitles,
                season = season, showtype=showtype, livechartid=livechartid, tags=tags, img=img, studios=studios,
                startdate=startdate, episodes=episodes, runtime=runtime, notes=notes, summary=summary, links=links)

def serializeshows(file,shows):
    """ Creates a json file containing the shows """
    with open(file,'w', encoding = 'utf-8') as f:
        json.dump(shows,f,default = Show.serialize)

def convertshowstostandard(data, season = None, showfactory = SeasonCharts.Show):
    """ Converts a full collection of API data to a list of standard Show Objects (via converttostandard)

    season will be pased to converttostandard
    """
    out = list()
    for show in data:
        out.append(converttostandard(show, season, showfactory = showfactory))
    return out

def converttostandard(show, season = None, showfactory = SeasonCharts.Show):
    """ Converts an Livechart Show to a standard Show Object """
    if not isinstance(show,Show):
        raise TypeError("converttostandard requires an AniChart Show Object.")
    chartsource = [(CHARTNAME, show.livechartid),]

    if not season:
        season = show.season
    japanese_title = show.japanese
    romaji_title = show.romaji
    english_title = show.english
    additional_titles = show.alternatetitles
    medium = show.showtype
    continuing = "leftovers" in [note.lower() for note in show.notes]
    summary = f"(From {CHARTNAME})\n{show.summary}"

    tags = [(tag[1],False) for tag in show.tags]
    
    startdate = show.startdate.strftime(SeasonCharts.DTFORMAT)

    episodes = show.episodes
    images = [show.img,]
    studios = show.studios
    ## Livechart has default/null value links
    links = [link for link in show.links if link[0] and link[1]]

    return showfactory(chartsource = chartsource, season = season,
                             japanese_title = japanese_title, romaji_title = romaji_title,
                             english_title = english_title, additional_titles = additional_titles,
                             medium = medium, continuing = continuing, summary = summary,
                             tags = tags, startdate = startdate, episodes = episodes, images = images,
                             studios = studios, links = links)

if __name__ == "__main__":
    season,year = "fall",2017
    
    print("parsing")
    getshowsbyseason(season,year)
    
    print("serializing")
    serializeshows("data-livechart.json",shows)
    with open("data-livechart.json",'r') as f:
        data = json.load(f)
    data = [Show(**show) for show in data]
    print(convertshowstostandard(data,season = SeasonCharts.buildseason(season,year)))
    print("done")
