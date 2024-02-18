
class Series():
    def __init__(self,seriesid, series):
        self.seriesid = seriesid
        self.series = series

class Subseries():
    def __init__(self, subseriesid: int|None, subseries, seriesid = None, series = None):
        self.series = Series(seriesid = seriesid, series = series)
        self.subseriesid = subseriesid
        self.subseries = subseries

class Genre():
    def __init__(self, genreid, name, abbreviation = None, dark = False, spoiler = False):
        self.genreid = genreid
        self.name = name
        self.abbreviation = abbreviation
        self.dark = dark
        self.spoiler = spoiler