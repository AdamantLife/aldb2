## Builtin
import collections
import csv
import datetime
import itertools
import json
import re
## This Module
from aldb2.WebModules import JST
## Custom Module
from alcustoms.methods import isiterable
"""
Module for aggregating season charts from various sites

Each site submodule should have the following attributes and functions for proper integration:
    CHARTNAME: Attribute. A unique name to identify the chart being parsed by the module. Case-sensitive.
    getshowsbyseason: Function. Accepts params season,year. Returns a list of show objects (these
                        objects may be customized for the source site).
    convertshowstostandard: Function. Accepts param shows as returned bygetshowsbyseason, as well
                            as showfactory, which should default to seasoncharts.Show (this file).
                            Returns a list of objects of type showfactory.

This ensures a consistent minimal workflow of:
    shows = getshowsbyseason(season,year)
    shows = convertshowstostandard(shows)
Which would correctly represent all shows listed in the chart as seasoncharts.Show objects. Inclusion of
showfactory allows for seasoncharts.Show to be subclassed and used in this workflow. CHARTNAME can be used
to sort the results by their module of origin.


Subclassing Show:
    When adapting Show also adjust:
        Show.serialize
        Show.__iadd__
        save_as_csv
"""

DTFORMAT = "%d/%m/%Y %H:%M:%S %z"

SEASONALIASES = [0  , "0"   , "w"       , "wi"  , "win",
                 1  , "1"   , "spring"  , "sp"  , "spr",
                 2  , "2"   , "summer"  , "su"  , "sum",
                 3  , "3"   , "f"       , "fa"  , "fal"]

SEASONRE = re.compile("""(?P<season>\w+)-(?P<year>\d{4})""")
SeasonError = AttributeError("Season must be a string formatted '{Season}-{4-digit Year}'")

def matchseason(season):
    """ Compares the season value to the standard Season Regex, returning True if it matches, else False """
    try:
        return bool(SEASONRE.match(season))
    except:
        return False

def parseseason(season):
    """ Returns a tuple (season:str [capitalized], year:str) if the season matches the Season Regex, otherwise returns a tuple (False, False) """
    try:
        seasonresearch = SEASONRE.search(season)
        return seasonresearch.group("season").lower().capitalize(),int(seasonresearch.group("year"))
    except: return False, False

def buildseason(season,year):
    """ Creates a correctly formatted season string.
   
    Accepts aliases for season (case-insensitive):
        Winter: 0   , "W"   , "Wi"  , "Win"
        Spring: 1           , "Sp"  , "Spr"
        Summer: 2           , "Su"  , "Sum"
        Fall:   3   , "F"   , "Fa"  , "Fal"
    """
    try:
        season = int(season)
    except: pass
    if isinstance(season,int):
        if season > 3:
            raise AttributeError("Season Index must be in range 0...3 inclusive.")
        season = str(season)
    if not isinstance(season,str):
        raise AttributeError("Season must be string or integer season index")
    season = season.lower()
    if season in SEASONALIASES:
        index = SEASONALIASES.index(season) // 5
        season = ["Winter","Spring","Summer","Fall"][index]
    season = season.capitalize()
    if season not in ("Winter","Spring","Summer","Fall"):
        raise AttributeError("Season must be 'Winter','Spring','Summer', or 'Fall', or an accepted alias")
    out = f"{season}-{year}"
    if not matchseason(out):
        raise AttributeError("Year must be 4 Digits")
    return out

