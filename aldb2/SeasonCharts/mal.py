## Builtin
import datetime
import re

## This Module
from aldb2 import SeasonCharts, WebModules
from aldb2.WebModules import myanimelist
from aldb2.WebModules.myanimelist import scraping

## Third Party
from AL_Web import requests as alrequests

SEASONURL = "https://myanimelist.net/anime/season/{year}/{season}"

def stripped_strings(ele):
    return " ".join(ele.stripped_strings)

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
           

    for cat in categories:

        category = stripped_strings(cat.find(class_="anime-header"))

        for showele in cat(class_ = "seasonal-anime"):

            titleele = showele.find(class_ = "link-title")
            engtitle = stripped_strings(titleele)
            mallink = titleele['href']
            malid = myanimelist.parse_siteid(mallink)
            
            genresele = showele.find(class_ = "genres-inner")
            genres = [stripped_strings(genre) for genre in genresele(class_ = "genre")]

            try:
                imageele = showele.find(class_ = "image")
                image = (img := imageele.find("img"))['src']
            except KeyError:
                image = img['data-src']
            except Exception as e:
                raise e

            synopsisele = showele.find(class_ = "synopsis")
            synopsis = stripped_strings(synopsisele.find(class_ = "preline"))

            propseles = synopsisele(class_="property")
            for property in propseles:
                items = property.parent(class_="item")
                prop = stripped_strings(property.find(class_="caption")).lower()
                if prop.endswith("s"): prop = prop[:-1]
                if prop == "studio":
                    studios = [stripped_strings(studio) for studio in items]
                elif prop == "theme":
                    genres.extend([stripped_strings(theme) for theme in items])
                elif prop == "demographic":
                    genres.append(stripped_strings(items[0]))
                elif prop == "source": pass
                else:
                    raise Warning(f"Unknown MAL List property: {prop}")

            infotopele = showele.find(class_ = "information")
            infoele = showele.find(class_ = "info")

            episodes = None
            if (epsmatch := EPSRE.search(stripped_strings(infoele))):
                episodes = epsmatch.group("episodes")
            ## We can pull showtype from category
            startdate = None
            if (start := infoele.find(class_ = "remain-time")):
                if (datematch := DATERE.search(stripped_strings(start))):
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
            studios = studios, links = [("Mal ID", mallink),]))

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
          