## Builtin
import datetime

## Sister Module
from ChartMaker import classes

class EpisodeAiring():
    """ A Simple Container Object for an Episode's Airing """
    def __init__(self,channel,dt,episode,title):
        self.channel = channel
        self.datetime = dt
        self.episode = episode
        self.title = title
    @property
    def formattime(self):
        return self.datetime.strftime("%d/%m/%Y %I:%M %p")
        
    def __eq__(self,other):
        if isinstance(other,EpisodeAiring):
            return self.datetime == other.datetime
    def __gt__(self,other):
        if isinstance(other,EpisodeAiring):
            return self.datetime > other.datetime
    def __ge__(self,other):
        if isinstance(other,EpisodeAiring):
            return self == other or self > other

    def __repr__(self):
        return f"Episode {self.episode}- {self.title} ({self.channel} @ {self.formattime})"


def getshowairings(record, shows = None, watchingonly = True, gathermethod = None, session = None):
    """ Gathers a list of EpisodeAiring for the given shows in a SeasonRecord file.

    record should be a SeasonRecord instance or a path to a file containing the SeasonRecord.
    If provided, shows should be a list of Show instances or strings matching Shows' name attribute.
    watchingonly indicates whether to only output Shows whose watching attribute is True.
    gathermethod should be a method reference that accepts a list of aldb2 Show and a requests Session,
    and produces list contianing a list for each show of EpisodeAiring objects.
    The lists returned by gathermethod can provide duplicates of episodes: these will be parsed
    out and only the earliest airing will be kept.
    Returns the resulting list of unique EpisodeAirings for each show (in alphabetical order)
    """
    if not isinstance(record,classes.SeasonRecord):
        try: record = classes.SeasonRecord(record)
        except: raise ValueError("Invalid SeasonRecord file.")

    import pprint
    pprint.pprint(record.compileshows())
    ## Building lookup for shows
    shownames = []
    if shows:
        if not isiterable(shows): raise ValueError("shows must be a List of Strings or Show Instances")
        for show in shows:
            if isinstance(show,str): shownames.append(show)
            elif isinstance(show,classes.Show): shownames.append(show.name)
            else: raise ValueError(f"shows must be a List of Strings or Show Instances: {show}")
    ## Make a list of Show Objects to gather
    showlist = list()
    for show in sorted(record.showstats.shows.values(),key=lambda show: show.name):
        ## If watchingonly is False, then output
        ## Otherwise output if show.watching is True
        if not watchingonly or show.watching:

            ## If shows is provided, make sure show is in list
            if shows is None or show.name in shownames:

                ## Only attempt to get the show if it has a showboy TID
                if show.showboyid:
                    showlist.append(show)

    showstrings = "\n".join(str(show) for show in showlist)
    print(f"Gettings Calendars For:\n{showstrings}")
    raise Exception()
    ## Delegate to gathermethod
    airings = gathermethod(showlist,session = session)
    output = list()
    ## For each episode number for a show, add the earliest to the list
    for show in airings:
        out = list()
        episodenumbers = sorted(list(set(episode.episode for episode in show)))
        for episode in episodenumbers:
            earliest = sorted([airing for airing in show if airing.episode == episode])[0]
            out.append(earliest)
        output.append(out)
    return output

def formatairingsasGoogle(airings):
    """ Formats a list of airings in Google Calendar Format

    airings should be a flat list (as opposed to the nested lists returned by getshowairings)
    Returns a list of lists which each contain:
        ["{Show Name} Episode {Episode Number}",airdate,airtime,episodetitle (japanese)]
    NOTE: These correspond to the Google Calendar Import formatting:
        ["Subject","Start Date","Start Time","Description"]
        >>> The above list should be added as the header row before importing into Google Calendar
    """
    out = []
    airings = sorted(airings)
    for airing in airings:
        dt = airing.datetime.astimezone(web.EST)
        
        subject = f"{airing.show.name} Episode {airing.episode}"
        startdate = f'{dt.strftime("%m/%d/%Y")}'
        starttime = f'{dt.strftime("%I:%M %p")}'
        description = airing.title

        out.append([subject,startdate,starttime,description])
    return out

def outputGoogleCalendar(airings):
    """ Reformat airings into Google Format and output to file """
    
    airings = itertools.chain.from_iterable(airings)
    out = formatairingsasGoogle(airings)

    out.insert(0,["Subject","Start Date","Start Time","Description"])
    with open("2018 Winter Calendar.csv",'w',newline = "",encoding='utf-8') as f:
        writer = csv.writer(f,quoting = csv.QUOTE_MINIMAL)
        writer.writerows(out)