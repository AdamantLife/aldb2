## Builtin
import datetime
import pathlib
## This Module
from aldb2 import Core
from aldb2 import SeasonCharts
from aldb2.SeasonCharts import anichart,anilist,livechart

""" A temporary module for gathering charts """

DEFAULTOUTPUT = pathlib.Path("output_gammut.json").resolve()

## Order represents precedence when consolidating data
MODULES = [anichart,livechart,anilist]

def run_gammut(season,year):
    """ Runs the gammut of charts and returns a consolidated chart of standardized Show objects """
    out = []
    for module in MODULES:
        shows = module.getshowsbyseason(season,year)
        shows = module.convertshowstostandard(shows)
        out.extend(shows)
    return out

def sortshows(shows,chartname):
    """ Sorts shows based on chartsource name """
    chartshows,extrashows = list(),list()
    for show in shows:
        if chartname in [chart for chart,chartid in show.chartsource]:
            chartshows.append(show)
        else:
            extrashows.append(show)
    return chartshows,extrashows

def consolidate_gammut(shows):
    """ Merges shows from all sites into a list based on japanese_title """
    out = list()
    for module in MODULES:
        ## Sort out shows based on the current module
        moduleshows,shows = sortshows(shows,module.CHARTNAME)
        for show in moduleshows:
            ## Check if show is not on the list yet
            if show not in out:
                out.append(show)
            ## Otherwise, update the output show
            else:
                outshow = out[out.index(show)]
                ## &= (__iand__) is the method for updating a show in-place
                outshow &= show
    ## Any extra shows that did not come from MODULES will assumed to be default values:
    ## therefore we'll do the same process as above, but iterate over out and use shows
    ## as the base to check
    for show in out:
        if show not in shows:
            shows.append(show)
        else:
            baseshow = shows[shows.index(show)]
            baseshow &= show
    ## shows is now our output
    return shows

def main(season = None,year = None, output = DEFAULTOUTPUT):
    """ The complete process of gathering shows from a season

    Runs the gammut, consolidates the gammut, and serializes the gammut into json format to output_gammut.json by default.
    season is the "Winter", "Spring", "Summer", "Fall"
    year is a valid year.
    output is a json file that does not already exist: the default is output_gammut.json. By exception, if the output is
    the default, local output_gammut.json file, it will be automatically overwritten if it exists.
    """
    if output != DEFAULTOUTPUT:
        output = pathlib.Path(output).resolve()
    validatemain(season,year,output)
    shows = run_gammut(season,year)
    shows = consolidate_gammut(shows)
    SeasonCharts.serialize_shows(shows,output)

def validatemain(season,year,output):
    """ Provides the validations performed by main for use in main-replacement/customization functions.

    This function also converts any non-standard data that it can interpret.
    Returns season,year,output.
    """
    today = datetime.datetime.today()
    if season is None:
        season = Core.getseason(today)
    if year is None:
        year = today.year
    seasonstring = SeasonCharts.buildseason(season,year)
    season,year = SeasonChart.parseseason(seasonstring)
    if not isinstance(output,pathlib.Path):
        try:
            output = pathlib.Path(output)
        except:
            raise ValueError("Could not interpret output")
    if output != DEFAULTOUTPUT and output.exists():
        raise ValueError("output location already exists!")
    return season,year,output

if __name__ == "__main__":
    season,year = "Spring",2018

    print("running gammut")
    shows = run_gammut(season,year)
    print("consolidating gammut")
    shows = consolidate_gammut(shows)
    print("saving shows")
    SeasonCharts.serialize_shows(shows,"output_gammut.json")
    print('loading shows')
    shows = SeasonCharts.load_serialized("output_gammut.json")
    print("writing to csv")
    ## Writing to csv
    SeasonCharts.save_as_csv(shows, "output_gammut.csv")
    print("done")
