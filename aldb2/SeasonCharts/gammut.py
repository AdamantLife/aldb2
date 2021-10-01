from click import echo

## Builtin
import datetime
import pathlib
import re
## This Module
from aldb2 import Core
from aldb2.Anime.anime import AnimeSeason
from aldb2 import SeasonCharts
from aldb2.SeasonCharts import anilist
from aldb2.SeasonCharts import mal
## ,livechart ## livechart's new cloudflare protection is difficult to get by; livechart is not vital enough to put more effort into
## ,anichart ## It seems that anichart may be an exact mirror of anilist at this point
from aldb2.WebModules import myanimelist ## Used to get additional information about shows
from aldb2.WebModules.myanimelist import scraping as malscraping ## Used to get additional information about shows

## Third Party
from Levenshtein import distance as lev_distance

""" A temporary module for gathering charts """

DEFAULTOUTPUT = pathlib.Path("output_gammut.json").resolve()

## Order represents precedence when consolidating data
MODULES = [anilist, mal ] ## livechart, anichart ## See notes above

## Dev Mode
VERBOSE = False
VERBOSE = True ## comment out
import traceback ## comment out

def run_gammut(season,year, modules = None):
    """ Runs the gammut of charts and returns a consolidated chart of standardized Show objects.

        if modules is None, default, gammut.MODULES will be used. Otherwise, modules should be a
        subset list of modules available in gammut.MODULES.
    """
    out = []
    if not modules:
        modules = list(MODULES)
    else:
        modules = [mod for mod in modules if mod in MODULES]
        if not modules: raise ValueError("No valid modules found in modules list")
    for module in modules:
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
    ## On each iteration, remove module's shows from remaining shows, then check
    ## if they are already  in the output list; if they are, combine the two,
    ## otherwise add the show to the output list
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

def findmissing_gammut(shows):
    """ Finds missing information for the given shows using various methods. 
    
        Complete Show Type: checks site resources to determine missing show types.
    """
    for show in shows:
        ## Used to check if mal made a change
        show_medium = show.medium
        ## Shows from the MAL chart call findmissing_showstats while they are gathered
        ## (so call use MAL for non-MAL shows)
        if mal.CHARTNAME not in [chartname for (chartname, chartid) in show.chartsource]:
            def pipe(output, verbose = False):
                if not verbose or VERBOSE and verbose:
                    echo(output)
            malscraping.findmissing_showstats(show, pipe = pipe)
        else:
            ## MAL is a reliable source, so make sure the next test fails
            show_medium = "MAL"
        ## We're now double-checking all show mediums that aren't
        ## parsed from mal
        if not show.medium or show_medium == show.medium:
            show_medium = _findmissing_showtype(show)
            ## Only overwrite show.medium if _findmissing_showtype could determine type
            if show_medium:
                show.medium = show_medium
        ## Make sure shorts are noted
        if show.medium and "short" not in show.medium.lower()\
            and show.runtime and show.runtime.total_seconds()\
            and show.runtime.total_seconds()< (60*17):
            show.medium += " Short"
    return shows   


def _findmissing_showtype(show):
    """ Use's showids to check various sites attempting to determine its type (returns type without setting it on show). """
    showtype = None
    ## Method 2: Check the description for LiveChart's "Theatrical Premiere" Keyword
    summary = show.summary.lower()
    if "theatrical premiere" in summary:
        return "Movie"
    ## Method 3: If OVA is in any of the titles
    ## using regex for easier word bounding
    ova = re.compile(r"\bovas?\b",re.IGNORECASE)
    if any(ova.search(title) for title in [show.japanese_title,show.romaji_title,show.english_title, summary]+show.additional_titles):
        return "OVA"
    ## Method etc....etc...etc...
    if any("the movie" in title.lower() for title in [show.japanese_title, show.romaji_title, show.english_title]):
        return "Movie"
    physicalrelease = re.compile("[BD|DVD][^.]+release",re.IGNORECASE)
    if physicalrelease.search(summary):
        return "Physical Release"
    if "tv special" in summary:
        return "TV Special"
    shorts = re.compile("anime shorts?", re.IGNORECASE)
    if shorts.search(summary):
        return "Shorts"
    ## Anime Tamago is an Animation Contest
    ## While marked as "Movies" on some sites, what runtimes I've found indicate they should be listed as OVA's instead
    if any("anime tamago" in title.lower() for title in show.additional_titles):
        return "OVA"
    ## TODO

def get_lev_distance(shows):
    """ Adds a lev_distance attribute to each show which contains a lookup for the
        Levenshtein Distance of the show's japanese_title to each other show's japanese_title """
        
    ## Create attribute for all shows
    for show in shows:
        show.lev_distance = dict()

    ## Compile Levenshtein Distances
    for show in shows:
        for other in shows:
            ## Skip this show
            if other == show: continue
            ## If other show has already done the calculation, use theirs
            if show.japanese_title in other.lev_distance:
                show.lev_distance[other.japanese_title] = other.lev_distance[show.japanese_title]
            ## Otherwise calculate it yourself
            else:
                show.lev_distance[other.japanese_title] = lev_distance(show.japanese_title, other.japanese_title)

def consolidate_duplicates(shows):
    """ Consolidates duplicate shows """
    shows = consolidate_duplicates_malid(shows)
    shows = consolidate_duplicates_titles(shows)
    return shows

