## Builtin
import re

## Third Party
from AL_Web import requests

""" Notes    

    Funimation has a forward-facing url (homepage) for each show which would be the parsed as the siteid
    On the backend it uses a Database id that can be acquired from the show's homepage (the source of the "siteid")
    It's unclear at the moment if an alternate url can be used to redirect to the homepage or if the DBID is available via a different method.
"""

## Base url for API
API_URL = f"""https://prod-api-funimationnow.dadcdigital.com/api/funimation/episodes/"""
default_session = requests.session_decorator_factory(useragent = True)

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME = "funimation"

def match_url(url):
    return bool(re.search("""funimation\.com""",url))

def parse_siteid(url):
    result = re.search("""(https?://)?www.funimation\.com/shows/(?P<siteid>[^\/\\?]+)""",url)
    if result:
        return result.group("siteid")
    return False


#####################

def siteid_to_homepageurl(siteid):
    """ Returns the homepage url formatted for the given siteid """
    return f"""https://www.funimation.com/shows/{siteid}/"""


@default_session
def get_dbid(siteid, session = None):
    url = siteid_to_homepageurl(siteid)
    print(url)
    print(session.headers)
    soup = requests.GET_soup(url, session = session)
    print(soup)
    if not isinstance(soup, requests.bs4.BeautifulSoup): raise ValueError(f"Failed to get a response for siteid: {siteid}")
    isrobots = soup.find("meta",attrs={"name":'ROBOTS'}) or soup.find("meta",attrs={"name":'robots'})
    if isrobots: raise RuntimeError(f"Request failed due to robots")
    return soup.find("div",attrs={"name":'top'}).attrib("data-id")