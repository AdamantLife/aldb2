## Builtin
import csv
import datetime
import itertools
import pathlib
import re
import warnings
import typing

## This Module
from aldb2.Anime import anime

## Custom Module
from alcustoms import filemodules
import AL_Excel ## Extension of openpyxl
from AL_Excel import Tables, EnhancedTable
from openpyxl.worksheet.worksheet import Worksheet

"""
Sheet Version History:

NOTE: For early version (Version < 3) Workbooks (and their associated versions) had some degree of undocumented updating after their initial creation/use.
NOTE: Changes to the formula of autocalculated columns are not recorded as it does not seem to be relevant at the moment

Version 0:
    - NOTE: This version recieved a minor formatting update after the fact
    - Additions
        - Worksheet: Record Stats
            - Unofficial Table Created: these cells are manually parsed since they are not actually a Table Object in the Excel File
            - This "Table" was added after the fact, likely around Version 2
            - Columns:
                - Year
                    - Year of the Season
                - Season
                    - Season Name
                - Version
                    - Version Number of the Record

        - Worksheet: Show Stats
            - Stats Table Created
                - Table Name: "Stats"
                - Columns:
                    - SeriesID
                        - ALDB Series ID
                    - SubseriesID
                        - ALDB Subseries ID
                    - SeasonID
                        - ALDB Season ID
                    - OriginalID
                        - AnimeLife Excel ID
                    - Include
                        - Used for determining output for automation
                        - Was updated as shows were cut from the season
                    - Name
                        - English Series Name
                    - Channel
                        - Channel Abbreviation
                    - Day
                        - Day of the week the show airs in USA
                    - Hashtag
                        - Twitter Hashtag
                    - Last Episode
                        - Last Episode Number from previous AnimeLife Excel Book (if any)
                    - Total Episodes
                        - Total Episodes by the end of the season, including any from previous AnimeLife Excel Book (if any)
                    - Last Normalize
                        - Last Episode's Normalized Total Value from previous AnimeLife Excel Book (if any)
                    - Last Hypelist
                        - Last Episode's Hypelist Count from previous AnimeLife Excel Book (if any)
                - The OriginalID, Last Episode, Total Episodes, Last Normalize, and Last Hypelist columns were likely added later

        - Worksheets: Ranking Sheets (e.g.- Week 1)
            - Ranking Table Created
                - Table Name Format: "Week{Week Number}"
                - The Table's Primary Key (key used to retrieve information from other Tables) is the Name Column
                - Columns:
                    (If not specified, this value was taken from the Show Stats Table)
                    - Channel
                    - Day
                    - Hashtag
                    - Name
                    - Include
                    - OneLiner
                        - Used to indicate whether a OneLiner Reaction Tweet was made for the episode
                    - Video
                        - Used to indicate whether a Video Reaction was made for the episode
                    - Rank
                        - The Episode's Rank for the week
                    - Normalized
                        - The Episode's Normalized Value for the Rank, See Below
                    - Previous Normalized
                        - The Previous Week's Normalized Total Value for the Show
                    - Total Normalized
                        - The sum of Normalized + Previous Normalized
                    - Episodes
                        - A Calculated episode number based on the week and the show's previous episode number
                    - Total Episodes
                        - The Total Episodes for the Show up to the given week
                    - Average
                        - The Average Normalized Value for the Show across the Total Episodes
                    - Previous Average
                        - The Previous Week's Average Normalized Value for the Show
                    - Last Rank
                        - The Show's Previous Overall Ranking based on the Previous Average
                    - New Rank
                        - The Show's Overall Ranking based on the current Average
                    - Rank Change
                        - The Change in Overall Rank from the Previous Week
                    - Hype List Occurences
                        - The Number of Times the Show has appeared on the Hype List (excluding the current week)             

            - Hype List Table Created
                - Starting in Week 3
                - Shows are eligible for the Hype List when after their 2nd Episode
                - Columns:
                    - Last List
                        - The Show's Name at the given rank on the previous week's Hype List
                    - Name
                    - Occurences
                        - The Number of Times the Show has appeared on the Hype List (including the current week)

                        
Version 0.5:
    - NOTE: Spring 2016 was likely originally this version but at the moment only Summer 2016 uses it: see Version 1 Note
    - Addition
        - Worksheet: Ranking Sheet (e.g.- Week 1)
            - Unofficial: The prototype of the Cut Table was created starting in Week 2 through Week 4
                - Not an actual Table Object in the Excel File and does not have a consistent format

Version 1:
    - Originally Spring 2016 was given this version, but the Version Number was completely
        achronological and the Season was later changed to Version 2.5 (See Below)

Version 2:
    - Additions
        - Worksheet: Show Stats
            - Stats Table Additions
                - Columns:
                    - Original Name
                        - The Japanese Name of the Show in Romaji
                    - First Episode
                        - The Date of the First Episode in the USA
                    - Group
                        - Watch Group
                        - Used for creating Weekly Video Reviews
                    - Channel Homepage
                        - The URL for the Show for the Streaming Service noted in Channel
                    - Website
                        - The URL for the Show's Official Website (Preferring the JP version)
                    - PV
                        - The URL for the Show's PV
                    - Showboy ID
                        - The ID for the Show on Showboy
                    - Renewal
                        - Whether or not the Show is a Renewal
                        - This column is used by the Cut Table Settings and to format the Stat Table Row
                    - Notes
                        - Notes for the Show
                        - First used in Version 2

        - Worksheet: Ranking Sheet
            - Ranking Table Additions
                - Columns:
                    - Season Episode
                        - The Number of the Episode in the Season
                    - Total Episodes
                        - A reference back to the Show Stats Table Total Episodes
            
            - Cut Table Created (Weeks 2-3)
                - NOTE: Even though Cut Table is only used in Weeks 2-3, shows are continued to be cut after that
                - Name Format: "Week{Week Number}Cut"
                - Columns:
                    - Name
                    - W1 Rank
                        - The Show's Episode Rank from Week 1
                    - W2 Rank
                        - The Show's Episode Rank from Week 2
                    - W3 Rank (Starting in Week 3)
                        - The Show's Episode Rank from Week 3
                    - T Rank
                        - The Show's Overal Rank for the current Week
                    - Likely Cut
                        - Whether or not the Show is likely to be cut
                        - Calculated based on whether the Show's T Rank is in the bottom 1/4 of the list
                    - Cut
                        - Whether or not the Show is cut (TRUE or MAYBE)
                    - Cut Order
                        - A Randomly generated value to determine the order in which the Shows are announced as cut during the Video Review
            
            - Cut Results Table Created
                - Always accompanies the Cut Table
                - Name Format: "Week{Week Number}CutResults"
                - Columns:
                    - Week 1 Total Shows
                        - The Total Number of Shows in Week 1
                    - Week 2 Total Shows
                        - The Total Number of Shows in Week 2
                    - Week 3 Total Shows (Starting in Week 3)
                        - The Total Number of Shows in Week 3

            - Cut Settings Table Created
                - Always accompanies the Cut Table
                - Name Format: "Week{Week Number}CutSettings"
                - Columns:
                    - Total # of Shows
                        - The Total Number of Shows being watched in the Season
                    - # Keep Shows
                        - The Number of Renewal Shows
                    - Total # Cuttable
                        - The Number of Shows that can be Cut
                    - Target Cut
                        - The Number of shows that should be cut
                    - Cut Average
                        - The average number of Shows to cut each week
                    - # After Cut (Starting in Week 3)
                        - The Number of Shows that will be left after the cut

    - Changes
        - Worksheet: Show Stats
            - Stats Table Changes
                - Columns:
                    - Channel
                        - The Channel name is no longer abbreviated
                    - Day
                        - Now calculated off of the First Episode Date
                    - Episodes
                        - Renamed to Last Episode

Version 2.1:
    - Additions
        - Worksheet: Ranking Sheet
            - Cut Table Settings Additions
                - Columns:
                    - Target Total
                        - The total number of shows to keep
                    - To Cut (Starting in Week 3)
                        - The Remaining number of shows to cut
                
    - Changes
        - Worksheet: Show Stats
            - Stats Table Changes
                - Columns:
                    - Original Name
                        - Can now contain Japanese Characters
                    - Group
                        - Unofficial: By this point the Group column was no longer used
        - Worksheet: Ranking Sheet
            - Cut Table Changes
                - Columns:
                    - Cut
                        - MAYBE is no longer a used value
    
    - Removed
        - Worksheet: Ranking Sheet
            - Cut Table Settings Removed
                - Columns:
                    - # After Cut (Starting in Week 3)
                        - Effectively Replaced by the To Cut Column as it was included to gauge the number of shows remaining to be cut

Version 2.2:
    - Additions
        - Worksheet: Show Stats
            - Stats Table Additions
                - Columns:
                    - Watching
                        - Whether or not the show is being watched
                        - Used to populate information within the sheet
                        - Unlike Include, it is not updated as shows are cut from the season
                    - RSS Feed Name
                        - For Streaming Services that have an RSS Feed, the ID for the Show in the RSS Feed
                    - Image
                        - A list f URLs for the Show's Banner Images
                    - ANN ID
                        - The ID for the Show on Anime News Network
                    - Last Average
                        - A Calculated Average Normalized Value based on Last Episode and Last Normalize
    
    - Changes
        - Worksheet: Ranking Sheet
            - Cut Table
                - Columns:
                    - Cut
                        - Renamed to "Cut?"

    - Removed
        - Worksheet: Ranking Sheet
            - Ranking Table Removed
                - Columns:
                    - Season Episode


Version 2.3:
    - Additions
        - Worksheet: Show Stats
            - Stats Table Additions
                - Columns:
                    - Anilist ID
                        - The ID for the Show on Anilist
                    - MAL ID
                        - The ID for the Show on MyAnimeList
                    - AniDB ID
                        - The ID for the Show on AniDB
    - Removed
        - Worksheet: Ranking Sheet
            - Ranking Table Removed
                - Columns:
                    - Include


Version 2.4
    - Addtions
        - Worksheet: Ranking Sheet
            - Cut Table Settings Additions
                - Columns:
                    - Previous Cut (Starting in Week 3)
                        - The Number of Shows that were previously cut

Version 2.5
    - Additions
        - Worksheet: Show Stats
            - Stats Table Additions
                    - Last Season
                        - The previous season the show aired in formatted "{Season} {Year}"

    - Changes
        - Worksheet: Show Stats
            - Stats Table Changes
                - Columns:
                    - First Episode
                        - May recieve a Datetime
                        
Version 2.6
    - NOTE- The aldb Database stopped being updated in Spring 2018 and therefore only previously
            uploaded series have SeriesID (and potentially SubseriesID and SeasonID)
    - Additions
        - Worksheet: Ranking Sheet
            - Ranking Table Additions
                - Columns:
                    - Date
                        - The Date when the Episode aired in the USA

    - Changes
        - Worksheet: Record Stats
            - Record Stats Table Changes
                - RecordStats is now a Table Object

    - Removed
        - Worksheet: Show Stats
            - Stats Table Removed
                - Columns:
                    - Include

                        
Version 2.7:
    - NOTE: Spring 2016 is the only Record which uses this version and did not originally use it:
        the season was being updated to Version 3 but was not completely converted and therefore
        was given the Version 2.7 designation. Some of the originally formatted Ranking data was
        copied to other cells within each worksheet.
                
Verison 3:
    - NOTE: Contains backwards-incompatible changes to the Ranking Sheet
    - Starting in this version all Show References are made using OriginalID rather than Name

    - Additions
        - Worksheet: Ranking Sheet
            - Ranking Table Additions
                - Columns:
                    - OriginalID
                        - As noted above, now used to populate information within the sheet
                    - Watched
                        - Used to keep track of whether or not the episode has been watched
            - Roundup Table Created (Weeks 1-5)
                - Name Format: "Week{Week Number}Roundup"
                - Is used to rate Series Premiere (First) Episode and used as a metric to determine the Episode's Rank
                - Animation, Art/Aesthetics, Character/Story Investment, and Plot/World Building are rated on a scale of 1.0-5.0
                - Columns:
                    - OriginalID
                    - Name
                    - Animation
                    - Art/Aesthetics
                    - Character/Story Investment
                    - Plot/World Building
                    - Average
                        - The average score of the 4 categories
                    - Rank
                        - The calculated rank of the episode based on the average score

    - Changes
        - Worksheet: Show Stats
            - Stats Table Changes
                - Columns:
                    - Minor Change: The columns were rearranged so Renewal comes before Watching: Renewal Shows that were previously marked are automatically marked as FALSE on Watching

    - Removed
        - Worksheet: Ranking Sheet
            - Ranking Table Removed
                - Columns:
                    - OneLiner
    

Version 3.1:
    - Additions
        - Worksheet: Record Stats
            - Record Stats Table Additions
                - Columns:
                    - Target Shows
                        - Used to set the Target Total for the Cut Table Settings
        - Worksheet: Ranking Sheet
            - Renewal Roundup Table Created (Week 1 plus any week with a Renewal)
                - Name Format: "Week{Week Number}RenewalRoundup"
                - Is used to rate a Renewal Series First Episode and used as a metric to determine the Episode's Rank
                - Recap/Reintroduction, Setup, and Animation are rated on a scale of 1.0-5.0
                - Columns:
                    - OriginalID
                    - Name
                    - Recap/Reintroduction
                    - Setup
                    - Animation
                    - Average
                        - The average score of the 3 categories
                    - Rank
                        - The calculated rank of the episode based on the average score
    
    - Changes
        - Worksheet: Ranking Sheet
            - Cut Table (and Accompanying Tables) Changes
                - Now appear in week 4 (updated as necessary)
            - Cut Table Settings Changes
                - Columns:
                    - Target Total
                        - Now set by the Target Shows column in Record Stats

Version 4:

    - Additions
        - Worksheet: Ranking Sheet
            - Hype List Table Additions
                - Columns:
                    - OriginalID
                        - Even after Version 3 was created the Hype List was still using Name as the Primary Key

            - Last Week's Hype List Table Created
                - Table Name Format: "Hype_Week{Week Number}_PreviousWeek"
                - This table was created because having the current Hype List and the Previous Week's Hype List
                    on the same list resulted in unnecessarily long lists.
                - This also makes it easier to compare shows on the previous Hype List to their current Episode Rank
                    to see whether the Episode met expectations
                - Columns:
                    - OriginalID
                    - Name
                    - This Week's Rank

            - Roundup Table Additions
                - Columns:
                    - Percent
                        - Score Percentage

    - Removed
        - Worksheet: Ranking Sheet
            - Hype List Table Removed
                - Columns:
                    - Last List
                        - This column was replaced by the Last Week's Hype List Table

Version 4.1
    - Additions
        - Worksheet: Ranking Sheet
            - Ranking Table Additions
                - Columns:
                    - Episode Number
                        - The Episode Number for the Episode
                        - This was added allow for a Show to have more than one episode per week


Version 4.2
    - Changes
        - Worksheet: Ranking Sheet
            - Ranking Table Changes
                - Columns:
                    - Episode Number
                        - No longer uses a formula Week 1

                        
Version 4.3
    - NOTE: Starting in Spring 2021, Watched began being used to indicate Finales using the value "F"
    - Additions
        - Worksheet: Anime Awards
            - Anime Awards Table Created
                - Table Name: AnimeAwards
                - Anime awards are random awards given out on a whim
                - Columns:
                    - Award
                        - Title of the Award
                    - OriginalID
                    - Name
                        - The Anime that won the Award

Version 5
    - NOTE: Summer 2020 is the only Record which uses this version; Fall 2020 reverts to Version 4.3. It is
            unclear if Workbooks started to be updated to what is now Version 5.1 (starting with Summer 2020)
            and the transition was not completed.
    - Additions
        - Worksheet: Weekly Ranking
            - Weekly Ranking Table Created
                - Table Name: "ChartData_WeeklyRanking"
                - This table was initially implemented to give an overview of each show's Episode Rank over the course of the season
                - Columns:
                    - OriginalID
                    - Show Name
                    - Week {Week Number}
                        - Each week 1-14 has a column

Version 5.1
    - Additions
        - Worksheet: Weekly Ranking
            - Weekly Overall Ranking Table Created
                - Table Name: "ChartData_WeeklyOverallRanking"
                - This table gathers the overall Rank for each show into a Table so it can be shown on the Weekly Rank Chart
                - Columns:
                    - OriginalID
                    - Name
                    - Week {Week Number}
                        - Each week 1-14 has a column
        - Worksheet: Weekly Rank Chart
            - This is a Chart Sheet, which is a special type of Worksheet that only contains a Chart
            - This chart plots the Weekly Ranking Table
        - Worksheet: Weekly Overall Rank Chart
            - This is a Chart Sheet, which is a special type of Worksheet that only contains a Chart
            - This chart plots the Weekly Overall Ranking Table

    - Changes
        - Worksheet: Weekly Ranking
            - Weekly Ranking Table Changes
                - Columns:
                    - Show Name
                        - Renamed to Name
                    - Week {Week Number}
                        - Changed to use the Normalized Value rather than the Rank

Version 5.2
    - Changes
        - Worksheet: Ranking Sheet
            - Cut Table (and Accompanying Tables) Changes
                - Now appear in all Weeks 2-6
                - Cut Table Settings updated to include all weeks up to the current week
            - Renewal Roundup Table Changes
                - Now only appears in Weeks 1-3

Version 5.3
    - Additions
        - Worksheet: Show Stats
            - Stats Table Additions
                - Columns:
                    - TikTok
                        - The TikTok URL for the Show
    - Removed
        - Worksheet: Show Stats
            - Stats Table Removed
                - Columns:
                    - RSS Feed Name
        - Worksheet: Ranking Sheet
            - Ranking Table Removed
                - Columns:
                    - Video
---

Normalized Value:
    Normalized value has been calculated the same for all versions of the Record.
    The range of ranks are normalized between 0 and 1, with 0 being the lowest rank (Best Rank) and 1 being the highest rank (Worst Rank).
        Excel Formula: "=IF(ISBLANK([@Rank]),NA(),0+(([@Rank]-MIN([Rank]))*(1-0))/(MAX([Rank])-MIN([Rank])))"
        Available under RankingSheet.getepisodenormalize(episode)
"""