def consolidate_duplicates_malid(shows):
    """ Further Consolidates shows based on their malid """
    shows = list(shows)
    malids = dict()
    output = []
    while shows:
        show = shows.pop(0)
        mids = [url for link in show.links if (url := myanimelist.parse_siteid(link[1]))]
        if not mids:
            output.append(show)
            continue
        if (mid := mids[0]) in malids:
            echo(f">>> Consolidateing {malids[mid].romaji_title} with {show.romaji_title}")
            ## Can only combine shows with the same Japanese Title (may change in future)
            show.additional_titles.append(show.japanese_title)
            show.japanese_title = malids[mid].japanese_title
            malids[mid] &= show
        else: malids[mid] = show
    output.extend(malids.values())
    return output


def consolidate_duplicates_titles(shows):
    """ Further consolidates the list by looking more closely at the titles """
    output = []
    shows = list(shows)
    while shows:
        show = shows.pop(0)
        others = list(shows)
        while others:
            other = others.pop(0)
            if any(name in [other.japanese_title, other.romaji_title, other.english_title]+other.additional_titles
            for name in [show.japanese_title, show.romaji_title, show.english_title]+show.additional_titles if name):
                shows.remove(other)
                ## In order to combine shows, both need the same jp title
                if other.japanese_title != show.japanese_title:
                    if not show.japanese_title: show.japanese_title = other.japanese_title
                    elif not other.japanese_title: other.japanese_title = show.japanese_title
                    else:
                        if other.japanese_title not in show.additional_titles: show.additional_titles.append(other.japanese_title)
                        other.japanese_title = show.japanese_title
                echo(f">>>> Consolidating {show.romaji_title} with {other.romaji_title}")
                show&=other
        output.append(show)
    #get_lev_distance(output)
    return output

def remove_ero(shows):
    """ Checks for specific key phrases that indicate that a show is hentai but was not tagged as such on its chart """
    regex = re.compile("Based on.*?(ero\w*? (doujin|game|CG))", re.IGNORECASE)
    blackliststudios = ["Fancy Realize Media",]
    def filterEro(show):
        """ Return False if show is suspected of being hentai """
        ## Shows explicitly marked as hentai
        if show.medium and "hentai" in show.medium.lower():
            echo(f"> Filtering: {show.get_title()} due to being labeled as hentai")
            return False
        desc = show.summary.lower()
        ## Check for shows based on either "ero* game" or "CG":
        ## erogames are automatically filtered (may be incorrect)
        ## cgs are filtered if their description contains explicit terms
        if (research := regex.search(desc)):
            if research.group(1) == "CG":
                if any([term in desc for term in ["sex","rape","molest", "chikan"]]):
                    echo(f"> Filtering: {show.get_title()} due to explicit cg set")
                    return False
            else:
                echo(f"> Filtering: {show.get_title()} due to being based on erotic game")
                return False
        ## Filter for blacklisted studios
        ## Outside chance of being wrong, but not too likely afaict
        if any(black in show.studios for black in blackliststudios):
            echo(f"> Filtering: {show.get_title()} due to blacklisted animation studio")
            return False
        return True
    return list(filter(filterEro, shows))

def remove_shorts(shows):
    """ Removes all shows with medium "shorts" or "TV_SHORT" from the output """
    def filterShorts(show):
        if show.medium and "short" in show.medium.lower():
            echo(f"> Filtering: {show.get_title()}")
            return False
        return True
    return list(filter(filterShorts,shows))

def remove_movies(shows):
    """ Removes all shows with medium "Movie" from the output """
    def filterMovies(show):
        if show.medium and show.medium.lower() in ["movie",]:
            echo(f"> Filtering: {show.get_title()}")
            return False
        return True
    return list(filter(filterMovies,shows))

def remove_short_runs(shows):
    """ Removes shows with "half" seasons (less than 10 episodes) """
    def filterShortRuns(show):
        if show.episodes and show.episodes < 10:
            print(f"> Filtering: {show.get_title()}")
            return False
        return True
    return list(filter(filterShortRuns, shows))

def label_netflix(shows):
    for show in shows:
        if "netflix" in [l.lower() for (l,url) in show.links]:
            print(f"> Changing medium to Netflix for: {show.get_title()}")
            show.medium = "Netflix"
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
    season,year = SeasonCharts.parseseason(seasonstring)
    if not isinstance(output,pathlib.Path):
        try:
            output = pathlib.Path(output)
        except:
            raise ValueError("Could not interpret output")
    if output != DEFAULTOUTPUT and output.exists():
        raise ValueError("output location already exists!")
    return season,year,output



def get_single_show(malid: str, season: str, year:int,  charts:list = None)-> SeasonCharts.Show:
    """ Gets stats for a single show from the given season and using the provided charts and/or malid.
    
        malid is the myanimelist site id for the show. It is required in order to determine which show to retrieve. 
        season should be a valid season ("winter", "spring", "summer", "fall") and year should be an integer.
        charts should be a list of modules based on the modules available in SeasonCharts/gammut. If not provided,
        all modules will be used.
    """
    if charts:
        charts = [mod for mod in charts if mod in MODULES]
        if not charts:
            raise ValueError("No valid modules in provided charts")
    else:
        charts = list(MODULES)

    seasonstring = SeasonCharts.buildseason(season, year)
    season, year = SeasonCharts.parseseason(seasonstring)

    shows = run_gammut(season,year, modules = charts)
    if not shows:
        echo("No shows found with that malid")
    shows = [show for show in shows if any(link for (site,link) in show.links if myanimelist.parse_siteid(link) == malid)]
    if not shows:
        echo("No shows found with that malid")
    ## Consolidate into a single show
    show = shows.pop(0)
    for other in shows: show &= other
    ## Convert back into list to keep using gammut functions
    shows = [show,]
    shows = findmissing_gammut(shows)
    fname = f"show_{shows[0].get_title()}.csv"
    SeasonCharts.save_as_csv(shows,fname)
    echo(f"File saved to: {fname}")

