""" aldb2.WebModules.myanimelist.scraping


    This module is provided for when the API is broken. Please use the API when available.
"""

## Builtin
import csv                                  ## Stat Scraping
import datetime                             ## Stat Scraping
import functools                            ## Utility
import json                                 ## Stat Scraping
import pathlib                              ## Stat Scraping
import re                                   ## Stat Scraping
import traceback                            ## Error Output for findmissing_showstats
## This Library
from aldb2 import WebModules                ## Stat Scraping (Timezones)
from aldb2.WebModules import myanimelist    ## General
from aldb2.Core import core as coremodules  ## Stat Scraping
from aldb2.Core import sql, getseason       ## Stat Scraping, Determine Premiere Season if Aired is not available
from aldb2.Anime.anime import parseanimeseason_toobject   ## Season Utilities
## Custom Module
import al_decorators as decorators            ## Utility
import AL_Web as web                   ## Whole Module
from AL_Web import requests as alrequests
## Third Party
import bs4                                  ## Whole Module

#################################################
"""
                Utility Functions

    Functions written for this module.
"""
#################################################
def _checkmalidurl(ba):
    """ Allows an url argument to be MALID instead, and replaces it with a properly formated url."""

    url = ba.arguments.get('url')

    ## Check if url is MALID as an INT
    malid = False
    try:
        malid = int(url)
    except:
        ## Check if is already url
        malid = myanimelist.parse_siteid(url)

    ## If we couldn't determine an ID, then return and let the method handle invalids
    if not malid:
        return
    ## Otherwise, we can convert into url
    ba.arguments['url'] = myanimelist.format_siteid(malid)

    
malid_deco = decorators.signature_decorator_factory(_checkmalidurl)


#################################################
"""
                General Functions
"""
#################################################

@alrequests.sessiondecorator
@malid_deco
def getanimepage(url, session = None):
    """ Returns the requests.response object for the webpage for the given MAL Anime ID. """
    if not myanimelist.is_siteurl(url):
        raise ValueError("Invalid site url")
    return session.get(url)

@alrequests.sessiondecorator
@malid_deco
def getanimesoup(url,session = None):
    """ Returns the BSoup for the MAL anime page with the given MAL Anime ID or url. """
    return alrequests.GET_soup(url)

def joinstring(sibling):
    try:
        return " ".join(sibling.stripped_strings)
    except:
        return str(sibling)


##################################################
"""
                Show Stats Scraping
"""
##################################################
MAL_LOCK = web.RequestLock(timeout = 2)

