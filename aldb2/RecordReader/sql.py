## This Module
from aldb2.RecordReader import *
## Backend
from alcustoms import sql

## Builtin
import collections
import datetime
import pathlib
## Sister Module
from aldb2.Anime import anime
from aldb2.Anime import sql as animesql
from aldb2.webmodules import sql as websql

""" Dependencies: Core, Anime, AnimeLife, webmodules """

## Stolen from https://stackoverflow.com/a/30070664/3225832
cjk_ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Kana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
]
def is_cjk(instring):
    def check(c):
        return any([range["from"] <= ord(c) <= range["to"] for range in cjk_ranges])
    return any(check(c) for c in instring)

class ImportResult():
    def __init__(self,result,reason,object):
        self.result = result
        self.reason = reason
        self.object = object
    @property
    def success(self):
        return bool(self.result)

def import_master(db, masterstats = None, masterepisodes = None, overwrite = False):
    """ Import masterstats and/or masterepisodes into the given database.

        In order to import stats and episodes with this method, the show/episode's SeasonID must
        be set. This method returns a 

        db should be a properly set up Database Connection for aldb2.
        By default, masterstats and masterepisodes refer to the module-default master file names
        in the current work directory. If provided, masterstats and/or masterepisodes should refer
        to existing files. If False, the file will not be imported into the database. If left as
        the default and the given file does not exist, the import for that filetype will be
        silently skipped.
        If overwrite is True, the database will be updated to match the provided files; existing
        records in the database that do not exist in the master file will not be removed or modified.
        By default (overwrite is False), this method will not update existing records and will only
        add missing ones.
    """
    with sql.Utilities.temp_row_factory(db,sql.advancedrow_factory):
        if masterstats:
            masterstats = pathlib.Path(masterstats).resolve()
            if not masterstats.exists():
                raise ValueError("masterstats must be an existing file.")
        if masterepisodes:
            masterepisodes = pathlib.Path(masterepisodes).resolve()
            if not masterepisodes.exists():
                raise ValueError("masterepisodes must be an existing file.")
        if masterstats is None:
            masterstats = pathlib.Path(master.DEFAULTSTATFILE).resolve()
            if not masterstats.exists():
                masterstats = None
        if masterepisodes is None:
            masterepisodes = pathlib.Path(master.DEFAULTEPISODEFILE).resolve()
            if not masterepisodes.exists():
                masterepisodes = None

        stats = []
        if masterstats:
            stats = master.load_masterstats(masterstats)
        episodes = []
        if masterepisodes:
            episodes = master.load_masterepisodes(masterepisodes)

        ## Potential early exit to save time
        if not stats and not episodes: return

        ## Constant, Lookup, and Table Setup 
        ANIMEMEDIUM = db.getadvancedtable("mediums").quickselect(medium__like = "anime").first()
        if ANIMEMEDIUM is None:
            raise AttributeError("anime medium is not defined in the database")
        ANIMEMEDIUM = ANIMEMEDIUM.mediumid
        SEASONLOOKUP = animesql.getseasonallookup(db)

        if stats:
            """
                ### Stats
                # Season Table: seasonid 
                #
                # Aliases: originalname name	
                # AnimeLibrary: notes
                # AnimeSeasons: seasonindex
                # Images_Anime: image
                # Links_Anime: website channel/channelhomepage pv
                # AiringInfo: firstepisode
                # webmodules_SiteIDs: showboyid annid anilistid malid anidbid 
                #
                # Unused: originalid seriesid subseriesid watching include day group rssfeedname hashtag lastseason 
                #
                ## >seriesid and subseriesid should validate seasonid
            
            """

            seasontable = db.getadvancedtable("season")
            aliasestable = db.getadvancedtable("aliases_season")
            animeseasonstable = db.getadvancedtable("animeseasons")
            librarytable = db.getadvancedtable("animelibrary")
            linkstable = db.getadvancedtable("links_anime")
            imagestable = db.getadvancedtable("images_anime")
            airingtable = db.getadvancedtable("airinginfo")
            sitestable = db.getadvancedtable("webmodules_siteids")
            websitetable = db.getadvancedtable("webmodules_website")

            for season in stats:
                ## We'll use continue to cut down on the indentation
                if not season.seasonid:
                    outstats.append(ImportResult(False,"No seasonid",season))
                    continue
                dbentry = seasontable.quickselect(seasonid = season.seasonid).first()
                #print(f"Updating Season: {dbentry.row}")
            
                if not dbentry: 
                    outstats.append(ImportResult(False,"seasonid not in Database",season))
                    continue

                ## English Name
                if season.name:
                    result = aliasestable.get_or_addrow(season = season.seasonid, seasonalias = season.name, language = "english").first()
                    #print(f"Added English Name: {seasontable.quickselect(pk = dbentry).first().row}")

                ## Japanese Alias
                if season.originalname:
                    result = aliasestable.get_or_addrow(season = season.seasonid, seasonalias = season.originalname, language = "japanese").first()
                    #print(f"Added Japanese Alias: {aliasestable.quickselect(pk = result).first().row}")

                ## notes
                if season.notes:
                    result = librarytable.get_or_addrow(season = season.seasonid).first()
                    libraryentry = librarytable.quickselect(libraryid = result).first()
                    notes = ""
                    if libraryentry.notes: notes = libraryentry.notes
                    librarytable.quickupdate(WHERE ={"libraryid":libraryentry}, notes = notes + season.notes)
                    #print(f"Updated Library: {librarytable.quickselect(pk = libraryentry).first().row}")

                ## Season
                animeseason = anime.parseanimeseason_toobject(season.seasonindex)
                animeseasonid = animeseasonstable.get_or_addrow(seasonid = dbentry, season = SEASONLOOKUP[animeseason.season], year = animeseason.year).first()
                res = animeseasonstable.quickselect(pk = animeseasonid).first()

                ## firstepisode
                if season.firstepisode:
                    airinginfo = airingtable.get_or_addrow(animeseason = animeseasonid).first()
                    try:
                        dt = datetime.datetime.strptime(season.firstepisode,"%Y-%m-%d %H:%M:%S")
                    except:
                        dt = datetime.datetime.strptime(season.firstepisode,"%Y-%m-%d %H:%M:%S.%f")
                    airingtable.quickupdate(WHERE = {"pk":airinginfo}, firstepisode = dt.date(), time = str(dt.time().replace(microsecond = 0)))#.strftime("%H:%M:%S"))
                    #res = airingtable.quickselect(pk = airinginfo).first()
                    #print(f"Added first episode: {res.row}")

                ## image
                if season.image:
                    res = imagestable.get_or_addrow(season = season.seasonid, url = season.image, imagetype = "poster").first()
                    #res = imagestable.quickselect(pk = res).first()
                    #print(f"Added image: {res.row}")
                
                ## website
                if season.website:
                    res = linkstable.get_or_addrow(season = season.seasonid, url = season.website, identification = "homepage").first()
                    #res = linkstable.quickselect(pk = res).first()
                    #print(f"Added website: {res.row}")

                ## stream
                if season.channelhomepage:
                    res = linkstable.get_or_addrow(season = season.seasonid, url = season.channelhomepage, identification = "stream").first()
                    #res = linkstable.quickselect(pk = res).first()
                    #print(f"Added homepage: {res.row}")

                ## pv
                if season.pv:
                    res = linkstable.get_or_addrow(season = season.seasonid, url = season.pv, identification = "pv").first()
                    #res = linkstable.quickselect(pk = res).first()
                    #print(f"Added pv: {res.row}")

                ## siteids
                for (kw,value) in season.to_dict().items():
                    if value and kw.endswith("id") and kw.lower() not in ['originalid','seasonid','subseriesid','seriesid']:
                        site = kw.rstrip("id")
                        res = websql.validate_add_siteid(db,season.seasonid,site,value)
                        #res2 = sitestable.quickselect(pk = res).first()
                        #print(f"Added {site} Siteid: {res2.row} {res2.website.row}")

        if episodes:
            """
                ### Episodes
                # Season Table seasonid
                #
                # AnimeLibrary: sum(episodes)
                # AnimeSeason: seasonindex
                # AL_WeeklyRanking: week rank episodenumber hypelistrank
                #
                # Unused: originalid
                #
                ## >seriesid and seasonindex should exist in Stats
            """

            ## Episodelookup is a lookup formatted: {"{seasonid}-{seasonindex}": [episodes],}
            episodelookup = collections.defaultdict(list)
            for episode in episodes:
                if episode.seasonid and episode.seasonindex:
                    episodelookup[f"{episode.seasonid}-{episode.seasonindex}"].append(episode)

            seasontable = db.getadvancedtable("season")
            librarytable = db.getadvancedtable("animelibrary")
            animeseasonstable = db.getadvancedtable("animeseasons")
            rankingtable = db.getadvancedtable("al_weeklyranking")


            for seasonepisodes in episodelookup.values():
                first = seasonepisodes[0]

                yearseasonid = first.animeseason.season
                yearseasonid = SEASONLOOKUP[yearseasonid]
                seasonid = animeseasonstable.get_or_addrow(seasonid = first.seasonid, season = yearseasonid, year = first.animeseason.year).first()
                #print("Added AnimeSeason:", dict(animeseasonstable.quickselect(pk = seasonid).first().row))

                for episode in seasonepisodes:
                    rankingid = rankingtable.quickselect(animeseason = seasonid, week = episode.week, episodenumber = episode.episodenumber).first()
                    if not rankingid:
                        rankingid = rankingtable.addrow(animeseason = seasonid, week = episode.week, episodenumber = episode.episodenumber, rank = episode.rank)
                    rankingtable.quickupdate(WHERE = {"pk":rankingid}, rank = episode.rank, hypelistrank = episode.hypelistrank)
                    #print("Added Episode:", dict(rankingtable.quickselect(pk = rankingid).first().row))


                ## len(episodes)
                allseasons = animeseasonstable.quickselect(seasonid = first.seasonid)
                allepisodes = list(itertools.chain.from_iterable([rankingtable.quickselect(animeseason = aseason) for aseason in allseasons]))
                if not allepisodes:
                    raise ValueError()

                allepisodes = len(allepisodes)

                ## season.episodes
                season = seasontable.quickselect(pk = first.seasonid).first()
                eps = season.episodes
                if not eps: eps = 0
                if allepisodes > eps:
                    seasontable.quickupdate(WHERE = {"pk":season}, episodes = allepisodes)
                    #print(f"Updated Season episodes count:", dict(seasontable.quickselect(pk = season).first().row))

                ## len(episodes)
                libraryid = librarytable.get_or_addrow(season = first.seasonid).first()
                libraryentry = librarytable.quickselect(pk = libraryid).first()
                eps = libraryentry.episodeswatched
                if not eps: eps = 0
                if allepisodes > eps:
                    librarytable.quickupdate(WHERE = {"pk":libraryentry}, episodeswatched = allepisodes)
                    #print(f"Updated library episodewatched count:", dict(librarytable.quickselect(pk = libraryentry).first().row))

