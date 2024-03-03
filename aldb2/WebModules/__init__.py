## Builtin
import datetime
import typing
from WebModules import anidb, anilist, animenewsnetwork, crunchyroll, funimation, myanimelist, syoboi

""" MODULE NOTE: A number of submodules have functionality deprecated for the time being;
    they are commented out to make the easier to restore if they are needed in the future. """

EST = datetime.timezone(datetime.timedelta(hours = -5))
JST = datetime.timezone(datetime.timedelta(hours = 9))

class PluginModule(typing.Protocol):
    """ A module that is a valid plugin for the ALDB2 Web Module system """
    ## SITENAME within the module has to be typed as str; if it is simply a
    ## string literal then it's type will be Literal[str] which is incompatible
    SITENAME: str
    @staticmethod
    def match_url(url: str)->bool: ...
    @staticmethod
    def parse_siteid(url: str)->str|typing.Literal[False]: ...

ModuleLookup = dict[str, PluginModule]

## NOTE: discover_modules was a function previously used to dynamically load modules from the WebModules directory.
##       It was removed as there's not a reasonable use case for it


MODULES: ModuleLookup = {
    anidb.SITENAME: anidb,
    anilist.SITENAME: anilist,
    animenewsnetwork.SITENAME: animenewsnetwork,
    crunchyroll.SITENAME: crunchyroll,
    funimation.SITENAME: funimation,
    myanimelist.SITENAME: myanimelist,
    syoboi.SITENAME: syoboi
    }

def check_site(url_or_sitename: str)->str|None:
    """ Scans installed submodules for a url or sitename that matches the given url or sitename """
    if not isinstance(url_or_sitename,str):
        raise TypeError("Invalid url or sitename")
    for mod in MODULES.values():
        if url_or_sitename.lower() == mod.SITENAME.lower():
            return mod.SITENAME
        result = mod.match_url(url_or_sitename) or mod.parse_siteid(url_or_sitename)
        if result: return mod.SITENAME
