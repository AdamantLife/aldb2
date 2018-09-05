## This Module
from aldb2 import Calendar
## This module will likely be added to This Module in the future
from ChartMaker import classes
## Builtin
import csv
import datetime
import itertools
import re
from xml.etree import ElementTree as ET
## Custom Module
from alcustoms.methods import isiterable
from alcustoms import web

URL = r"https://cal.syoboi.jp"
CALENDARURL = r"http://cal.syoboi.jp/tid/{showboyid}/time"
FINDURL = r"http://cal.syoboi.jp/find"
FINDPARAMS = {
    "type":"quick",
    "sd":"1",
    "kw":"",
    "exec":"??",
    }

sessiondecorator = web.session_decorator_factory(referrer = URL)

def getshowboyurl(show):
    """ Returns a Showboy Calendar URL formatted with Show's Showboy ID (Raises AttributeException if show does not have showboyid)"""
    if not show.showboyid: raise AttributeError("Show does not have a Showboy ID")
    return CALENDARURL.format(showboyid=show.showboyid)

#################################################################
"""
                           XML METHODS
                                                              """
#################################################################
XMLAPI = r"http://cal.syoboi.jp/db.php?"
@sessiondecorator
def getxmlapi(command, *, session = None,**kw):
    """ An XML response from the API using the given settings.
    
    Requires the xml command.
    """
    kw["Command"] = command
    resp = web.requests_GET_html(XMLAPI,session = session, params = kw)
    return ET.fromstring(resp)

@sessiondecorator
def getepisodes_xml(shows, *, session = None):
    """ Uses the XML API available for syoboi """
    episodes = list()

    ## Get XML
    root = getxmlapi("ProgLookup", session = session, TID = ",".join([str(show.showboyid) for show in shows]), JOIN = "SubTitles")

    ## Parse
    airings = list()
    progs = root.find("ProgItems")
    for progitem in root.iter("ProgItem"):
        ## At some point we might convert his ChID to the channel name. Not really important at this point.
        channel = progitem.find("ChID").text
        dt = progitem.find("StTime").text
        dt = datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S").replace(tzinfo = web.JST)
        episode = progitem.find("Count").text
        if episode is None: episode = -1
        ## Casting to Float for recap (and other.5) Episode Numbers
        episode = float(episode)
        ## Convert back for Normal Episode Numbers when possible.
        if episode.is_integer(): episode = int(episode)
        title = progitem.find("STSubTitle").text
        showid = progitem.find("TID").text
        airing = Calendar.EpisodeAiring(channel = channel, dt = dt, episode = episode, title = title)
        airing.show = int(showid)
        airings.append(airing)

    for show in shows:
        eps = sorted([air for air in airings if air.show == show.showboyid])
        for ep in eps: ep.show = show
        episodes.append(eps)

    return episodes

#################################################################
"""
                           SOUP METHODS
                                                              """
#################################################################
URLMATCHERE = re.compile("tid/(?P<id>\d+)")

@sessiondecorator
def gettids_soup(series, session = None):
    out = list()
    for ser in series:
        params = dict(FINDPARAMS)
        params['kw'] = ser
        resp = session.get(FINDURL,params = params)
        url = resp.url
        urlresearch = URLMATCHERE.search(url)
        if urlresearch:
            out.append(urlresearch.group("id"))
        else:
            out.append(url)

    return out

"""
     CALENDAR SOUP METHODS HAVE BEEN SUPERCEDED BY XML METHODS!

      They are retained as a backup method if XML-API breaks.
"""

ROWRE = re.compile("""PID.+""")
DTRE  = re.compile("""(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\(.\) ?(?P<hour>\d{,2}):(?P<minute>\d{2})""")
def getepisodeairingsfromsoup(soup):
    """ Gets EpisodeAirings from Soup """
    airings = []
    
    table = soup.find("table",attrs={"id":"ProgList"})
    for row in table.find_all("tr",id=ROWRE):
        channel = " ".join(row.find("td",attrs={"class":"ch"}).stripped_strings)
        dt = " ".join(row.find("td",attrs={"class":"start"}).stripped_strings)
        episode = " ".join(row.find("td",attrs={"class":"count"}).stripped_strings)
        title = " ".join(row.find("td",attrs={"class":"subtitle"}).stripped_strings)

        ## Convert Wierd Japanese times (i.e.- 26:30)
        dtresearch = DTRE.search(dt)
        year,month,day,hour,minute = dtresearch.groups()
        daydelta = int(hour) // 24
        hour = int(hour) % 24

        dtobj = datetime.datetime(int(year),int(month),int(day),hour,int(minute),tzinfo=web.JST) + datetime.timedelta(days = daydelta)

        air = Calendar.EpisodeAiring(channel,dtobj,episode,title)

        airings.append(air)

    return airings

@sessiondecorator
def getepisodes_soup(shows,session = None):
    """ Gather method by parsing the Show's Calendar page on shoboi """
    episodes = list()
    for show in shows:
        print(f"Show: {show.name}")
        url = getshowboyurl(show)
        soup = web.requests_GET_soup(url,session = session)
        airings = getepisodeairingsfromsoup(soup)
        print(f"Got {len(airings)} airings")
        airings = sorted(airings)
        for airing in airings: airing.show = show
        episodes.append(airings)
    return episodes


if __name__=="__main__":
    FILE = r"C:\Users\Reid\Dropbox\][Video Editing\AnimeLife\__Record W2018.xlsx"
    RECORD = classes.SeasonRecord(FILE)

    SHOWS = """
    A Place Further Than the Universe
citrus
DARLING in the FRANXX
IDOLiSH 7
Junji Ito Collection
Kokkoku
March Comes in Like a Lion 2nd Season
Overlord II
Record of Grancrest War
The Ancient Magus' Bride
"""
    from alcustoms.methods import linestolist
    import pprint
    SHOWS = linestolist(SHOWS)
    S1 = [show.strip() for show in SHOWS if show.strip()]
    S2 = RECORD.showstats.getshowbyname(*S1)
    for s1,s2 in zip(S1,S2):
        if s2 is None:
            print(f"Could not find {s1} ({s2})")
    SHOWS = [show for show in S2 if show]
    pprint.pprint(SHOWS)

    def gettids():
        
        #SHOWS = """
        #"""
        #
        series = [show for show in RECORD.showstats.shows.values() if not show.showboyid]
        seriesstring = '\n'.join(str(show) for show in series)
        print(f"Getting TIDS for:\n{seriesstring}")
        tids = gettids_soup(series)

        for show,tid in zip(series,tids): print(f"{show}:\t{tid}")

        print('done')

    def outputcalendar_soup():
        shows = None

        airings = Calendar.getshowairings(FILE,shows = shows, gathermethod = getepisodes_soup)
        Calendar.outputGoogleCalendar(airings)

    def outputcalendar_xml(shows = None):

        airings = Calendar.getshowairings(FILE, shows = shows, gathermethod = getepisodes_xml)
        Calendar.outputGoogleCalendar(airings)
        

    #gettids()
    #outputcalendar_soup()
    outputcalendar_xml(shows = SHOWS)