class Show():
    """ A generalized container for outputting standardized chart data """
    def __init__(self, chartsource, season, japanese_title, romaji_title = "", english_title = "", additional_titles = None, medium = "TV", continuing = None, renewal = None, summary = "", tags = None, startdate = None, episodes = 0, runtime = 0, images = None, studios = None, links = None):
        """ Creates a new standardized Show Object.

        chartsource is a list of chart sources for this show. Each element should be a tuple (chart name, show's id for the chart).
        season is the anime season that the show is airing, formatted "{Season}-{4-digit Year}".
        japanese_title is the title as it appears on Japanese Television/in Japanases listings.
        romaji_title is a transliteration of the japanese_title into the Latin Alphabet.
        english_title is the Official Localized English title; if not available, it should be an approximation of japanese_title in English.
        additional_titles should be any additional titles not already provided (such as additional translations, transliteration into Hira/Katakana, localizations for non-Japanese/English languages, etc).
        medium is the format of the show. This should typical be one of: "TV" for standard-length television Shows;
            "TV Short" for short-format television shows; "OVA" for direct-to-video releases; "ONA" for internet shows;
            or "Movie" for feature-length releases (this format name supercedes any others that may be applicable).
        continuing should be a boolean indicating whether the series was airing in the previous anime season (multi-coor season).
        renewal should be a boolean indicating whether the series is a sequel season.
        summary is a blurb describing the series.
        tags is a list of descriptive terms (including genres). These may be strings, Tag Objects, or a dictionary with values matching Tag Object attributes; they will be converted to Tag Objects automatically.
        startdate is a Datetime indicating the air date and time of the first episode (in JST).
        episodes is the number of episodes the series is set to air.
        images is a list of links to promotional images/posters for the series.
        studios is a list of studios names involved in the production of the Show.
        links is a list of tuples, each tuple consisting of (linkname: str, url: str). linkname describes the link (i.e.- "PV", "MAL Page", "Official Site", etc).
        """

        if not isinstance(chartsource,(list,tuple)):
            raise AttributeError("chartsource must be a list")
        if any(not isinstance(chart,(list,tuple)) for chart in chartsource)\
            or any(len(chart) != 2 for chart in chartsource):
            raise AttributeError("Each source for chartsource should be a length-2 tuple containing (chart name, show's id for the chart).")
        self.chartsource = chartsource

        aseason,ayear = parseseason(season)
        if not aseason:
            raise SeasonError
        self.season = buildseason(aseason,ayear)
        if japanese_title is None: japanese_title = ""
        self.japanese_title = japanese_title
        if romaji_title is None: romaji_title = ""
        self.romaji_title = romaji_title
        if english_title is None: english_title = ""
        self.english_title = english_title
        if additional_titles is None: additional_titles = list()
        self.additional_titles = additional_titles
        self.medium = medium
        self.continuing = continuing
        self.renewal = renewal
        if summary is None: summary = ""
        self.summary = summary
        if tags is None: tags =[]
        self.tags = [Tag(tag) for tag in tags]

        if isinstance(startdate,str):
            try:
                startdate = datetime.datetime.strptime(startdate, DTFORMAT)
            except:
                startdate = datetime.datetime.strptime(startdate, DTFORMAT.rstrip("%z"))
        elif isinstance(startdate,(int,float)):
            startdate = datetime.datetime.fromtimestamp(startdate)
        if not isinstance(startdate,datetime.datetime) and not startdate is None:
            raise AttributeError(f"startdate should be datetime or None: {startdate}")
        if startdate:
            startdate = startdate.replace(tzinfo= JST)
        self.startdate = startdate
        if episodes is None:
            episodes = 0
        episodes = int(episodes)
        self.episodes = episodes
        if runtime is None: runtime = 0
        runtime = int(runtime)
        self.runtime = datetime.timedelta(minutes = runtime)

        if images is None: images = []
        ## In case user only submits one image
        if isinstance(images,str):
            images = [images,]
        if not isinstance(images,(list,tuple)):
            raise AttributeError("images should be a list of image urls for promotional images/posters")
        self.images = list(images)

        if studios is None: studios = list()
        if not isinstance(studios, (list,tuple)) or any(not isinstance(studio,str) for studio in studios):
            raise AttributeError("studios should be a list of strings, or None.")
        self.studios = studios
        
        if links is None: links = list()
        if not isinstance(links,(list,tuple))\
            or any(not isinstance(link,(list,tuple)) for link in links)\
            or any(0 > len(link) > 2 for link in links)\
            or any(not isinstance(element,str) for link in links for element in link):
            raise AttributeError("links must be None or a list of length-2 tuples containing strings")
        links = [(site.lower().title(),link) for site,link in links]
        self.links = sorted(set(links), key = lambda link: links.index(link))

    def get_title(self):
        return self.romaji_title or self.english_title or self.japanese_title

    def serialize(self):
        """ Makes a json-valid serialization of the Show """
        runtime = self.runtime
        if isinstance(runtime, datetime.timedelta):
            runtime = runtime.total_seconds() / 60
        return dict(chartsource=self.chartsource, season=self.season,
                    japanese_title=self.japanese_title, romaji_title = self.romaji_title,
                    english_title = self.english_title, additional_titles = self.additional_titles,
                    medium = self.medium, continuing = self.continuing, renewal = self.renewal, summary = self.summary,
                    tags = [tag.serialize() for tag in self.tags], startdate = self.startdate.strftime(DTFORMAT) if self.startdate else None,
                    episodes = self.episodes, runtime = runtime, images = self.images, studios = self.studios, links = self.links)

    def __eq__(self,other):
        if isinstance(other,Show):
            return self.japanese_title == other.japanese_title

    def __iand__(self,other):
        if isinstance(other,Show):
            if self == other:
                ## Begin consolidating show stats
                self.chartsource.extend(tuple(chart) for chart in other.chartsource)
                ## self.season shouldn't need to updated
                ## japanese_title has already been confirmed to be equal per self == other
                ## romaji_title should always be based off of japanese_title, so we only need to update if missing
                if not self.romaji_title and other.romaji_title:
                    self.romaji_title = other.romaji_title
                ## If other's english_title mismatches, we'll assume that ours takes precedence
                ## and store other's in addtional_titles (assuming it's not already there)
                if other.english_title != self.english_title\
                    and other.english_title not in self.additional_titles:
                    self.additional_titles.append(other.english_title)
                ## For each addtional_title, if it doesn't already exist somewhere on this object,
                ## we'll add it to our list
                for title in other.additional_titles:
                    if title not in self.additional_titles\
                        and title not in [self.japanese_title,self.romaji_title,self.english_title]:
                        self.additional_titles.append(title)
                ## We assume that "TV" is the default, therefore we update if we have TV and other contradicts us
                if self.medium == "TV" and other.medium != "TV":
                    self.medium = other.medium
                ## Hentai takes precedence over all other mediums (to assist filtering)
                if "hentai" in other.medium.lower():
                    self.medium = other.medium
                ## if continuing = True takes precedence
                self.continuing = self.continuing or other.continuing
                ## if renewal = True takes precedence
                self.renewal = self.renewal or other.renewal
                ## Just hack on the summaries together
                self.summary += "\n"+other.summary
                ## Consolidate tags uniquely, and if either source lists a tag as spoiler, respect it.
                for tag in other.tags:
                   if tag in self.tags:
                       mytag = self.tags[self.tags.index(tag)]
                       mytag.spoiler = mytag.spoiler or tag.spoiler
                   else:
                       self.tags.append(tag)
                ## It seems more likely that the earliest startdate may be some kind of default
                ## (either a chart default or season default) and there is little benifit in making
                ## the startdate later, so we'll assume that the latest startdate is the correct one.
                ## Also, note that startdate can be None

                ## If we have a startdate conflict
                if self.startdate and other.startdate and self.startdate != other.startdate:
                    self.startdate = max(self.startdate,other.startdate)
                ## If we're missing ours and other has one
                elif not self.startdate and other.startdate:
                    self.startdate = other.startdate
                ## Assume that the highest episodes number is the most accurate
                self.episodes = max(self.episodes,other.episodes)
                ## Assume that the highest runtime is the most accurate
                self.runtime = max(self.runtime if self.runtime else datetime.timedelta(), other.runtime if other.runtime else datetime.timedelta())
                ## There should never be duplicates, but we'll check anyway
                for image in other.images:
                    if image not in self.images: 
                        self.images.append(image)
                ## There may be multiple studios credited, but our chart(s) might not catch all of them
                ## We'll make a lower() list in case of weird casing
                studios = [studio.lower() for studio in self.studios]
                for studio in other.studios:
                    if studio.lower() not in studios:
                        self.studios.append(studio)
                ## We're only really concerned about the links themselves (the label is only for convenience)
                links = [url for (sitename,url) in self.links]
                for (sitename,url) in other.links:
                    if url not in links:
                        self.links.append((sitename,url))
                return self
        raise TypeError(f"Invalid types for &=: {self.__class__.__name__} and {other.__class__.__name__}")
    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.japanese_title}({__name__})"

