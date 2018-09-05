from aldb2.Core.sql import util

SQLCONFIG = util.loadsqljson(__file__)

def getweekindex(year,season,week):
    return year + season/10 + week/100

def CTE_showweeks(show = False, weekindex = False):
    """ Returns the CTE snippet to build showweeks ("showweeks AS ([etc...]" ) """
    args = []
    if show:
        args.append("""subseriesranking.subseriesid = :show""")
        args.append("""subseriesweeklyranking.rank IS NOT NULL""")
    if weekindex:
        args.append("""al_weekindex.weekindex <= :weekindex""")
    if args:
        args = "\nAND".join(args)
        args = "WHERE "+args
    else:
        args = ""
    return f"""
showweeks AS (
    SELECT al_weekindex.weekindex
    FROM al_subseriesranking
    LEFT JOIN al_weekindex ON al_subseriesranking.week = al_weekindex.week
    {args}
    GROUP BY al_weekindex.weekindex
    )"""

def QS_normalize_average(showweeks = None):
    """ Returns the sql-string to query for the average of a subseries' normalized ranks
    
        Accepts showweeks, which should be a returned value from the CTE_showweeks method.
        If not provided, this method will use CTE_showweeks with the default arguments.
    """
    if showweeks is None: showweeks = CTE_showweeks()
    return f"""
    WITH
    {showweeks}
    SELECT subseries, avg(normalized) AS average, group_concat(normalized,",") AS normalized, max(weekindex) AS lastweekindex
    FROM al_normalized
    GROUP BY subseries
    """