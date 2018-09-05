## Builtin
import datetime
import itertools
import urllib.request as urequest
import xml.etree.ElementTree as ET
## Third Party
import bs4 ## Used to parse out News Thumbnail
## Custom Module
import alcustoms.methods as almethods

class Item():
    """ A Crunchyroll RSS Item Class """
    def __init__(self,category=None,pubdate=None,series=None,episodenumber=1,title=None,link="",thumbnails=None):
        """ Creates a new Crunchyroll RSS Item

pubdate should be a datetime instance, string, or None (default None). If None, pubdate will be the
current datetime via datetime.today(). If string, string should be formatted "%a, %d %b %Y %H:%M:%S %Z"
thumbnails, if supplied, should be a mapping of thumbnail widths (integers) with url values.
"""
        self.category=category
        if pubdate is None: pubdate = datetime.datetime.today()
        elif isinstance(pubdate,str):
            pubdate = datetime.datetime.strptime(pubdate,"%a, %d %b %Y %H:%M:%S %Z")
        elif not isinstance(pubdate,datetime.datetime):
            raise AttributeError("pubdate requires datetime instance, string, or None")
        self.pubdate = pubdate
        self.series = series
        self.episodenumber = episodenumber
        self.title = title
        self.link = link
        if thumbnails is None: thumbnails = dict()
        self.thumbnails = {int(k):v for k,v in thumbnails.items()}

    @property
    def defaultthumbnail(self):
        """ We're just returning the biggest one for now """
        return self.thumbnails[max(self.thumbnails)]

    def __repr__(self):
        return f"CRItem {self.series} Ep {self.episodenumber}"

    def parsexml(itemelement):
        """ Parses a Crunchyroll rss <item> element, returning an Item object """
        category = itemelement.findtext('category')
        pubdate = itemelement.findtext('pubDate')
        series = itemelement.findtext('seriesTitle')
        episodenumber = itemelement.findtext('episodeNumber')
        title = itemelement.findtext('title')
        link = itemelement.findtext('link')
        thumbnails = {ele.attrib['width']:ele.attrib['url'] for ele in itemelement.findall('thumbnail')}
        return Item(category=category,pubdate=pubdate,series=series,episodenumber=episodenumber,
                    title=title,link=link,
                    thumbnails=thumbnails)

class NewsItem():
    """ An Item for Crunchyroll News """
    def __init__(self,title = None, pubdate = None, link = None, thumbnail = None):
        self.title = title
        if pubdate is None: pubdate = datetime.datetime.today()
        elif isinstance(pubdate,str):
            pubdate = datetime.datetime.strptime(pubdate,"%a, %d %b %Y %H:%M:%S %Z")
        elif not isinstance(pubdate,datetime.datetime):
            raise AttributeError("pubdate requires datetime instance, string, or None")
        self.pubdate = pubdate
        self.link = link
        self.thumbnail = thumbnail
    def parsexml(itemelement):
        """ Parses a Crunchyroll News rss <item> elment, returning a NewsItem Object """
        title = itemelement.findtext('title')
        pubdate = itemelement.findtext('pubDate')
        link = itemelement.findtext('link')
        thumbnail = NewsItem.parsethumbfromdescription(itemelement.find("description"))
        return NewsItem(title=title,pubdate=pubdate,link=link,thumbnail=thumbnail)
    def parsethumbfromdescription(descriptionelement):
        """ Gets the thumbnail from the description element.

        Crunchyroll News RSS does not provide the thumbnail separate from the description.
        The description is html-formatted, so we load it into BeautifulSoup, then find the
        first <img> tag and return it's source.
        """
        soup = bs4.BeautifulSoup(descriptionelement.text,'html.parser')
        img = soup.find('img')
        if not img: return None
        return img.attrs['src']


def getitemsfromrss(feedurl,itemclass = Item):
    """ Series of methods for querying and parsing Crunchyroll rss feed """
    tree = getfeed(feedurl)
    root = tree.getroot()
    almethods.removenamespaces(root)
    return getitems(root,itemclass=itemclass)

def getfeed(feedurl):
    """ Queries the rss for the feed """

    with urequest.urlopen(feedurl) as resp:
        tree = ET.parse(resp)

    return tree

def getitems(root,itemclass = Item):
    """ Returns all items as Item Objects from a CR root element """
    if "channel" in root.tag: channels = [root,]
    else: channels=root.findall('channel')
    items = itertools.chain.from_iterable([channel.findall('item') for channel in channels])
    items = [itemclass.parsexml(item) for item in items]
    return items