ShowName = str
ShowOriginalID = int
ShowSeasonID = int
ShowSubseriesID = int
ShowSeriesID = int
ShowIdentifier = typing.Union[ShowName,ShowOriginalID,ShowSeasonID,ShowSubseriesID,ShowSeriesID]

## EnhancedTable.todicts() keyfactory for converting Headers to attribute names
keyfactory = lambda key: key.lower().replace(" ","")

WBNAME = '''^(?:(?!~\$).)*?(?P<season>[a-zA-Z]+)\s*(?P<year>\d+)'''
WBNAMERE=re.compile(WBNAME)
## WBNAME[1:] -> Remove start-of-line marker
FILENAMERE = re.compile(f"""^__Record\s+{WBNAME[1:]}\s*.xlsx?""",re.IGNORECASE)
## WEEKRE is currently used on tables (which cannot have spaces) but accepts spaces for use with Workbook names
WEEKRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)\s*$""", re.IGNORECASE)
## See WEEKRE note
HYPERE = re.compile("""^Hype(?:\s|_)*Week(?:\s|_)*(?P<number>\d+)""", re.IGNORECASE)

HYPEHISTRE = re.compile("""^Hype_Week(?P<number>\d+)_PreviousWeek\s*$""", re.IGNORECASE)
ROUNDUPRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)Roundup\s*$""", re.IGNORECASE)
ROUNDUPRENEWALRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)RenewalRoundup\s*$""", re.IGNORECASE)
CUTRE = re.compile("""^Week(?:\s|_)*(?P<number>\d+)Cut(?P<type>Settings|Results)?\s*$""", re.IGNORECASE)

CHARTDATARE = re.compile("""^Chart\s*Data_(?P<type>WeeklyRanking|WeeklyOverallRanking)\s*$""", re.IGNORECASE)
ANIMEAWARDS = re.compile("""^AnimeAwards\s*$""", re.IGNORECASE)


def listvalidfilenames(dire: str|pathlib.Path, recurse:bool=False)->typing.Generator[pathlib.Path,None, None]:
    """ A generator that yields all the validly named Record files (as pathlib.Path instances; does not garauntee that the files are correctly formatted)
    
        Args:
            dire: The directory to search for Record files
            recurse: If True, recursively search the directory for Record files. If False, only search the given directory.
    """
    dire = pathlib.Path(dire).resolve()
    if not dire.exists() or not dire.is_dir():
        raise ValueError("Invalid directory: must be a directory and must exist")
    yield from filemodules.iterdir_re(dire,FILENAMERE, recurse=recurse)

def isvalidfilename(filename: str)->bool:
    """ Returns True if the filename is a valid Record filename (does not garauntee that the file is correctly formatted)

        Args:
            filename: The filename to check
    """
    return bool(FILENAMERE.match(str(filename)))

def extractseasonfromfilename(filename:str)->anime.AnimeSeason:
    """ Returns the AnimeSeason object for the season and year in the filename (if any)

        Args:
            filename: The filename to parse
    """
    res=WBNAMERE.search(str(filename))
    if res:
        season,year=res.group('season'),res.group('year')
        out=""
        if season:
            out+=season+" "
        if year: out+=year
        return anime.parseanimeseason_toobject(out)
    raise ValueError("Invalid filename: does not contain a season and year")

class SeasonRecord():
    @staticmethod
    def load_directory(dire: str|pathlib.Path, recurse:bool=False)->typing.Generator["SeasonRecord",None, None]:
        """ A generator that yields all the validly formatted Record files (as SeasonRecord instances)

            Args:
                dire: The directory to search for Record files
                recurse: If True, recursively search the directory for Record files. If False, only search the given directory.
        """
        for file in listvalidfilenames(dire,recurse):
            yield SeasonRecord(file)

    def __init__(self,file:pathlib.Path, data_only=True):
        self._file=file
        xlsx=self.xlsx=AL_Excel.load_workbook(filename=str(file),data_only=data_only)
        self._sheets={sheet:xlsx[sheet] for sheet in xlsx.sheetnames}
        tables = Tables.get_all_tables(xlsx)
        tables = {table.displayName:table for (ws,table) in tables}
        try:
            table = tables.pop('RecordStats')
        except KeyError:
            table = RecordStats.parsesheet(self._sheets['Record Stats'])
        self._recordstats: RecordStats = RecordStats(table,self)
        self._recordstatssheet = table.worksheet
        if self.recordstats.version >= 3.1:
            self._recordstats = RecordStatsV3_1(table,self)
        
        table = tables.pop('Stats')
        # except KeyError:
        #     table = ShowStats.parsesheet(self._sheets['Show Stats'])
        if self.recordstats.version < 3:
            idvalue = ExcelShowStats.NAMEVALUE
        else: idvalue = ExcelShowStats.ORIGINALIDVALUE
        self._showstats: ShowStats = ExcelShowStats(table = table, record = self, idvalue = idvalue)
        self._showstatssheet = table.worksheet
                
        self._weeks: typing.Dict[int, RankingSheet]={}
        weektables: typing.Dict[int, Tables.EnhancedTable] = {}
        hypetables: typing.Dict[int, Tables.EnhancedTable] = {}
        cuttables: typing.Dict[int, Tables.EnhancedTable] = {}
        rounduptables: typing.Dict[int, Tables.EnhancedTable] = {}
        rounduprenewaltables: typing.Dict[int, Tables.EnhancedTable] = {}
        historytables: typing.Dict[int, Tables.EnhancedTable] = {}
        
        for name,table in tables.items():
            if (ws := WEEKRE.search(name)):
                weektables[int(ws.group("number"))]=table
            elif (hs := HYPERE.search(name)):
                hypetables[int(hs.group("number"))]=table
            elif (cs:=CUTRE.search(name)) and not cs.group("type"):
                cuttables[int(cs.group("number"))]=table
            ## Cut Settings and Cut Results are not currently parsed
            ## Cut Results could be calculated without parsing and Cut Settings
            ## will only need to be retrieved once for the whole season
            elif (cs:=CUTRE.search(name)) and cs.group("type"): pass
            elif (rs := ROUNDUPRE.search(name)):
                rounduptables[int(rs.group("number"))]=table
            elif (rus := ROUNDUPRENEWALRE.search(name)):
                rounduprenewaltables[int(rus.group("number"))]=table
            elif (hhs := HYPEHISTRE.search(name)):
                historytables[int(hhs.group("number"))]=table
            ## Chart Data is not currently parsed as it can be calculated without parsing
            elif CHARTDATARE.match(name): pass
            ## TODO: Anime Awards is not currently parsed
            elif ANIMEAWARDS.match(name): pass
            else:
                warnings.warn(f'Unknown Table: "{name}"')

        for week,table in weektables.items():
            hypetable = hypetables.get(week)
            cuttable = cuttables.get(week)
            rounduptable = rounduptables.get(week)
            rounduprenewaltable = rounduptables.get(week)
            version = self.recordstats.version
            if version >= 4:
                s = RankingSheetV4(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self, historytables.get(week))
            elif version >= 3.1:
                s = RankingSheetV3_1(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self)
            elif version >= 3:
                s = RankingSheetV3(table, hypetable, cuttable, rounduptable, self)
            else:
                s = RankingSheetV1(table, hypetable, self)
            s.setshowstats(self.showstats.shows)
            self._weeks[week]=s
    @property
    def file(self)->pathlib.Path:
        return self._file
    @property
    def sheets(self):
        return self._sheets
    @property
    def weeks(self)->typing.Dict[int,"RankingSheetVersions"]:
        return self._weeks
    def week(self,weeknumber: int)->"RankingSheetVersions":
        """ Returns the RankingSheet for the given week number """
        return self.weeks[weeknumber]
    @property
    def recordstatssheet(self)->Worksheet:
        return self._recordstatssheet
    @property
    def recordstats(self)->"RecordStats":
        return self._recordstats
    @property
    def showstatssheet(self)->Worksheet:
        return self._showstatssheet
    @property
    def showstats(self)->"ShowStats":
        return self._showstats
    @property
    def animeseason(self)->anime.AnimeSeason:
        return self.recordstats.animeseason

    def close(self):
        self.xlsx.close()

    def getlastweek(self)->"RankingSheet":
        weeks = [week for week in self.weeks.values() if week.shows]
        weeks.sort(key=lambda week: week.weeknumber, reverse=True)
        return weeks[0]

    def compileshows(self)->dict:
        """ Returns all shows as a series of dicts { showname: {Stats: ShowStatsObject, Weeks: [ EpisodeObjects ]}} """
        lookup = {showname:{"Stats":stats,"Weeks":[]} for showname,stats in self.showstats.shows.items()}
        for rankingsheet in self.weeks.values():
            rankedshows = rankingsheet.getepisoderanking()
            for showepisode in rankedshows:
                _id = showepisode.originalid
                if _id is None:
                    _id = self.showstats.getshowbyname(showepisode.name).originalid
                lookup[_id]['Weeks'].append(showepisode)
        return lookup
    
    def __eq__(self,other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex == other.recordstats.seasonindex
    
    def __lt__(self, other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex < other.recordstats.seasonindex
    
    def __gt__(self, other):
        if not isinstance(other,SeasonRecord):
            return False
        return self.recordstats.seasonindex > other.recordstats.seasonindex
    
    def __repr__(self):
        return str(f"Season Record<{self.file.name}> {self.animeseason} {self.recordstats.version}")

class RecordStats():
    
    @staticmethod
    def parsesheet(sheet: Worksheet)-> EnhancedTable:
        column = 1
        row = 1
        tableref = Tables.gettablesize(sheet,startcolumn = column, startrow = row)
        table = AL_Excel.EnhancedTable(worksheet = sheet, displayName = "RecordStats", ref = tableref)
        return table
    
    def __init__(self,table: Tables.EnhancedTable, record: SeasonRecord):
        self._table = table
        self._record = record
        ## todicts returns keys() at index 1 (also note that this should also only 
        ## return 1 actual row if the RecordStats is properly formatted)
        self.stats: typing.Dict[str, typing.Any] = {key.lower():v for key,v in self.table.todicts()[1].items()}
        

    @property
    def season(self)->str:
        if "season" in self.stats and self.stats['season']:
            return self.stats['season']
        return extractseasonfromfilename(str(self.record.file)).season
    @property
    def year(self)->int:
        if "year" in self.stats and self.stats['year']:
            return self.stats['year']
        return extractseasonfromfilename(str(self.record.file)).year

    @property
    def version(self)->float:
        return float(self.stats['version'])

    @property
    def animeseason(self)->anime.AnimeSeason:
        return anime.AnimeSeason(self.season,self.year)
        
    @property
    def seasonindex(self)->float:
        if "seasonindex" in self.stats and self.stats['seasonindex']:
            return self.stats['seasonindex']
        return self.animeseason.seasonindex
        

    @property
    def table(self)->Tables.EnhancedTable:
        return self._table
    @property
    def record(self)->SeasonRecord:
        return self._record
    
class RecordStatsV3_1(RecordStats):
    def __init__(self,table: Tables.EnhancedTable, record: SeasonRecord):
        super().__init__(table,record)

    @property
    def targetshows(self)->int:
        return int(self.stats['targetshows'])

class ShowStats():
    SHOWIDVALUE = "SeriesID"
    ONAMEVALUE = "Original Name"
    NAMEVALUE = "Name"
    ORIGINALIDVALUE = "OriginalID"
    def __init__(self, shows:typing.Sequence[dict], idvalue:str):
        self._shows = {show[idvalue.lower()]:Show(self,**show) for show in shows if show[idvalue.lower()]}
        self.idvalue = idvalue

    @property
    def shows(self)->typing.Dict[ShowIdentifier,"Show"]:
        return self._shows

    def getshowbyname(self, show: str)-> "Show":
        """ Returns the Show Object for a show of the given name string.

        Returns the Show Object if name is in shows, else None.
        If more than one string is passed (positional args), returns a List of results (per this method).
        """
        if not isinstance(show,str):
            raise ValueError("Arguements to getshowbyname must be strings")
        shows = [s for s in self.shows.values() if (s.originalname and s.originalname.lower() == show.lower()) or (s.name and s.name.lower() == show.lower())]
        if shows:
            return shows[0]
        raise ValueError(f"Show '{show}' not found in ShowStats")

class MasterShowStats(ShowStats):
    MASTERIDVALUE = "originalid"
    @staticmethod
    def load_masterstats(csvfile):
        """ Function for loading Stats from Master csv File (Rather than standard Excel Record) """
        with open(csvfile,'r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return MasterShowStats(shows = list(reader), idvalue = MasterShowStats.MASTERIDVALUE)
    
    def __init__(self, shows: list[dict], idvalue: str):
        super().__init__(shows, idvalue)


class ExcelShowStats(ShowStats):
    def __init__(self, table: Tables.EnhancedTable, record: SeasonRecord, idvalue: str):
        self._table = table
        self.record = record
        shows = table.todicts(keyfactory = keyfactory)
        ## Remove headers
        headers = shows.pop(0)
        super().__init__(shows, idvalue= idvalue)

    @property
    def table(self)->Tables.EnhancedTable:
        return self._table

class Show():
    def __init__(self,statssheet: ShowStats, originalid: int, seasonid: typing.Optional[int] = None, seriesid: typing.Optional[int] = None, subseriesid: typing.Optional[int] = None,
                 watching: typing.Optional[bool] = None, include: typing.Optional[bool] = None, originalname: typing.Optional[str] = None, name: typing.Optional[str] = None, channel: typing.Optional[str] = None,
                 day: typing.Optional[str] = None, firstepisode: str|datetime.datetime|None = None, group: typing.Optional[int] = None, channelhomepage: typing.Optional[str] = None, image: typing.Optional[str] = None,
                 rssfeedname: typing.Optional[str] = None, hashtag: typing.Optional[str] = None, website: typing.Optional[str] = None, pv: typing.Optional[str] = None,
                 showboyid: typing.Optional[str] = None, annid: typing.Optional[str] = None,anilistid: typing.Optional[str] = None, malid: typing.Optional[str] = None, anidbid: typing.Optional[str] = None,
                 renewal: typing.Optional[bool] = None, lastepisode: typing.Optional[int] = None, totalepisodes: typing.Optional[int] = None, lastnormalize: typing.Optional[float] = None, lastaverage: typing.Optional[float] = None,
                 lasthypelist: typing.Optional[int] = None, notes: typing.Optional[str] = None, lastseason: typing.Optional[str] = None, **kw):
        self.statssheet = statssheet
        self.originalid = originalid

        self.kw = kw
        if kw:
            extras = ", ".join(kw.keys())
            try: warnings.warn(f"Show received additional Keywords: {extras}",UserWarning)
            except: pass
        self.seasonid = seasonid
        self.seriesid = seriesid
        self.subseriesid = subseriesid
        if not watching: watching = False
        if not include: include = False
        self.watching = bool(watching)
        self.include = bool(include)
        self.originalname = originalname
        self.name = name
        self.channel = channel
        self.day  = day
        self.firstepisode = firstepisode
        if group: group = int(group)
        self.group = group
        self.channelhomepage = channelhomepage
        self.rssfeedname = rssfeedname
        self.hashtag = hashtag
        self.website = website
        self.pv = pv
        self.showboyid = showboyid
        self.annid = annid
        self.anilistid = anilistid
        self.malid = malid
        self.anidbid = anidbid
        self.image = None
        if not renewal: renewal = False
        self.renewal = bool(renewal)
        if not lastepisode: lastepisode = 0
        self.lastepisode = int(lastepisode)
        if not totalepisodes: totalepisodes = -1
        self.totalepisodes = int(totalepisodes)
        if not lastnormalize: lastnormalize = 0
        self.lastnormalize = float(lastnormalize)
        if not lasthypelist: lasthypelist = 0
        self.lasthypelist = int(lasthypelist)
        self.lastseason = lastseason

        self.notes = notes

        self.episodeurls=dict()
        self.seasonorder=list()

    @property
    def lastaverage(self)-> float:
        if not self.lastepisode: return 0.0
        return self.lastnormalize / self.lastepisode

    def to_dict(self)->dict:
        return dict(originalid = self.originalid, seasonid = self.seasonid, seriesid = self.seriesid, subseriesid = self.subseriesid,
                    watching = self.watching, include = self.include, originalname = self.originalname, name = self.name, channel = self.channel,
                 day = self.day, firstepisode = self.firstepisode, group = self.group, channelhomepage = self.channelhomepage, image = self.image,
                 rssfeedname = self.rssfeedname, hashtag = self.hashtag, website = self.website, pv = self.pv,
                 showboyid = self.showboyid,annid = self.annid,anilistid = self.anilistid, malid = self.malid, anidbid = self.anidbid,
                 renewal = self.renewal, lastepisode = self.lastepisode, totalepisodes = self.totalepisodes, lastnormalize = self.lastnormalize, lastaverage = self.lastaverage,
                 lasthypelist = self.lasthypelist, notes = self.notes, lastseason = self.lastseason)

    def __repr__(self):
        return str(self)
    def __str__(self):
        return f"Season Show: {self.name}"

class HypeList():
    NAMEHEADER = "name"
    LASTHEADER = "lastlist"
    def __init__(self,table: Tables.EnhancedTable, week: "RankingSheet"):
        self._table = table
        self.week = week

    @property
    def rows(self):
        ## First index is keys()
        return self.table.todicts(keyfactory = keyfactory)[1:]

    @property
    def table(self)->Tables.EnhancedTable:
        return self._table
    
    def rank(self, show: "Episode|ShowName")-> int|None:
        raise NotImplementedError("rank() must be implemented by subclasses")

class HypeListV1(HypeList):
    """ HypeListV1:

        Used for Spreadsheet version prior to Version 4.

        Format:
            Last List           | Name              | Occurences
            -----------------------------------------------------
            Prev. Week Rank 1   | Curr. Week Rank 1 | Number of Prev. Occurences of Curr. Week Rank 1
            Prev. Week Rank 2   | Curr. Week Rank 2 | Number of Prev. Occurences of Curr. Week Rank 2
            ... etc

        When the table is read as a dict (using AL_Excel.EnhancedTable.todicts()),the result is:
        [   ["Last List", "Name", "Occurences"], ## Table Keys
            {"Last List": "Prev. Week Rank 1", "Name": "Curr. Week Rank 1", "Occurences": "Number of Prev. Occurences of Curr. Week Rank 1"},
            {"Last List": "Prev. Week Rank 2", "Name": "Curr. Week Rank 2", "Occurences": "Number of Prev. Occurences of Curr. Week Rank 2"},
            ... etc
            ]

        Current Hypelist is therefore row comprehension for "Name" where the value is not Blank (None)
        Previous Hypelist is likewise row comprehension for "Last List" where the value is not Blank (None)
    """
    def __init__(self, table: Tables.EnhancedTable, week: "RankingSheet"):
        super().__init__(table, week)

    @property
    def hypelist(self)->typing.List[str]:
        return[row[self.NAMEHEADER] for row in self.rows if row[self.NAMEHEADER]]
        
    @property
    def history(self)->typing.List[str]:
        return [row[self.LASTHEADER] for row in self.rows if row[self.LASTHEADER]]

    def rank(self,show: "Episode|ShowName")-> int|None:
        """ Returns the Rank on the current HypeList of the given show (None if the show is not on the hypelist) """
        if isinstance(show,Episode):
            show = show.name
        if show in self.hypelist: return self.hypelist.index(show)+1
        return None

class HypeListv4(HypeList):
    """ HypelistV4:

        Used for Spreadsheet Version 4 (current version). In this version, Hypelist and Hypelist
            History are split between two tables.

        Hypelist Format:
            OriginalID  | Name          | Occurences
            -------------------------------------------------------------------
            Rank 1 OID  | Rank 1 Name   | Number of Prev. Occurences of Rank 1
            Rank 2 OID  | Rank 2 Name   | Number of Prev. Occurences of Rank 2
            ... etc

        Hyplist History Format:
            OriginalID              | Name                      | This Week's Rank
            ----------------------------------------------------------------------------------------
            Prev. Week Rank 1 OID   | Prev. Week Rank 1 Name    | Episode Rank of Prev. Week Rank 1
            Prev. Week Rank 2 OID   | Prev. Week Rank 2 Name    | Episode Rank of Prev. Week Rank 2
            ... etc

        
    """
    OIDHEADER = "originalid"
    NAMEHEADER = "name" 
    LASTHEADER = None

    def __init__(self, table: Tables.EnhancedTable, week: "RankingSheet", historytable: Tables.EnhancedTable|None):
        super().__init__(table, week)
        self._historytable = historytable

    @property
    def hypelist(self):
        return self.rows

    @property
    def history(self):
        if self._historytable:
            return self._historytable.todicts(keyfactory = keyfactory)[1:]
        return []

    def rank(self, show: "Episode|ShowOriginalID|ShowName")-> int|None:
        if isinstance(show, Episode):
            show = int(show.originalid)
        if isinstance(show, int):
            show = str(show)
            header = self.OIDHEADER
        elif isinstance(show, str):
            header = self.NAMEHEADER
        for i,row in enumerate(self.hypelist, start=1):
            if row[header]==show:
                return i
        return None

EpisodeDict = typing.Dict[str|int, "Episode"]


class RankingSheet():
    RANKHEADER="rank"
    NEWRANKHEADER="newrank"
    EPISODEHEADER="episodes"
    HYPEOCCURENCEHEADER="hypelistoccurences"
    WEEKRE=re.compile('''.*week\s*(?P<week>\d+)''',re.IGNORECASE)
    HYPELIST: typing.Type[HypeList] = HypeListV1

    @staticmethod
    def getheaderindex(columns,header):
            if isinstance(header,list):
                header=[head for head in header if head in columns]
                if not header: return None
                header=min(header,key=lambda head: columns.index(head.lower()))
            if isinstance(header,str):
                if header.lower() not in columns: return None
                return columns.index(header.lower())+1
            return None

    def __init__(self,table: Tables.EnhancedTable, hypelist: typing.Optional[Tables.EnhancedTable], record: SeasonRecord):
        self._table = table
        self._record = record
        ws = WEEKRE.search(table.displayName)
        if not ws: raise ValueError(f"Invalid Worksheet Name: does not contain a week number: {table.displayName}")
        self.weeknumber=int(ws.group("number"))
        self.hypelist: HypeList|None = None
        if hypelist and self.hypelist: self.hypelist = self.HYPELIST(hypelist,self)

        self.shows: EpisodeDict = dict()
        ## Index-0 of todicts is keys()
        shows = self.table.todicts(keyfactory = keyfactory)[1:]
        for show in shows:
            originalid = show.get("originalid",None)
            seasonid = show.get("seasonid",None)
            name = show['name']
            ## For old records
            if not originalid and not seasonid:
                ## Getting showstats preemptively
                showstat = None
                if name:
                    showstat = self.record.showstats.getshowbyname(name)
                ## Check for old alias first
                originalid = show.get("seriesid",None)
                ## Fill in if necessary/possible
                if showstat:
                    if not originalid:
                        originalid = showstat.originalid
                    if not seasonid:
                        seasonid = showstat.seasonid

            
            rank = show[self.RANKHEADER]

            ranktotal = show[self.NEWRANKHEADER]
            episode = show[self.EPISODEHEADER]
            hypelistocc = show[self.HYPEOCCURENCEHEADER]
            if name:
                show = Episode(originalid=originalid,seasonid = seasonid, name=name,week=self,
                                         rank=rank,ranktotal=ranktotal,episode=episode,
                                         hypelistocc=hypelistocc)
                self.shows[name] = show

    @property
    def table(self):
        return self._table
    @property
    def record(self):
        return self._record

    def setshowstats(self,showstats: typing.Dict[str|int, "Show"]):
        for show,stats in showstats.items():
            if isinstance(show,int):
                show = stats.name
            if show in self.shows:
                thisshow = self.shows[show]
                thisshow.showstats = stats
                if thisshow.originalid is None:
                    thisshow.originalid = stats.originalid

    def getepisoderanking(self) -> typing.List["Episode"]:
        rankings=[show for show in self.shows.values() if show.rank is not None]
        return sorted(sorted(rankings,key=lambda show:show.name),key=lambda show: show.rank)
    
    def getseasonranking(self) -> typing.List["Episode"]:
        rankings=[show for show in self.shows.values() if show.ranktotal is not None]
        return sorted(sorted(rankings,key=lambda show:show.name),key=lambda show: show.ranktotal)
    
    def gethypelistranking(self) -> typing.List["Episode"]:
        rankings=[show for show in self.shows.values() if show.hypelistrank is not None]
        rankings.sort(key=lambda show:show.name)
        rankings.sort(key=lambda show: show.hypelistrank if show.hypelistrank else 10000)
        return rankings
    
    
    def getepisodenormalize(self,episode: "Episode")-> float:
        """ Returns the normalized value for the show's Ranking. """
        rankings = self.getepisoderanking()
        minrank = min(rankings, key = lambda ranking: ranking.rank).rank
        maxrank = max(rankings, key = lambda ranking: ranking.rank).rank
        BASE,CEIL = 0,1
        return BASE + ( (episode.rank - minrank) * (CEIL - BASE) ) / ( maxrank - minrank)

