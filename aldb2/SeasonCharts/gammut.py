## Builtin
import datetime
import pathlib
import re
## This Module
from aldb2 import Core
from aldb2 import SeasonCharts
from aldb2.SeasonCharts import anilist
## ,livechart ## livechart's new cloudflare protection is difficult to get by; livechart is not vital enough to put more effort into
## ,anichart ## It seems that anichart may be an exact mirror of anilist at this point
from aldb2.WebModules import myanimelist ## Used to get additional information about shows
from aldb2.WebModules.myanimelist.scraping import getshowstats ## Used to get additional information about shows

## Third Party
from Levenshtein import distance as lev_distance

""" A temporary module for gathering charts """

DEFAULTOUTPUT = pathlib.Path("output_gammut.json").resolve()

## Order represents precedence when consolidating data
MODULES = [anilist, ] ## livechart, anichart ## See notes above

## Default Year
YEAR = str(datetime.date.today().year)

## Dev Mode
VERBOSE = False
VERBOSE = True ## comment out
import traceback ## comment out

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
        ## Mal is now used unconditionally (not only for missing data)
        _findmissing_mal(show)
        ## We're now double-checking all show mediums that aren't
        ## parsed from mal
        if not show.medium or show_medium == show.medium:
            show_medium = _findmissing_showtype(show)
            ## Only overwrite show.medium if _findmissing_showtype could determine type
            if show_medium:
                show.medium = show_medium
    return shows

def _findmissing_mal(show):
    """ Uses MAL (if available) to fill in whatever info it can """
    ids = [url for link in show.links if (url := myanimelist.parse_siteid(link[1]))]
    malinfo = None
    for link in ids:
        try:
            echo(f">>> {show.romaji_title}({link})")
            malinfo = getshowstats(link)
        except Exception as e:
            echo(f">>> Failed to get MAL info for: {show.romaji_title if show.romaji_title else show.english_title}({link})")
            if VERBOSE: echo(traceback.format_exc())
        if malinfo: break
    if not malinfo: return
    if not show.medium and malinfo['type']:
        show.medium = malinfo['type']
    ## Hard overriding because
    if "rating" in malinfo and "hentai" in malinfo['rating'].lower():
        show.medium = "Hentai"
    if (runtime := malinfo.get('runtime')) and (runtime.seconds / 60 ) < 17:
        show.medium = "TV SHORT"



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

    get_lev_distance(shows)
    return shows

def remove_ero(shows):
    """ Checks for specific key phrases that indicate that a show is hentai but was not tagged as such on its chart """
    regex = re.compile("Based on.*?(ero\w*? (doujin|game|CG))", re.IGNORECASE)
    blackliststudios = ["Fancy Realize Media",]
    def filterEro(show):
        """ Return False if show is suspected of being hentai """
        ## Shows explicitly marked as hentai
        if show.medium and show.medium.lower() == "hentai":
            echo(f"> Filtering: {show.romaji_title} due to being labeled as hentai")
            return False
        desc = show.summary.lower()
        ## Check for shows based on either "ero* game" or "CG":
        ## erogames are automatically filtered (may be incorrect)
        ## cgs are filtered if their description contains explicit terms
        if (research := regex.search(desc)):
            if research.group(1) == "CG":
                if any([term in desc for term in ["sex","rape","molest", "chikan"]]):
                    echo(f"> Filtering: {show.romaji_title} due to explicit cg set")
                    return False
            else:
                echo(f"> Filtering: {show.romaji_title} due to being based on erotic game")
                return False
        ## Filter for blacklisted studios
        ## Outside chance of being wrong, but not too likely afaict
        if any(black in show.studios for black in blackliststudios):
            echo(f"> Filtering: {show.romaji_title} due to blacklisted animation studio")
            return False
        return True
    return list(filter(filterEro, shows))

def remove_shorts(shows):
    """ Removes all shows with medium "shorts" or "TV_SHORT" from the output """
    def filterShorts(show):
        if show.medium and show.medium.lower() in ["shorts", "tv_short", "tv short"]:
            echo(f"> Filtering: {show.romaji_title}")
            return False
        return True
    return list(filter(filterShorts,shows))

