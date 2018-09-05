## This Module
from aldb2.Core.sql import util
from aldb2 import SeasonCharts
from aldb2.SeasonCharts import gammut


def gammut_main(connection, season = None, year = None, output = gammut.DEFAULTOUTPUT):
    """ Runs gammut's main function and then imports the results into the database. """
    gammut.main(season = season, year = year, output = output)
    shows = SeasonCharts.load_serialized(output)

    def checktitle(title):
        """ subfunction for checking titles """
        matches = getshowbytitle(connection,title = title)
        matches = [mat for mat in matches if mat['season'] == season and mat['year'] == year]
        ## This is a little obnoxious, but we'll just have to assume we're only going to get one match at this point
        if matches: return matches[0]

    for show in shows:
        match = None
        for title in [show.japanese_title,show.romaji_title,show.english_title]+show.additional_titles:
            match = checktitle(title)
            ## If we found a title, we can stop
            if match: break
        if not match:
            ## If no match, we add to database
            addshow(show)
        else:
            ## Otherwise, we update
            updatebyshow(connection, match['scshowid'],show)
            

        

################ SeasonCharts_Shows
@util.row_factory_saver
def getshowbytitle(connection, title):
    """ Gets shows with a matching title """
    liketitle = f"%{title}%"
    shows = connection.execute("""
SELECT scshowid,animeseasonid,season,year,japanesetitle,romajititle,englishtitle,additionaltitles,medium,continuing,summary
FROM "SeasonCharts_shows"
WHERE japanesetitle =:title OR romajititle =:title OR englishtitle =:title OR additionaltitles LIKE :liketitle;""",dict(title = title, liketitle = liketitle)).fetchall()
    if not shows: return
    return [{"scshowid":show[0],"animeseasonid":show[1],"season":show[2],"year":show[3],"japanesetitle":show[4],
             "romajititle":show[5],"englishtitle":show[6],"additionaltitles":show[7],"medium":show[8],"continuing":show[9],"summary":show[10]}
            for show in shows]


def addshow(connection,show):
    """ Adds a show object to the database """
    connection.execute("""
INSERT INTO "SeasonCharts_shows"
(season,year,japanesetitle,romajititle,englishtitle,additionaltitles,medium,continuing,summary)
VALUES (:season,:year,:japanese_title,:romaji_title,:english_title:additionaltitles,:medium,:continuing,:summary);""",
dict(season = show.season, year = show.year, japanese_title = show.japanese_title, english_title = show.english_title, additionaltitles = ", ".join(show.additional_titles),
     medium = show.medium, continuing = int(show.continuing), summary = show.summary))

def updatebyshow(connection,showid,show):
    """ Uses a show object to update a database entry """
    connection.execute("""
UPDATE "SeasonCharts_shows"
SET 
WHERE scshowid = :scshowid

""")