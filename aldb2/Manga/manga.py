class Manga():
    def __init__(self, rowid, series, subseries = "", mangaseries = "", catrank = "C", volumes = 0, own = 0, read = 0, nextvolume = "12/31/2100",
                 publisher="N/A",image='noimages.png',thumbnail='noimages-thumbnail.png'):
        self.rowid = rowid
        self.series = series
        self.subseries = subseries
        self.mangaseries = mangaseries
        self.catrank = catrank
        self.volumes = int(volumes)
        self.own = int(own)
        self.read = int(read)
        if nextvolume==False: nextvolume=None
        self.nextvolume = nextvolume    ## Timestamp or False
        self.publisher=publisher
        self.image=image                ##file location
        self.thumbnail=thumbnail        ##file location

    def complete(self):
        return self.volumes>=self.own>=self.read and not self.nextvolume
    def getnextvolume(self):
        if not self.nextvolume: return False
        return datetime.datetime.fromtimestamp(self.nextvolume)

    def title(self):
        return gettitle(series=self.series,subseries=self.subseries)
    def allstring(self):
        return " ".join([str(attr) for attr in [self.rowid,self.series,self.subseries,self.catrank,self.volumes,self.own,self.read,self.nextvolume,self.publisher,self.image,self.thumbnail]])
    def __repr__(self):
        return "{}{}".format(self.series[:5], " "+self.subseries[:5] if self.subseries else "")
    def __eq__(self,other):
        if isinstance(other, Manga):
            return ''.join([self.series,self.subseries])==\
                   ''.join([other.series,other.subseries])
    def __sub__(self,other):
        if not isinstance(other,Manga): raise TypeError("Cannot compare Manga to {}".format(type(other)))
        return {attr:getattr(other,attr) for attr in
                ['series', 'subseries', 'catrank', 'volumes', 'own', 'read', 'nextvolume',
                 'publisher', 'image', 'thumbnail']
                if getattr(self,attr)!=getattr(other,attr)}
    def __hash__(self):
        return hash(''.join([str(attr) for attr in
                            [self.series,self.subseries,self.catrank,self.volumes,self.own,self.read,
                             self.nextvolume,self.publisher,self.image,self.thumbnail]]))