def remove_movies(shows):
    """ Removes all shows with medium "Movie" from the output """
    def filterMovies(show):
        if show.medium and show.medium.lower() in ["movie",]:
            echo(f"> Filtering: {show.romaji_title}")
            return False
        return True
    return list(filter(filterMovies,shows))


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
    import click
    from click import echo

    from alcustoms.text.texttable import TextTable ## Used in Debug


    CACHEFILE = pathlib.Path("output_gammut.json")
    PROCESSFILE = pathlib.Path("process_gammut.json")
    OUTPUTFILE = pathlib.Path("output_gammut.csv")
    
    ## Debug files
    LEV_DEBUGFILE =pathlib.Path("debug_levenshtein_distance.txt")

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--season","-s",default="Spring")
    @click.option("--year","-y",default=YEAR)
    @click.option("--removeEro", "-re", is_flag = True, default = True)
    @click.option("--removeShorts", "-rs", is_flag = True, default = True)
    @click.option("--removeMovies", "-rm", is_flag = True, default = True)
    def run(season,year, removeero, removeshorts, removemovies):
        def gather():
            """ Gathers shows from the internet and saves them to cache """
            echo(f"running gammut for {season.season} {season.year} Season")
            shows = run_gammut(season = season.season,year = season.year)
            echo("consolidating gammut")
            shows = consolidate_gammut(shows)
            echo("saving shows")
            SeasonCharts.serialize_shows(shows, cachefile)
            process()

        def process():
            """ Loads the cache, processes the shows, and saves them to another cache file """
            echo('loading shows')
            shows = SeasonCharts.load_serialized(cachefile)
            echo("gathering extra info")
            shows = findmissing_gammut(shows)
            echo("consolidating duplicates")
            shows = consolidate_duplicates(shows)
            echo("saving processed results")
            SeasonCharts.serialize_shows(shows, processfile)
            output()

        def output():
            """ Loads the processed cache, customizes the final output, and saves them to csv """
            echo("loading processed results")
            shows = SeasonCharts.load_serialized(processfile)
            if removeero:
                echo("removing eros")
                shows = remove_ero(shows)
            if removeshorts:
                echo("removing shorts")
                shows = remove_shorts(shows)
            if removemovies:
                echo("removing movies")
                shows = remove_movies(shows)
            echo("writing to csv")
            ## Writing to csv
            SeasonCharts.save_as_csv(shows, outputfile)
            echo("done")


        from aldb2.Anime import anime
        try:
            season = anime.parseanimeseason_toobject(dict(season = season,year = year))
        except:
            echo("Invalid Season")
            return

        echo(f"Gather Shows for {season} Season")
        processfile = PROCESSFILE.with_name(PROCESSFILE.stem+"-"+str(season)+PROCESSFILE.suffix)
        cachefile = CACHEFILE.with_name(CACHEFILE.stem+"-"+str(season)+CACHEFILE.suffix)
        outputfile = OUTPUTFILE.with_name(OUTPUTFILE.stem+"-"+str(season)+OUTPUTFILE.suffix)

        def ask(item):
            use = None
            while use not in ["y","n"]:
                use = input(f"{item}? (y/n)").lower()
            return use == "y"
                
        def ask_use_delete_file(FILE, name):
            if FILE.exists():
                use = ask(f"Use {name}")
                if not use:
                    delete = ask(f"Delete {name}")
                    if delete:
                        FILE.unlink()
                return use
        
        result = ask_use_delete_file(processfile, "processed cached results")
        if result: return output()
        
        result = ask_use_delete_file(cachefile, "cached results")
        if result: return process()

        return gather()

    @cli.command()
    def config():
        echo("hello")

    @cli.command()
    @click.argument("mode")
    def debug(mode):
        if mode == "lev_distance":
            if not cachefile.exists():
                raise ValueError("No Cached Shows: Call run first")
            shows = SeasonCharts.load_serialized(cachefile)
            get_lev_distance(shows)
            output = ""
            for show in shows:
                rows = list(show.lev_distance.items())
                ## Sort smallest distance > Larger Distance
                rows = sorted(rows, key = lambda row: row[1])
                table = TextTable(title = show.japanese_title, headers = ["Show", "Distance"], rows = rows)
                output += str(table) + "\n"
            with open(LEV_DEBUGFILE, 'w', encoding = "UTF-8") as f:
                f.write(output)
            echo(f"Log written to: {LEV_DEBUGFILE}")

    cli()
