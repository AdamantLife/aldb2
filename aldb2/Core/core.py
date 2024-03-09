
class Franchise():
    def __init__(self,franchiseid, franchise):
        self.franchiseid = franchiseid
        self.franchise = franchise

class Series():
    def __init__(self, seriesid: int|None, series, franchiseid = None, franchise = None):
        self.franchise = Franchise(franchiseid = franchiseid, franchise = franchise)
        self.seriesid = seriesid
        self.series = series

class Genre():
    def __init__(self, genreid, name, abbreviation = None, dark = False, spoiler = False):
        self.genreid = genreid
        self.name = name
        self.abbreviation = abbreviation
        self.dark = dark
        self.spoiler = spoiler