
## Parent Module
from aldb2 import WebModules

## Custom
from alcustoms import sql

def search_site(connection, value):
    """ Searches the wm_website and wm_aliases tables for the given phrase and returns a list of wm_website rows with matching name, domain, or alias.
    
        connection should be a database connection.
        value should be a string which represents the string value to search for.
        Returns the resulting cursor.fetchall() value.
    """
    if not isinstance(value,str):
        raise ValueError("Search value must be a string.")

    return connection.execute("""SELECT webmodules_website.* FROM
webmodules_website
LEFT JOIN webmodules_aliases ON webmodules_website.wmsiteid = webmodules_aliases.website
WHERE name LIKE "%:value%"
    OR domain LIKE "%:value%"
    OR alias LIKE "%:value%";""").fetchall()

def get_sitemodule(connection, site):
    ## figure out what site contains
    name = webmodules.check_site(site)

    ## check_site will check the base name (name that appears in webmodules_website)
    if not name:
        with sql.Utilities.temp_row_factory(connection,sql.advancedrow_factory):
            aliaspk = connection.getadvancedtable("webmodules_aliases").quickselect(alias__like = site).first()
        if not aliaspk:
            raise LookupError(f"Could not locate website with name or url: {url_or_sitename}")
        name = aliaspk.website.name

    return webmodules.MODULES[name]

def validate_add_siteid(connection,seasonid, url_or_sitename,siteid = None):
    """ Parses out information based on provided information and adds it to the database """

    _module = get_sitemodule(connection, url_or_sitename)

    sid = _module.parse_siteid(url_or_sitename)

    if sid and siteid and sid != siteid:
        raise ValueError("Given site url does not match siteid")
    elif sid and not siteid:
        siteid = sid

    ## If we don't have a siteid by this point, we can't do anything
    if not siteid:
        raise ValueError("Could not determine siteid")

    dbid = connection.getadvancedtable("webmodules_website").quickselect(name = _module.SITENAME).first()
    ## Need website to add
    if dbid is None:
        raise ValueError("Could not get ID for website")

    result = connection.getadvancedtable("webmodules_siteids").get_or_addrow(website = dbid, season = seasonid, siteid = siteid).first()
    return result