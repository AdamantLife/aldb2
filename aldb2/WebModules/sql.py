

def search_site(connection, value):
    """ Searches the wm_website an dwm_aliases tables for the given phrase and returns a list of wm_website rows with matching name, domain, or alias.
    
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