class Scraper():
    @alrequests.sessiondecorator
    @malid_deco
    def __init__(self, url, session = None):
        ##self.resp = alrequests.GET(url)
        ##self.soup = alrequests.response_to_soup(self.resp)
        with MAL_LOCK:
            self.soup = getanimesoup(url,session)
        self.stats = {}

    @property
    def alt_titles_re(self):
        return re.compile("\s*alternative\s*titles\s*", re.IGNORECASE)
    @property
    def information_re(self):
        return re.compile("\s*information\s*",re.IGNORECASE)
    @property
    def title_re(self):
        return re.compile("\s*(?P<type>(?:English|Synonyms|Japanese)):\s*(?P<title>.*?)\s*$")
    @property
    def statistics_re(self):
        return re.compile("\s*statistics\s*",re.IGNORECASE)
    @property
    def informationvalues_re(self):
        return re.compile("(?P<category>type|episodes|status|aired|airing|premiered|broadcast|producers|licensors|studios|source|genres|duration|rating)\s*:\s*(?P<value>.+)", re.IGNORECASE)

    def parse_stats(self):
        try:
            content = self.soup.find(id = "content")
            ## All the information is kept in the first Row of a Table's Body
            ## DEV NOTE: Chrome seems to auto add TBody to table: source html printout doesn't include it
            content = content.find("table").find("tr")
            ## Sidebar is first td in Row
            self.parse_sidebar(content.find("td"))
            self.parse_related(self.soup)

        except AttributeError as e:
            ## print(self.resp.ok)
            ## print(self.resp.text)
            raise e
        

    def parse_sidebar(self, sidebar):
        ## Parsing Methods
        ## Primary code below double hash line

        def parse_titles(sidebar):
            alt_titles_header = sidebar.find("h2", string=self.alt_titles_re)

            ## No Alternative titles (very rare)
            if not alt_titles_header:
                ## Return the information header
                return sidebar.find("h2", string=self.information_re)

            for sibling in alt_titles_header.next_siblings:
                text = joinstring(sibling)
                ## Done with Alternative Titles
                if self.information_re.search(text):
                    return sibling
                if (research := self.title_re.search(text)):
                    kind, title = research.group('type'), research.group('title').strip()
                    if kind == "English": key = 'english_title'
                    elif kind == "Japanese": key = 'japanese_title'
                    else: key = "alternative_titles"
                    if key == "alternative_titles":
                        self.stats[key] = [t.strip() for t in title.split("\n")]
                    else:
                        self.stats[key] = title
            raise RuntimeError("Could not locate Information Header")

        def parse_information(information_header):
            for sibling in information_header.next_siblings:
                text = joinstring(sibling)
                ## Done with Information section
                if self.statistics_re.search(text):
                    return sibling
                if (research := self.informationvalues_re.search(text)):
                    key = research.group('category').lower()
                    value = research.group('value')
                    if key in ["aired","airing"]:
                        if (firstepisode := re.compile("\s*(.*?)\s+to.*$", re.IGNORECASE).search(value)):
                            ## Sometimes "aired" is vague (i.e.- May, 2020 to ?)
                            try:
                                if(date := datetime.datetime.strptime(firstepisode.group(1), "%b %d, %Y")):
                                    self.stats['first_episode'] = date
                            except: pass
                    elif key == "broadcast":
                        if (airtime := re.compile(".*?\s+(?P<time>\d+:\d+)(?:\s+\((?P<timezone>\w{3})\))").search(value)):
                            if airtime:
                                t = datetime.datetime.strptime(airtime.group("time"),"%H:%M")
                                if (timezone := airtime.group("timezone")) and timezone.lower() == "jst":
                                    t.replace(tzinfo = WebModules.JST)
                                self.stats['airtime'] = t
                    elif key in ["producers", "licensors","studios"] and value.strip() != "None":
                        self.stats[key] = [p.strip() for p in value.split(",")]
                    elif key == "genres":
                        ## Technically could try pattern matching to strip out repeats
                        ## but this seems simpler
                        ## Results should be spans with display:none
                        genres = sibling("span", itemprop = "genre")
                        self.stats['genres'] = [genre.string if genre.strings else " ".join(genre.stripped_strings) for genre in genres]
                    elif key == "duration":
                        if (duration := re.compile(".*?(?:(?P<hour>\d+\s)*hr)?.*?(?:(?P<minute>\d+)\s*min)").search(value)):
                            if (hours:=duration.group("hour")): hours = int(hours)
                            else: hours = 0
                            if (minutes:=duration.group("minute")): minutes = int(minutes)
                            else: minutes = 0
                            self.stats['runtime'] = datetime.timedelta(hours = hours, minutes = minutes)
                    ## Keys that don't need processing
                    elif key  in ["type","source","rating"] and value.lower() != "none":
                        self.stats[key] = value
                        
            raise RuntimeError("Could not locate Statistics Header")

        ######################
        ######################
        
        information = parse_titles(sidebar)
        if information is None: raise ValueError("Could not find Information Section")
        statistics = parse_information(information)
        ## TODO: parse statistics

    def parse_related(self, soup):
        relations = {}
        related = soup.find(class_="anime_detail_related_anime")

        if related:
            """Note: related table is an absolute mess:

            Sometimes it is misformatted like this:
                <table>
                    <tr> <== Should be <tbody>
                        <tr><td>[...etc]</td></tr>
                        <tr><td>[...etc]</td></tr>
                    </tr>
                </table>

            Othertimes it is misformatted like this:
                <table>
                    <tr>
                        <td>[Category:]</td>
                        <td>[List of Links]</td>
                        <tr> <== Category Rows are nested within themselves
                            <td>[Category:]</td>
                            <td>[List of Links]</td>
                        </tr>
                    </tr>
                </table>

            Hence why we we're just going to iterfind categories and then iterfind values
            """
            ## We are assuming that all categories have "fw-n" as a class (font-weight: 400!important)
            CATCLASS = "fw-n"
            categories = related("td", class_ = CATCLASS)
            ## Check the next, un-processed TD to find siblings that contain links
            for category in categories:
                animes = []
                next_td = category.find_next_sibling("td")

                ## Check the next <td>: if it is not a Category, add it to animes
                while next_td and CATCLASS not in next_td['class']:
                    links = next_td("a")
                    for link in links:
                        animes.append((link['href'], joinstring(link)))

                    next_td = next_td.find_next_sibling("td")
                
                ## Done with current category
                relations[joinstring(category).rstrip(":")] = animes

        self.stats['relations'] = relations

