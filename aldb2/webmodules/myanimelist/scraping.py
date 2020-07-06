""" aldb2.webmodules.myanimelist.scraping


    This module is provided for when the API is broken. Please use the API when available.
"""

## Builtin
import csv                                  ## Stat Scraping
import datetime                             ## Stat Scraping
import functools                            ## Utility
import json                                 ## Stat Scraping
import pathlib                              ## Stat Scraping
import re                                   ## Stat Scraping
import time                                 ## 
## This Library
from aldb2 import webmodules                ## Stat Scraping (Timezones)
from aldb2.webmodules import myanimelist    ## General
from aldb2.Core import core as coremodules  ## Stat Scraping
from aldb2.Core import sql                  ## Stat Scraping
## Custom Module
from alcustoms import decorators            ## Utility
from alcustoms import web                   ## Whole Module
from alcustoms.web import requests as alrequests
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
        return re.compile("(?P<category>type|episodes|status|aired|premiered|broadcast|producers|licensors|studios|source|genres|duration|rating)\s*:\s*(?P<value>.+)", re.IGNORECASE)

    def parse_stats(self):
        try:
            content = self.soup.find(id = "content")
            ## All the information is kept in the first Row of a Table's Body
            ## DEV NOTE: Chrome seems to auto add TBody to table: source html printout doesn't include it
            content = content.find("table").find("tr")
            ## Sidebar is first td in Row
            self.parse_sidebar(content.find("td"))
        except AttributeError as e:
            ## print(self.resp.ok)
            ## print(self.resp.text)
            raise e
        

    def parse_sidebar(self, sidebar):
        ## Parsing Methods
        ## Primary code below double hash line
        def joinstring(sibling):
            try:
                return " ".join(sibling.stripped_strings)
            except:
                return str(sibling)

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
                    if key == "aired":
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
                                    t.replace(tzinfo = webmodules.JST)
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


if __name__ == "__main__":
    from alcustoms.web.requests import CachedSession
    print(getshowstats("https://myanimelist.net/anime/40221/Kami_no_Tou", session = CachedSession()))

