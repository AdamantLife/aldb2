## Builtin
import datetime
import importlib
import pathlib
import urllib.request as urequest
## Custom Module
from alcustoms import filemodules

EST = datetime.timezone(datetime.timedelta(hours = -5))
JST = datetime.timezone(datetime.timedelta(hours = 9))

def discover_modules():
    """ Discovers all valid submodules """
    lopath = pathlib.Path(__file__).resolve().parent
    def filetest(pathobj):
        """ Tests if a Path Object is a valid submodule """
        _module = importlib.import_module("aldb2.webmodules."+pathobj.stem)
        for required_attr in ["SITENAME",]:
            if not getattr(_module,required_attr,None):
                del _module
                return False
        for required_method in ["match_url","parse_siteid",]:
            if not callable(getattr(_module,required_method,None)):
                del _module
                return False
        return True

    for pyfile in filemodules.iterdir_re(lopath,".*",test = filetest):
        mod = importlib.import_module("aldb2.webmodules."+pyfile.stem)
        MODULES[mod.SITENAME] = mod

MODULES = {}
discover_modules()

def getseriespage(anime):
    '''Fetches and reads homepage html into memory'''
    print('Getting Page for:', anime.title)
    url=anime.homepage
    html=urequest.urlopen(url).read()
    print('>>> Page Recieved')
    return html

def check_site(url_or_sitename):
    """ Scans installed submodules for a url or sitename that matches the given url or sitename """
    if not isinstance(url_or_sitename,str):
        raise TypeError("Invalid url or sitename")
    for mod in MODULES.values():
        ## This is extraneous, but we'll be explicit
        result = False
        if url_or_sitename.lower() == mod.SITENAME.lower():
            result = True
        else:
            result = mod.match_url(url_or_sitename)
            if not result:
                result = mod.parse_siteid(url_or_sitename)
        if result: return mod.SITENAME