def compile_masterstats(db, animeseasonid):
    """ Compiles the MasterStats object from the database for the given animeseasonid """
    with sql.Utilities.temp_row_factory(db,sql.advancedrow_factory):
        animeseasonstable = db.getadvancedtable("animeseasons")
    season = animeseasonstable.quickselect(pk = animeseasonid).first()

    if not season: raise ValueError("Invalid animeseasonid")
    """ Current stats
    ## Season
    seasonid, name
    ## AnimeSeasons
    seasonindex, renewal, lastseason
    ## Aliases_Season
    originalname (jpn)
    ## Links_Anime
    channel + channelhomepage (homepage), website , pv
    ## AiringInfo
    firstepisode
    ## Images_Anime
    image (poster)
    ## AnimeLibrary
    notes
    ## AL_WeeklyRanking
    include (can be assumed by existence of episodes)
    ## Webmodules_SiteIDs
    showboyid , annid , anilistid , malid , anidbid

    ## Can't use
    originalid, watching , day , group , rssfeedname , hashtag
    """

    with sql.Utilities.temp_row_factory(db,sql.advancedrow_factory):
        aliasestable = db.getadvancedtable("aliases_season")
        linkstable = db.getadvancedtable("links_anime")
        airingtable = db.getadvancedtable("airinginfo")
        imagestable = db.getadvancedtable("images_anime")
        librarytable = db.getadvancedtable("animelibrary")
        rankingtable = db.getadvancedtable("al_weeklyranking")
        websitetable = db.getadvancedtable("webmodules_website")
        siteidtable = db.getadvancedtable("webmodules_siteids")
    
    ## Originalid is a positional arg butcannot be retrieved at current
    ## (may add a recordreader datbabase table later that can track it)
    output = dict(originalid = None)
    output['seasonid'] = season.seasonid.pk
    output['subseriesid'] = season.seasonid.subseries.pk
    output['seriesid'] = season.seasonid.subseries.series.pk

    yseason = animesql.get_AnimeSeason(season)
    output['seasonindex'] = float(yseason)
    
    allaseas = animeseasonstable.quickselect(seasonid = season.seasonid)
    for seas in allaseas:
        if not seas.season:
            print(seas.row)
        seas.AnimeSeason = animesql.get_AnimeSeason(seas)
    previousseas = sorted([seas for seas in allaseas if  seas.AnimeSeason < yseason], key = lambda seas: seas.AnimeSeason)

    if previousseas:
        output['renewal'] = True
        output['lastseason'] = str(previousseas[-1].AnimeSeason)

    enalias = aliasestable.quickselect(season = season.seasonid, language__like = "english").first()
    if enalias:
        output['name'] = enalias.seasonalias
    else:
        with sql.Utilities.temp_row_factory(db,sql.dict_factory):
            res = db.execute("""SELECT fulltext FROM season_fulltext WHERE seasonid = ?;""",(season.seasonid.pk,)).fetchone()
            output['name'] = res
    jpalias = aliasestable.quickselect(season = season.seasonid, language__like = "japanese").first()
    if jpalias:
        output['originalname'] = jpalias.seasonalias

    homepage = linkstable.quickselect(season = season.seasonid, identification = "stream").first()
    if homepage:
        output['channelhomepage'] = homepage.url
    website = linkstable.quickselect(season = season.seasonid, identification = "homepage").first()
    if website:
        output['website'] = website.url
    pv = linkstable.quickselect(season = season.seasonid, identification = "pv").first()
    if pv:
        output['pv'] = pv.url

    airinginfo = airingtable.quickselect(animeseason = season).first()
    if airinginfo:
        if airinginfo.firstepisode and airinginfo.time:
            output['firstepisode'] = datetime.datetime.strptime(airinginfo.firstepisode+" "+airinginfo.time,"%Y-%m-%d %H:%M:%S")

    poster = imagestable.quickselect(season = season.seasonid, imagetype = "poster").first()
    if poster:
        output['poster'] = poster.url

    libraryitem = librarytable.quickselect(season = season.seasonid).first()
    if libraryitem.notes:
        output['notes'] = libraryitem.notes

    episodes = rankingtable.quickselect(animeseason = season)
    ## If we had any episode rankings, then the season is included
    if episodes:
        output['include'] = True
    
    for heading in ["showboyid", "annid", "anilistid", "malid", "anidbid"]:
        sitename = heading.rstrip("id")
        sitemodule = websql.get_sitemodule(db,sitename)
        site = websitetable.quickselect(name = sitemodule.SITENAME).first()
        sid = siteidtable.quickselect(season = season.seasonid, website = site).first()
        if sid:
            #print(f"{season.pk}\t{sitename}\t{sid}")
            output[heading] = sid.siteid

    return master.MasterStat(**output)

