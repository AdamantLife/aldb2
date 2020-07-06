## Builtin
import re

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME = "crunchyroll"

def match_url(url):
    return bool(re.search("""crunchyroll\.com""",url))

def parse_siteid(url):
    result = re.search("""(https?://)?www.crunchyroll\.com/(?P<siteid>[^\/\\?]+)""",url)
    if result:
        return result.group("siteid")
    return False