class Tag():
    """ A Descriptive term for the content and themes of a Show """
    def __init__(self, tag, spoiler = False):
        """ Creates a new Tag Object.

        tag is a string which describes a theme or genre represented in or by the Show.
        spoiler is a boolean which indicates whether the tag spoils a plot point that is initially obfuscated
        """
        if isinstance(tag,(list,tuple)):
            if len(tag) == 1:
                tag = tag[0]
            elif len(tag) == 2:
                tag,spoiler = tag
            else:
                raise TypeError(f"__init__() takes from 2 to 3 positional arguments but {len(tag)} were given")
        elif isinstance(tag,dict):
            kwargs = tag
            try:
                tag = kwargs.pop("tag")
            except KeyError:
                raise TypeError("__init__() missing 1 required positional argument: 'tag'")
            spoiler = kwargs.pop("spoiler",spoiler)
            if kwargs:
                raise TypeError("__init__() got an unexpected keyword argument '{list(kwargs)[0]}'")

        if not isinstance(tag,str):
            raise TypeError("tag argument must be a string")
        self.tag = tag
        self.spoiler = bool(spoiler)

    def serialize(self):
        return dict(tag = self.tag, spoiler = self.spoiler)
    def __eq__(self,other):
        if isinstance(other,Tag):
            return self.tag == other.tag

    def __hash__(self):
        return hash(self.tag)

    def __str__(self):
        return self.tag

    def __repr__(self):
        return f"<{self.__class__.__name__} object: {self.tag}{'*spoiler*' if self.spoiler else ''}>"