def compile_masterepisodes(db, animeseasonid):
    """ Compiles a list of MasterEpisode objects from the database for the given animeseasonid """
    with sql.Utilities.temp_row_factory(db,sql.advancedrow_factory):
        animeseasonstable = db.getadvancedtable("animeseasons")
        rankingtable = db.getadvancedtable("al_weeklyranking")

    season = animeseasonstable.quickselect(pk = animeseasonid).first()
    episodes = rankingtable.quickselect(animeseason = season)
    """ Current Stats:
        ## Season
        seasonid
        ## AnimeSeasons
        seasonindex
        ## AL_WeeklyRanking
        week, rank, episodenumber, hypelistrank
        ## Unused
        originalid
    """
    def convert(episode):
        ## Originalid is a positional arg butcannot be retrieved at current
        ## (may add a recordreader datbabase table later that can track it)
        output = dict(originalid = None)
        output['week'], output['rank'],output['episodenumber'],output['hypelistrank'] =\
            episode.week, episode.rank, episode.episodenumber,episode.hypelistrank
        output['seasonindex'] = float(animesql.get_AnimeSeason(episode.animeseason))
        output['seasonid'] = episode.animeseason.seasonid.seasonid
        return master.MasterEpisode(**output)

    return [convert(episode) for episode in episodes]

