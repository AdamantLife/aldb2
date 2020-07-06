## Builtin
import re

#################################################################
"""
                     webmodules Requirements
                                                              """
#################################################################
SITENAME = "Anilist"

def match_url(url):
    return bool(re.search("""anilist\.co""",url))

def parse_siteid(url):
    result = re.search("""(https?://)?anilist\.co/anime/(?P<siteid>\d+)""",url)
    if result:
        return result.group("siteid")
    return False

#################################################################
#################################################################

ANIMEURL = r"http://anilist.co/anime/{identification}"


ANILISTRE = re.compile(ANIMEURL.replace("http:","https?:").replace(r"{identification}",r"(?P<identification>\w+)"))
def parseidfromurl(url):
    search = ANILISTRE.search(url)
    if not search: return False
    return search.group("identification")