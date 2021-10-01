import datetime
import pathlib

import click
from click import echo
from aldb2 import SeasonCharts
from aldb2.SeasonCharts import gammut

from AL_Text import TextTable ## Used in Debug

## Default Year
YEAR = str(datetime.date.today().year)

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
@click.option("--labelNetflix", "-netflix", is_flag = True, default = True)
@click.option("--removeEro", "-re", is_flag = True, default = True)
@click.option("--removeShorts", "-rs", is_flag = True, default = True)
@click.option("--removeMovies", "-rm", is_flag = True, default = True)
@click.option("--removeShortRuns", "-rsr", is_flag = True, default = True)
def run(season,year, labelnetflix, removeero, removeshorts, removemovies, removeshortruns):
    def gather():
        """ Gathers shows from the internet and saves them to cache """
        echo(f"running gammut for {season.season} {season.year} Season")
        shows = gammut.run_gammut(season = season.season,year = season.year)
        echo("saving shows")
        SeasonCharts.serialize_shows(shows, cachefile)
        process()

    def process():
        """ Loads the cache, processes the shows, and saves them to another cache file """
        echo('loading shows')
        shows = SeasonCharts.load_serialized(cachefile)
        echo("consolidating gammut")
        shows = gammut.consolidate_gammut(shows)
        echo("consolidating duplicates")
        shows = gammut.consolidate_duplicates(shows)
        echo("gathering extra info")
        shows = gammut.findmissing_gammut(shows)
        echo("consolidating gammut with extra info")
        shows = gammut.consolidate_gammut(shows)
        echo("consolidating duplicates with extra info")
        shows = gammut.consolidate_duplicates(shows)
        echo("saving processed results")
        SeasonCharts.serialize_shows(shows, processfile)
        output()

    def output():
        """ Loads the processed cache, customizes the final output, and saves them to csv """
        echo("loading processed results")
        shows = SeasonCharts.load_serialized(processfile)
        if removeero:
            echo("removing eros")
            shows = gammut.remove_ero(shows)
        if removeshorts:
            echo("removing shorts")
            shows = gammut.remove_shorts(shows)
        if removemovies:
            echo("removing movies")
            shows = gammut.remove_movies(shows)
        if removeshortruns:
            echo("removing short-run shows")
            shows = gammut.remove_short_runs(shows)
        if labelnetflix:
            echo("labeling netflix shows")
            shows = gammut.label_netflix(shows)

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
@click.argument("malid")
@click.option("--season","-s",default="Spring")
@click.option("--year","-y",default=YEAR)
def runsingle(malid, season, year):
    gammut.get_single_show(malid, season, year)
    

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
        gammut.get_lev_distance(shows)
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

if __name__ == "__main__":
    cli()