def export_master(db, seasons = None, masterstats = None, masterepisodes = None):
    """ Exports database into masterstats and masterepisodes files.

        This function uses RecordReader.master's save_masterstats and save_masterepisodes to export masterstats and masterepisodes (respectively).
        seasons should be a list of AnimeSeason objects or objects that can be parsed into AnimeSeasons by Anime.anime.parseanimeseason.
        If seasons is None, all seasons will be exported from the database.
        If masterstats or masterepisodes if False, that file will not be exported. If not supplied, these files will be exported to
        the current work directory using the names "master_episodes.csv" and "master_episodes.csv", respectively. Otherwise, filenames or file
        paths should be supplied.
    """
    if masterstats is None:
        masterstats = master.DEFAULTSTATFILE
    if masterepisodes is None:
        masterepisodes = master.DEFAULTEPISODEFILE

    if masterstats and masterstats.exists():
        raise FileExistsError("masterstats file already exists")
    if masterepisodes and masterepisodes.exists():
        raise FileExistsError("masterepisodes file already exists")

    rankingtable = db.getadvancedtable("al_weeklyranking")
    trf = sql.Utilities.temp_row_factory
    if seasons:
        if not isinstance(seasons,(list,tuple)):
            raise TypeError("Invalid seasons argument: should be a list or None")
        if not all(isinstance(season,anime.AnimeSeason) for season in seasons):
            try:
                seasons = [anime.parseanimeseason_toobject(season) for season in seasons]
            except:
                raise TypeError("Could not interpret seasons to AnimeSeason Objects")
    else:
        with trf(db,sql.dict_factory):
            seasons = db.execute("""
WITH 
    aseas AS (
        SELECT DISTINCT animeseason FROM al_weeklyranking
        )
SELECT DISTINCT year, season
FROM aseas
LEFT JOIN animeseasons ON animeseasons.animeseasonid = aseas.animeseason""").fetchall()
            seasons = [anime.parseanimeseason_toobject(season) for season in seasons]

    ## Should only happen if no rankings have occured and seasons has not been manually set
    if not seasons: return
    seasons = [f'"{season}"' for season in seasons]
    seasons = f"({','.join(seasons)})"
    animeseasonstable = db.getadvancedtable("animeseasons")
    with trf(db,sql.AdvancedRow_Factory(parent = animeseasonstable)):
        series = db.execute(f"""
WITH
    yearseas AS (
        SELECT animeseasonid, yearseason.season||" "||year AS yearseason
        FROM animeseasons
        LEFT JOIN yearseason ON animeseasons.season = yearseason.yearseasonid
        )
    SELECT animeseasons.animeseasonid as animeseasonid
    FROM animeseasons
    LEFT JOIN yearseas ON animeseasons.animeseasonid = yearseas.animeseasonid
    WHERE yearseas.yearseason IN {seasons};
""").fetchall()
    
    if masterstats:
        seasons = [compile_masterstats(db,**season.row)
                   for season in series]
        master.save_masterstats(seasons,masterstats)

    if masterepisodes:
        episodes = [compile_masterepisodes(db,**season.row) for season in series]
        episodes = list(itertools.chain.from_iterable(episodes))
        episodes = sorted(sorted(episodes, key = lambda episode: episode.week), key = lambda episode: episode.seasonindex)
        master.save_masterepisodes(episodes,masterepisodes)