""" Useful Info

Relevant class="itemprop" elements-
    * "description": <span> full description
    * "name": <span> title, romanized (Use child of h1; other is a heirarchal link may be abbreviated)
    * "image": <img> Small Poster

The rest of the information has to be scraped based off of formatting...
"""
def getshowstats(url,session = None):
    scraper = Scraper(url = url, session = session)
    scraper.parse_stats()
    return scraper.stats


def findmissing_showstats(show, url = None, session = None, pipe = None):
    """
        Fills in info that is often missing from Charts (may be updated in the future to compare all info).

        Pipe- print output: currently used for interfacing with SeasonCharts.gammut
    """
    if pipe is None:
        def pipe(output, verbose = False):
            pass
    if not url:
        ids = [url for link in show.links if (url := myanimelist.parse_siteid(link[1]))]
        malinfo = None 
        for link in ids:
            try:
                pipe(f">>> {show.english_title or show.romaji_title or show.japanese_title}({link})")
                malinfo = getshowstats(link, session = session)
            except Exception as e:
                pipe(f">>> Failed to get MAL info for: {show.romaji_title if show.romaji_title else show.english_title}({link})")
                pipe(traceback.format_exc(), verbose = True)
            if malinfo: break
    else:
        malinfo = getshowstats(url)

    if not malinfo: return

    if not show.japanese_title and malinfo.get("japanese_title"):
        show.japanese_title = malinfo['japanese_title']

    for name in malinfo.get("additional_titles",[]):
        if name not in show.additional_titles:
            show.additional_titles.append(name)

    if not show.startdate and malinfo.get("first_episode"):
        show.startdate = malinfo['first_episode'].replace(tzinfo = WebModules.JST)

    ## NOTE: for both continuing and renewal, we always take True if possible
    if (premiered := malinfo.get("premiered")) or (first_episode := malinfo.get("first_episode")):
        if not premiered:
            premiered = getseason(first_episode) + f"-{first_episode.year}"
        if (continuing := parseanimeseason_toobject(premiered) < parseanimeseason_toobject(show.season)):
            show.continuing = continuing

    if (renewal := bool(malinfo['relations'].get("Prequel"))):
        show.renewal = renewal

    if not show.runtime and malinfo.get("runtime"):
        show.runtime = malinfo['runtime']

    if not show.medium and malinfo['type']:
        show.medium = malinfo['type']

    ## Hard overriding the next two medium types
    if (runtime := malinfo.get('runtime')) and ((runtime.total_seconds() / 60 ) < 17):
        show.medium = show.medium + " SHORT"

    if ("rating" in malinfo and "hentai" in malinfo['rating'].lower()) or "hentai" in [genre.lower() for genre in malinfo['genres']]:
        show.medium = "Hentai"


if __name__ == "__main__":
    from AL_Web.requests import CachedSession
    print((malinfo := getshowstats("https://myanimelist.net/anime/80", session = CachedSession())))
    for cat,vals in malinfo['relations'].items():
        print(cat, len(vals))