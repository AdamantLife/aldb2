## Builtin
import datetime

SQLCONFIG = "sql/sql.json"

def getseason(date = None):
    """ Returns an educated guess at the current airing season based on a datetime.date or datetime.datetime object (if not provided, will use for datetime.datetime.today())"""
    if date is None: date = datetime.datetime.today()
    if not isinstance(date, (datetime.datetime,datetime.date)):
        raise TypeError("date must be datetime.datetime or datetime.date object")
    month = date.month
    index = month // 4
    return ["Winter","Spring","Summer","Fall"].index(index)