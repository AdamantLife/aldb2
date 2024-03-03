""" aldb2.webmodules.myanimelist

    Module for retrieving information from MyAnimelist.
"""


## Builtin
import re
import typing

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME: str = "MyAnimeList"

def match_url(url: str) -> bool:
    return bool(re.search(r"""myanimelist\.net""",url))

def parse_siteid(url: str)-> str|typing.Literal[False]:
    result = re.search(r"""(https?://)?myanimelist\.net/anime/(?P<siteid>\d+)""",url)
    if result:
        return result.group("siteid")
    return False


##################################################################

def format_siteid(malid):
    return f"https://myanimelist.net/anime/{malid}"

def is_siteurl(url):
    if not isinstance(url,str):
        raise ValueError("")