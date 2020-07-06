""" aldb2.webmodules.myanimelist

    Module for retrieving information from MyAnimelist.
"""


## Builtin
import re

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME = "MyAnimeList"

def match_url(url):
    return bool(re.search("""myanimelist\.net""",url))

def parse_siteid(url):
    result = re.search("""(https?://)?myanimelist\.net/anime/(?P<siteid>\d+)""",url)
    if result:
        return result.group("siteid")
    return False


##################################################################

def format_siteid(malid):
    return f"https://myanimelist.net/anime/{malid}"

def is_siteurl(url):
    if not isinstance(url,str):
        raise ValueError("")