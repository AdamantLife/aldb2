## This Module
from aldb2 import Calendar
from aldb2.WebModules import anilist
from aldb2.WebModules.anilist import graphql

## Custom Module
from alcustoms import web
from alcustoms.web import requests as alrequests



@alrequests.sessiondecorator
def getshowarings_graphql(shows, session = None):
    """ Uses anilist's GraphQL API to get Show Airings """
    ## Get urls for the shows that it's available
    for show in shows:
        print(show)
    anilistids = [show.anilist_id for show in shows if show.anilist_id]
    for show in shows:
        print(show,show.anilist_id)
    ## Convert urls to ids
    anilistids = [anilist.parseidfromurl(anid) for anid in anilistids]
    if not anilistids: return

    mediaPage = 1
    mediahasNextPage = True
    ## Default PageInfo with "hasNextField" to aid iteration; works with both QueryPage and AiringSchedule
    pageinfo = graphql.getpageinfo()
    while mediahasNextPage:
        airingPage = 1
        airinghasNextPage = True
        while airinghasNextPage:
            airingschedule = getairingschedule(page = airingPage, pageInfo = pageinfo)
            media = graphql.PageMedia("id",airingschedule,id_in = anilistids)
            mediapage = graphql.getpage(pageinfo,media,page = mediaPage)
            querystring = mediapage.getquery()
            print(querystring)
            airinghasNextPage = False
            mediahasNextPage = False
            ## graphql.query_api(querystring)
            ## TODO:
            ## query server
            ## parse/store output
            ## update airinghasNextPage based on aggregate of shows' airingSchedule[pageInfo]
            ## (Looking at iQL, looks like you can query for additional pages so long as at least one thing returns
            ## i.e.- Show1 has 12 eps, Show2 has 24 eps => batch of 12 => hasNextPage Show1: False, Show2: True =>
            ## querying again does not raise page index error, and simply returns empty list for Show1)
            airingPage += 1
        ## TODO: update mediahasNextPage based on latest result's Page[pageInfo]
        mediaPage += 1
    return ## TODO EpisodeAiring objects (possibly subclass)

def getairingschedule(page = None, pageInfo = None):
    """ Generates a new AiringConnection node.

    page should be a positive integer.
    pageInfo should be an PageInfo instance. If omitted, will be generated using graphql.getpageinfo().
    """
    if page:
        if not isinstance(page,int) or page <= 0:
            raise ValueError("page should be a positive integer")
    if not pageInfo:
        pageInfo = graphql.getpageinfo()
    nodes = graphql.AiringNodes("episode","airingAt")
    airingschedule = graphql.MediaAiringSchedule(nodes,pageInfo, perPage = 50, page = page)
    return airingschedule

if __name__ == "__main__":
    FILE = r"C:\Users\Reid\Dropbox\][Video Editing\AnimeLife\__Record SP2018.xlsx"

    SHOWS = None

    Calendar.getshowairings(FILE,gathermethod=getshowarings_graphql)