class RankingSheetV1(RankingSheet):
    """ Ranking Sheet for Record Versions prior to 4"""
    HYPELIST = HypeListV1
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, record: SeasonRecord):
        super().__init__(table, hypelist, record)

class RankingSheetV3(RankingSheetV1):
    HYPELIST = HypeListV1
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, cuttable: Tables.EnhancedTable|None,
                 rounduptable: Tables.EnhancedTable|None, record: SeasonRecord):
        super().__init__(table, hypelist, record)
        self.cuttable = cuttable
        self.rounduptable = rounduptable

class RankingSheetV3_1(RankingSheetV3):
    HYPELIST = HypeListV1
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, cuttable: Tables.EnhancedTable|None,
                 rounduptable: Tables.EnhancedTable|None, rounduprenewaltable: Tables.EnhancedTable|None,
                 record: SeasonRecord):
        super().__init__(table, hypelist, cuttable, rounduptable, record)
        self.rounduprenewaltable = rounduprenewaltable

class RankingSheetV4(RankingSheetV3_1):
    """ Ranking Sheet for Record Version 4 (current version) """
    HYPELIST: typing.Type[HypeListv4] = HypeListv4
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None,
                 cuttable: Tables.EnhancedTable|None, rounduptable: Tables.EnhancedTable|None,
                 rounduprenewaltable: Tables.EnhancedTable|None, record: SeasonRecord, hypehistory: Tables.EnhancedTable|None = None):
        ## Do not pass hypehistory to super().__init__ since it has a different instantiation signature
        super().__init__(table, None, cuttable, rounduptable, rounduprenewaltable, record)
        if hypelist:
            self.hypelist = RankingSheetV4.HYPELIST(hypelist, self, hypehistory)

RankingSheetVersions = RankingSheet|RankingSheetV1|RankingSheetV3|RankingSheetV3_1|RankingSheetV4

class Episode():
    def __init__(self, originalid: int, name: str, week:RankingSheet, rank: int, ranktotal: int,
                 episode: int, hypelistocc:typing.Optional[int]=0, seasonid: typing.Optional[int] = None,
                 showstats: Show|None = None):
        self.originalid = originalid
        self.seasonid = seasonid
        self.name=name
        self.week = week
        self.rank=rank
        self.ranktotal=ranktotal
        self.episodenumber=episode
        self.hypelistocc=hypelistocc
        self.showstats = showstats

    @property
    def hypelistrank(self):
        if self.week.hypelist:
            return self.week.hypelist.rank(self)

    @property
    def normalizedrank(self):
        return self.week.getepisodenormalize(self)

    def to_dict(self):
        return dict(originalid = self.originalid, name = self.name, week = self.week, rank = self.rank, ranktotal = self.ranktotal, episodenumber = self.episodenumber, hypelistocc = self.hypelistocc, hypelistrank = self.hypelistrank)

    def __repr__(self):
        return f"Episode {self.name}:{self.episodenumber}"
    
class FirstEpisodeRatingTable():
    pass