## Builtin
import datetime
import re

## This Module
from aldb2 import SeasonCharts, WebModules
from aldb2.WebModules import myanimelist
from aldb2.WebModules.myanimelist import scraping

## Third Party
from alcustoms.web import requests as alrequests

SEASONURL = "https://myanimelist.net/anime/season/{year}/{season}"

def getshows_fromseasonpage(season, year):
    """ Current Query Method for getshowsbyseason """
    session = alrequests.getbasicsession()
    aseason = SeasonCharts.buildseason(season,year)

    shows = []
    url = SEASONURL.format(season = season.lower(), year = year)

    EPSRE = re.compile("(?P<episodes>\d+) eps", re.IGNORECASE)
    DATERE = re.compile("(?P<datetime>\w{3} \d+, \d+, \d{2}:\d{2}) \((?P<timezone>\w{3})\)", re.IGNORECASE)

    shows = []
    session = alrequests.CachedSession()
    #session = alrequests.getbasicsession()

    r = session.get(url)
    soup = alrequests.response_to_soup(r)
    categories = soup(class_="seasonal-anime-list")
    with open("test.html", 'w', encoding = "utf-8") as f:
        f.write(str(soup))
        

    for cat in categories:

        category = " ".join(cat.find(class_="anime-header").stripped_strings)

        for showele in cat(class_ = "seasonal-anime"):

            titleele = showele.find(class_ = "link-title")
            engtitle = " ".join(titleele.stripped_strings)
            mallink = titleele['href']
            malid = myanimelist.parse_siteid(mallink)

            prodsrcele = showele.find(class_ = "prodsrc")
            studio = " ".join(prodsrcele.find(class_ = "producer").stripped_strings)
            episodes = None
            if (epsmatch := EPSRE.search(" ".join(prodsrcele.find(class_ = "eps").stripped_strings))):
                episodes = epsmatch.group("episodes")
            
            genresele = showele.find(class_ = "genres-inner")
            genres = [" ".join(genre.stripped_strings) for genre in genresele(class_ = "genre")]

            try:
                imageele = showele.find(class_ = "image")
                image = (img := imageele.find("img"))['src']
            except KeyError:
                image = img['data-src']
            except Exception as e:
                raise e

            synopsisele = showele.find(class_ = "synopsis")
            synopsis = " ".join(synopsisele.find(class_ = "preline").stripped_strings)

            infotopele = showele.find(class_ = "information")
            infoele = showele.find(class_ = "info")
            ## We can pull showtype from category
            startdate = None
            if (start := infoele.find(class_ = "remain-time")):
                if (datematch := DATERE.search(" ".join(start.stripped_strings))):
                    startdate = datetime.datetime.strptime(datematch.group("datetime"),"%b %d, %Y, %H:%M")
                    if datematch.group("timezone") == "JST":
                        startdate.replace(tzinfo = WebModules.JST)

            continuing = "continuing" in category.lower()

            medium = category
            
            if category.lower() in ["tv (new)", "tv (continuing)"]:
                medium = "TV"

            if "Hentai" in genres:
                medium = "hentai"

            shows.append(Show(malid, season = aseason,  english_title=engtitle,
            medium = medium, continuing = continuing,
            summary=synopsis, tags = genres, startdate= startdate,episodes= episodes, images = image,
            studios = [studio,], links = [("Mal ID", mallink),]))

    for show in shows:
        ## TODO!!!: right now the only link we're scraping is the mal link: if this changes, this code will break
        scraping.findmissing_showstats(show, session = session)

    return shows
    


#####################################################################
"""
                            ALDB2 INTEGRATION
                                                                  """
#####################################################################

CHARTNAME = "MyAnimeList"

class Show(SeasonCharts.Show):
    ## For flexibility, MyAnimeList japanese title can be None
    def __init__(self, malid, season, japanese_title = None, **kw):
        super().__init__(chartsource= [(CHARTNAME,malid),], season = season, japanese_title= japanese_title, **kw)

def getshowsbyseason(season,year, querymethod = getshows_fromseasonpage):
    """ Returns shows given the season and year """
    shows = querymethod(season,year)
    return shows

def convertshowstostandard(shows, showfactory = SeasonCharts.Show):
    """ Converts shows that are created by this module into the Standardized Format for the SeasonCharts module """
    ## Mal.Show is effectively idental to SeasonCharts.Show at the moment
    return shows



if __name__ == "__main__":
    getshows_fromseasonpage("Winter", 2021)
          