def serialize_shows(shows,filename):
    """ Exports the shows as a json """
    if any(not isinstance(show,Show) for show in shows):
        raise TypeError("shows should be a list of Show objects")

    shows = [show.serialize() for show in shows]
    with open(filename,'w',encoding = 'utf-8') as f:
        json.dump(shows,f)

def load_serialized(filename):
    """ Loads shows saved as json """
    with open(filename,'r',encoding = 'utf-8') as f:
        data = json.load(f)
    shows = [Show(**show) for show in data]
    return shows

def save_as_csv(shows, filename, include_spoilers = False):
    """ Converts serialized data to csv-compliant format via json_to_csvdict and then writes it to file
    
    Most multi-value fields are combined (i.e. - chartsource, tags), but Links are separated into their own columns.
    """

    output = list()
    headers = ["ChartSource","Season","Japanese Title","Romaji Title","English Title","Additional Titles", "Medium", "Continuing", "Renewal", "Summary", "Tags", "StartDate", "Episodes", "Runtime", "Images", "Studios"]
    ## Showlinks is for accounting for links in relation to individual shows
    showlinks = list()
    ## sites is for creating a master list
    sites = list()
    for show in shows:
        out = list()
        out.append(", ".join(f"{source} ({cid})" for source,cid in show.chartsource))
        out.extend([show.season, show.japanese_title, show.romaji_title, show.english_title,", ".join(show.additional_titles),show.medium, str(show.continuing), str(show.renewal), show.summary])
        if include_spoilers: tags = show.tags
        else: tags = [tag for tag in show.tags if not tag.spoiler]
        out.append(", ".join(tag.tag for tag in tags))
        out.extend([show.startdate.isoformat() if show.startdate else None, show.episodes, show.runtime, ", ".join(show.images), ", ".join(show.studios)])
        ## We're going to handle links separately
        showlinks.append(show.links)
        sites.extend(site for site,link in show.links)


        output.append(out)

    ## Create a unique list based on sites
    flatsites = sorted(set(sites))
    ## Create just sites for each show for easier counting
    showsites = [[site for site,link in showlink] for showlink in showlinks]
    ## For each site in the unique set, add the required number of headers required for all links
    ## then add the appropriate links to the output
    for site in flatsites:
        ## For each show, check how many links to that site it has and then take the max
        count = max([showlink.count(site) for showlink in showsites])
        ## Since we'll be iterating the numbers several times, we'll initialize a variable to work off of
        counts = list(range(1,count+1))
        ## Add headers
        for i in counts:
            ## For any additional header, add a numeric suffix
            if i > 1: headers.append(f"{site}{i}")
            ## Otherwise, add the default header
            else: headers.append(site)
        ## Add the show's links to output
        ## showlinks and showoutput should be the same length and should be in the same order
        for showlink,showoutput in zip(showlinks,output):
            ## Filter for the current site (and drop site since we dont' need it)
            links = [link for s,link in showlink if s == site]
            ## Add links for the site, and fill in missing links with empty strings
            for link,count in itertools.zip_longest(links,counts, fillvalue = ""):
                showoutput.append(link)

    ## We should now be done
    with open(filename,'w', encoding = "utf-8", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(output)