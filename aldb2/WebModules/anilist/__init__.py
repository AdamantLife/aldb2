## Builtin
import re

ANIMEURL = r"http://anilist.co/anime/{identification}"


ANILISTRE = re.compile(ANIMEURL.replace("http:","https?:").replace(r"{identification}",r"(?P<identification>\w+)"))
def parseidfromurl(url):
    search = ANILISTRE.search(url)
    if not search: return False
    return search.group("identification")