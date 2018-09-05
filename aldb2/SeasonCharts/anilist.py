## Builtin
import datetime

## This Module
from aldb2 import SeasonCharts
from aldb2.WebModules import anilist,myanimelist
from aldb2.WebModules.anilist import graphql

## Custom Module
from alcustoms import web


""" ALDB2 Integration at Bottom """

#####################################################################
"""
                          General
                                                                  """
#####################################################################
        

#####################################################################
"""
                          GraphQL Integration
                                                                  """
#####################################################################

def graphql_getchartstats(season,year):
    """ GraphQL API method for gathering SeasonChart Information """
    shows = list()
    session = web.getbasicsession()
    aseason = SeasonCharts.buildseason(season,year)

    ## Season Field and PageInfo are the same for every iteration
    seasonfield = getchartstats_season(season,year)
    pageinfo = graphql.PageInfo("hasNextPage")

    ## Looping over pagination
    page = 1
    hasNextPage = True
    while hasNextPage:
        query = \
                graphql.getpage(
                    pageinfo,
                    seasonfield,
                    page=page
                    )
        querystring = query.getquery()
        response = graphql.query_api(querystring,{},session = session)
        if not isinstance(response,dict):
            print(response)
            print(response.json())
            raise AttributeError("Failed to successfully Query Server")
        ## data is just basically a wrapper and Page has the info we're interested
        response = response['data']['Page']

        ## Update our Loop variables
        hasNextPage = response['pageInfo']['hasNextPage']
        page += 1

        ## Show list is under "media"
        shows.extend(response["media"])
    out = list()
    for show in shows:
            titles = show['title']
            relations = show['relations']['edges']
            relationtypes = [rel['relationType'] for rel in relations]
            start = show['startDate']
            startyear, startmonth, startday = start['year'],start['month'],start['day']
            studionodes = show['studios']['nodes']
            externallinks = show['externalLinks']
            anilistid = anilist.ANIMEURL.format(identification = show['id'])
            malid = myanimelist.MAL_URL.format(identification = show['idMal'])

            japanese_title = titles['native']
            romaji_title = titles["romaji"]
            english_title = titles['english']
            additional_titles = show['synonyms']
            medium = show['format']
            ## TODO continuing
            renewal = any(relation == graphql.SEQUEL for relation in relationtypes)
            summary = show['description']
            tags = [(tag['name'],tag['isGeneralSpoiler']) for tag in show['tags']]
            if startyear and startmonth:
                if not startday:
                    startday = 1
            else:
                startyear,startmonth,startday =datetime.MINYEAR,1,1
            startdate = datetime.datetime(startyear,startmonth,startday,tzinfo=web.JST)
            episodes = show['episodes']
            images = show['coverImage']['large']
            if studionodes:
                studios = [studionodes[0]['name'],]
            else: studios = list()
            links = [(link['site'],link['url']) for link in externallinks]
            links.append(("MAL ID",malid))
            out.append(SeasonCharts.Show(
                chartsource=[(CHARTNAME,anilistid),], season = aseason, japanese_title = japanese_title, romaji_title= romaji_title, english_title = english_title,
                additional_titles=additional_titles, medium = medium, renewal = renewal, summary = summary, tags= tags, startdate = startdate, episodes = episodes,
                images = images, studios = studios, links = links
                ))
    return out



def getchartstats_season(season,year):
    """ Method for generating the Season element for use in graphql_getchartstats """
    titlefield = graphql.MediaTitle("native","romaji","english")
    linksfield = graphql.MediaExternalLink("site","url")
    relationsfield = graphql.MediaConnection(
        graphql.MediaEdges(
            "relationType",
            graphql.MediaNode("type","id",
                              graphql.MediaTitle("userPreferred"))
            )
        )
    startDatefield = graphql.startDate("year","month","day")
    trailerfield = graphql.MediaTrailer("site")
    tagsfield = graphql.MediaTags("id","name","isGeneralSpoiler","rank")
    imagefield = graphql.MediaCoverImage("large")
    studiosfield = graphql.MediaStudios(
        graphql.StudioNodes("name"),
        isMain = True
        )
    seasonfields = ("id","idMal","format",titlefield,"episodes",startDatefield,trailerfield,relationsfield,linksfield,"hashtag","synonyms","description",tagsfield,imagefield,studiosfield)
    return getseasonmedia("Spring",2018,*seasonfields,type = graphql.ANIME)

def getseasonmedia(season,year,*fields,**filters):
    """ Returns a PageMedia for the given season """
    if not isinstance(year,int) and year < 0:
        raise ValueError("Invalid Year Argument")
    if isinstance(season,str):
        stringseasons = [str(SEAS) for SEAS in graphql.MediaSeason]
        if season.upper() in stringseasons:
            season = graphql.MediaSeason[stringseasons.index(season.upper())]
    if season not in graphql.MediaSeason:
        raise ValueError("Season must be a string representing a season or a Constant in graphql.MediaSeason")
    filters['season'] = season
    filters['seasonYear'] = year
    return graphql.PageMedia(*fields,**filters)


#####################################################################
"""
                            ALDB2 INTEGRATION
                                                                  """
#####################################################################
CHARTNAME = "Anilist"

def getshowsbyseason(season,year, querymethod = graphql_getchartstats):
    """ Returns shows given the season and year """
    shows = querymethod(season,year)
    return shows

def convertshowstostandard(shows, showfactory = SeasonCharts.Show):
    """ Converts shows that are created by this module into the Standardized Format for the SeasonCharts module """
    if any(not isinstance(show,showfactory) for show in shows):
        raise AttributeError("This module expects to only use the stock showfactory")
    return shows



if __name__ == "__main__":
    response = graphql_getchartstats("Spring",2018)
    print(response)
    if not response.ok:
        print(response.json())
        print(response.request.body)