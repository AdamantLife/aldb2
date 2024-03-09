""" aldb2.RecordReader.master

    This module is used to parse AnimeLife Excel Records
"""

## Builtin
import collections
import datetime
import pathlib
import re
import warnings
import typing

## This Module
from aldb2.Anime import anime
from aldb2.RecordReader.classes import SeasonRecord, RecordStats, ShowStats, ShowBase, ShowIdentifier, RankingSheet, Episode, ShowLookup, EpisodeDict, RecordStatsDict, WeekLookup

## Custom Module
import AL_Excel ## Extension of openpyxl
from AL_Excel import Tables, EnhancedTable
import AL_Filemodules as filemodules
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import Cell

"""
Excel Sheet Version History:

NOTE: For early version (Version < 3) Workbooks (and their associated versions) had some degree of undocumented updating after their initial creation/use.
NOTE: Changes to the formula used in autocalculated columns are not recorded as it does not seem to be relevant at the moment

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

## DEV NOTE: Various Excel subclasses parse their sheets based on previously parsed classes, but everything is parsed within
##           ExcelSeasonRecord. This means that the higher classes are not initialized before the lower classes are parsed.
##           To avoid passing around more arguments than are necessary, the higher classes are initialized with empty values
##           for the lower classes that are parsed later; the lower classes are then added to the higher classes after they
##           are finished parsing.

## EnhancedTable.todicts() keyfactory for converting Headers to attribute names
DEFAULTKEYFACTORY = lambda key: key.lower().replace(" ","")

WBNAME = r'''^(?:(?!~\$).)*?(?P<season>[a-zA-Z]+)\s*(?P<year>\d+)'''
WBNAMERE=re.compile(WBNAME)
## WBNAME[1:] -> Remove start-of-line marker
FILENAMERE = re.compile(fr"""^__Record\s+{WBNAME[1:]}\s*.xlsx?""",re.IGNORECASE)
## WEEKRE is currently used on tables (which cannot have spaces) but accepts spaces for use with Workbook names
WEEKRE = re.compile(r"""^Week(?:\s|_)*(?P<number>\d+)\s*$""", re.IGNORECASE)
## See WEEKRE note
HYPERE = re.compile(r"""^Hype(?:\s|_)*Week(?:\s|_)*(?P<number>\d+)""", re.IGNORECASE)

HYPEHISTRE = re.compile(r"""^Hype_Week(?P<number>\d+)_PreviousWeek\s*$""", re.IGNORECASE)
ROUNDUPRE = re.compile(r"""^Week(?:\s|_)*(?P<number>\d+)Roundup\s*$""", re.IGNORECASE)
ROUNDUPRENEWALRE = re.compile(r"""^Week(?:\s|_)*(?P<number>\d+)RenewalRoundup\s*$""", re.IGNORECASE)
CUTRE = re.compile(r"""^Week(?:\s|_)*(?P<number>\d+)Cut(?P<type>Settings|Results)?\s*$""", re.IGNORECASE)

CHARTDATARE = re.compile(r"""^Chart\s*Data_(?P<type>WeeklyRanking|WeeklyOverallRanking)\s*$""", re.IGNORECASE)
ANIMEAWARDS = re.compile(r"""^AnimeAwards\s*$""", re.IGNORECASE)

class CellClass:
    """ A class that allows for attribute access to a Cell object.
    
        Instance attributes which are prepended with "cell_" are assumed to be Cell objects. The Cell's value can
        be accessed and set using the attribute name without the underscore.
    """
    PREPEND = "cell_"
    def __getattribute__(self, __name: str) -> typing.Any:
        prepend = CellClass.PREPEND+__name
        try:
            return super().__getattribute__(prepend).value
        except:
            return super().__getattribute__(__name)
    def __setattr__(self, __name: str, __value: typing.Any) -> None:
        prepend = CellClass.PREPEND+__name
        if hasattr(self,prepend):
            getattr(self, prepend).value = __value
        else:
            super().__setattr__(__name,__value)

@typing.overload
def listvalidfilenames(dire: str, recurse:bool=False)->typing.Generator[str,None, None]: ...

@typing.overload
def listvalidfilenames(dire: pathlib.Path, recurse:bool=False)->typing.Generator[pathlib.Path,None, None]: ...

def listvalidfilenames(dire: str|pathlib.Path, recurse:bool=False)->typing.Generator[str|pathlib.Path,None, None]:
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

class ExcelSeasonRecord(SeasonRecord):
    _showstats: "ExcelShowStats"
    @staticmethod
    def load_directory(dire: str|pathlib.Path, recurse:bool=False)->typing.Generator["ExcelSeasonRecord",None, None]:
        """ A generator that yields all the validly formatted Record files (as SeasonRecord instances)

            Args:
                dire: The directory to search for Record files
                recurse: If True, recursively search the directory for Record files. If False, only search the given directory.
        """
        for file in listvalidfilenames(dire,recurse):
            if isinstance(file,str):
                file = pathlib.Path(file)
            yield ExcelSeasonRecord(file)

    def __init__(self,file:pathlib.Path, data_only=False):
        xlsx=self.xlsx=AL_Excel.load_workbook(filename=str(file),data_only=data_only)
        self._sheets={sheet:xlsx[sheet] for sheet in xlsx.sheetnames}
        tables = Tables.get_all_tables(xlsx)
        tables = {table.displayName:table for (ws,table) in tables}
        try:
            table = tables.pop('RecordStats')
        except KeyError:
            table = ExcelRecordStats.parsesheet(self._sheets['Record Stats'])
        recordstats: ExcelRecordStats = ExcelRecordStats(table,self)
        self._recordstatssheet = table.worksheet
        if recordstats.version >= 3.1:
            recordstats = ExcelRecordStatsV3_1(table,self)
        
        table = tables.pop('Stats')
        # except KeyError:
        #     table = ShowStats.parsesheet(self._sheets['Show Stats'])
        if recordstats.version < 3:
            idvalue = ExcelShowStats.NAMEVALUE
        else: idvalue = ExcelShowStats.ORIGINALIDVALUE
        showstats = ExcelShowStats(table = table, record = self, idvalue = idvalue)
        self._showstatssheet = table.worksheet
                
        weeks: WeekLookup= collections.OrderedDict()
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

        ## DEV NOTE: Weeks is being initialized as Empty so that RankingSheet can reference the superclass' attributes
        super().__init__(file=file, recordstats=recordstats, showstats=showstats, weeks=weeks)

        for week,table in weektables.items():
            hypetable = hypetables.get(week)
            cuttable = cuttables.get(week)
            rounduptable = rounduptables.get(week)
            rounduprenewaltable = rounduptables.get(week)
            version = recordstats.version
            ## RankingSheetVersions ## uncomment to get text editor feedback
            if version >= 5.3:
                s = RankingSheetV5_3(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self, historytables.get(week))
            elif version >= 4.1:
                s = RankingSheetV4_1(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self, historytables.get(week))
            elif version >= 4:
                s = RankingSheetV4(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self, historytables.get(week))
            elif version >= 3.1:
                s = RankingSheetV3_1(table, hypetable, cuttable, rounduptable, rounduprenewaltable, self)
            elif version >= 3:
                s = RankingSheetV3(table, hypetable, cuttable, rounduptable, self)
            elif version >= 2.6:
                s = RankingSheetV2_6(table, hypetable, self)
            elif version >= 2.2:
                s = RankingSheetV2_2(table, hypetable, self)
            elif version >= 2.0:
                s = RankingSheetV2(table, hypetable, self)
            else:
                s = RankingSheetV0(table, hypetable, self)
            weeks[week]=s

        super().__init__(file=file, recordstats=recordstats, showstats=showstats, weeks=weeks)

    @property
    def sheets(self):
        return self._sheets
    @property
    def recordstatssheet(self)->Worksheet:
        return self._recordstatssheet
    @property
    def showstatssheet(self)->Worksheet:
        return self._showstatssheet

    def close(self):
        self.xlsx.close()

    def save(self):
        self.xlsx.save(self.file)

class ExcelRecordStats(RecordStats):
    
    @staticmethod
    def parsesheet(sheet: Worksheet)-> EnhancedTable:
        column = 1
        row = 1
        tableref = Tables.gettablesize(sheet,startcolumn = column, startrow = row)
        table = AL_Excel.EnhancedTable(worksheet = sheet, displayName = "RecordStats", ref = tableref)
        return table
    
    def __init__(self,table: Tables.EnhancedTable, record: SeasonRecord):
        ## todicts returns keys() at index 1 (also note that this should also only 
        ## return 1 actual row if the RecordStats is properly formatted)
        stats: RecordStatsDict = {"season": "", "year": 0, "version": 0.0, "extras": {}}
        for key,v in table.todicts(attribute="cell")[1].items():
            stats["extras"]["cell_"+key.lower()] = v
        season = stats["extras"].get('cell_season')
        if not season:
            season = extractseasonfromfilename(str(record.file)).season
        else: season = str(season.value)
        stats["season"] = season
        year = stats["extras"].get('cell_year')
        if not year:
            year = extractseasonfromfilename(str(record.file)).year
        else: year = int(year.value)
        stats["year"] = year
        version = stats["extras"].get('cell_version')
        if not version:
            version = 0.0
        else: version = float(version.value)
        stats["version"] = version

        super().__init__(record, stats)
        self._table = table

    @property
    def season(self)->str:
        return self.stats["season"]
    
    @property
    def year(self)->int:
        return int(self.stats["year"])
    
    @property
    def version(self)->float:
        return float(self.stats["version"])


    
class ExcelRecordStatsV3_1(ExcelRecordStats):
    def __init__(self,table: Tables.EnhancedTable, record: SeasonRecord):
        super().__init__(table,record)

    @property
    def targetshows(self)->int:
        return int(self.stats["extras"]['targetshows'])

class ExcelShowStats(ShowStats):
    SHOWIDVALUE = "SeriesID"
    ONAMEVALUE = "Original Name"
    NAMEVALUE = "Name"
    ORIGINALIDVALUE = "OriginalID"

    def __init__(self, table: Tables.EnhancedTable, record: SeasonRecord, idvalue: str):
        self._table = table
        self.record = record
        shows: list[collections.OrderedDict[str,Cell]] = table.todicts(keyfactory = DEFAULTKEYFACTORY, attribute="cell")
        ## Remove headers
        shows.pop(0)
        ## DEV NOTE: Initializing with empty shows because self.loadshows requires self.idvalue
        ##            The alternative would be to pass idvalue to loadshows
        super().__init__(shows = ShowLookup(), idvalue= idvalue)
        _shows = self.loadshows(shows)
        self.shows.update(_shows)

    def loadshows(self, shows: list[collections.OrderedDict[str, Cell]])-> ShowLookup:
        ## Note taht show[id] is a cell and therefore should be stored as .value
        return collections.OrderedDict((show[self.idvalue.lower()].value,ExcelShow(self,**show)) for show in shows if show[self.idvalue.lower()]) ## type: ignore ## Linter says that Cell.value returns _CellValue, but no such object exists so it's impossible to type
    @property
    def table(self)->Tables.EnhancedTable:
        return self._table
    
    def getshowbyname(self, show: str) -> "ExcelShow":
        return super().getshowbyname(show) ## type: ignore ## TODO: Not sure whether to overload or generic type _shows/getshowbyname
    
    def getshowsbyoriginalid(self, originalid: int) -> list["ExcelShow"]:
        return super().getshowsbyoriginalid(originalid) ## type: ignore ## TODO: Not sure whether to overload or generic type _shows/getshowbyname

class ExcelShow(ShowBase, CellClass):
    def __init__(self,statssheet: ShowStats, originalid: Cell, seasonid: Cell|None = None, seriesid: Cell|None = None, subseriesid: Cell|None = None,
                 watching: Cell|None = None, include: Cell|None = None, originalname: Cell|None = None, name: Cell|None = None, channel: Cell|None = None,
                 day: Cell|None = None, firstepisode: Cell|datetime.datetime|None = None, group: Cell|None = None, channelhomepage: Cell|None = None, image: Cell|None = None,
                 rssfeedname: Cell|None = None, hashtag: Cell|None = None, website: Cell|None = None, pv: Cell|None = None,
                 showboyid: Cell|None = None, annid: Cell|None = None,anilistid: Cell|None = None, malid: Cell|None = None, anidbid: Cell|None = None,
                 renewal: Cell|None = None, lastepisode: Cell|None = None, totalepisodes: Cell|None = None, lastnormalize: Cell|None = None, lastaverage: Cell|None = None,
                 lasthypelist: Cell|None = None, notes: Cell|None = None, lastseason: Cell|None = None, **kw):
        super().__init__(**kw)

        self.statssheet = statssheet
        self.cell_originalid = originalid

        self.cell_seasonid = seasonid
        self.cell_seriesid = seriesid
        self.cell_subseriesid = subseriesid
        self.cell_watching = watching
        self.cell_include = include
        self.cell_originalname = originalname
        self.cell_name = name
        self.cell_channel = channel
        self.cell_day = day
        self.cell_firstepisode = firstepisode
        self.cell_group = group
        self.cell_channelhomepage = channelhomepage
        self.cell_rssfeedname = rssfeedname
        self.cell_hashtag = hashtag
        self.cell_website = website
        self.cell_pv = pv
        self.cell_showboyid = showboyid
        self.cell_annid = annid
        self.cell_anilistid = anilistid
        self.cell_malid = malid
        self.cell_anidbid = anidbid
        self.cell_image = image
        self.cell_renewal = renewal
        self.cell_lastepisode = lastepisode
        self.cell_totalepisodes = totalepisodes
        self.cell_lastnormalize = lastnormalize
        self.cell_lasthypelist = lasthypelist
        self.cell_lastseason = lastseason

        self.cell_notes = notes

        self.episodeurls=dict()
        self.seasonorder=list()


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

class HypeList(CellClass):
    NAMEHEADER = "name"
    LASTHEADER = "lastlist"
    def __init__(self,table: Tables.EnhancedTable, week: "RankingSheet"):
        self._table = table
        self.week = week

    @property
    def rows(self):
        ## First index is keys()
        return self.table.todicts(keyfactory = DEFAULTKEYFACTORY, attribute="cell")[1:]

    @property
    def table(self)->Tables.EnhancedTable:
        return self._table
    
    def rank(self, show: "ExcelEpisode")-> int|None:
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
        return[row[self.NAMEHEADER].value for row in self.rows if row[self.NAMEHEADER] and row[self.NAMEHEADER].value] ## type: ignore ## Linter says that Cell.value returns _CellValue, but no such object exists so it's impossible to type
        
    @property
    def history(self)->typing.List[str]:
        return [row[self.LASTHEADER].value for row in self.rows if row[self.LASTHEADER] and row[self.LASTHEADER].value] ## type: ignore ## Linter says that Cell.value returns _CellValue, but no such object exists so it's impossible to type

    def rank(self,show: "ExcelEpisode")-> int|None:
        """ Returns the Rank on the current HypeList of the given show (None if the show is not on the hypelist) """
        if show.name in self.hypelist: return self.hypelist.index(show.name)+1
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

        Hypelist History Format:
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
            return self._historytable.todicts(keyfactory = DEFAULTKEYFACTORY, attribute="cell")[1:]
        return []

    def rank(self, show: "ExcelEpisode")-> int|None:
        for i,row in enumerate(self.hypelist, start=1):
            if row[self.OIDHEADER]==show.originalid:
                return i
        return None

class ExcelEpisode(Episode, CellClass):
    name: str = ""
    week: "RankingSheet|None" = None
    rank: int = -1
    show: ExcelShow|None = None
    
    def __init__(self, name: Cell, week:"RankingSheet", rank: Cell, show: ExcelShow):
        super().__init__(week = week, rank = int(rank.value) if rank.value else None, show = show, date = None, episodenumber = None) # type: ignore ## As noted elsewhere, the linter does understand rank.value.
                                                                                                              #  Converting inside of a try/except block beforehand doesn't supprose the linter error
        self.cell_name = name
        self.cell_week = week
        self.show = show
        self.cell_rank = rank

    @classmethod
    def parsetablevalues(cls, rankingsheet:"RankingSheet", tabledict: dict[str, Cell])-> dict[str, typing.Any]:
        return {}

    @classmethod
    def parse(cls, rankingsheet: "RankingSheet", tabledict: dict[str, Cell])-> "ExcelEpisode|None":
        vals = cls.parsetablevalues(rankingsheet, tabledict)
        return cls(**vals)

    def to_dict(self):
        return dict(originalid = self.originalid, name = self.name, week = self.week, rank = self.rank, ranktotal = self.ranktotal, episodenumber = self.episodenumber, hypelistocc = self.hypelistocc, hypelistrank = self.hypelistrank)

    def __repr__(self):
        return f"Episode {self.name}:{self.episodenumber}"
    
class ExcelEpisodeV0(ExcelEpisode):
    ## Added version 0
    oneliner: bool = False
    video: bool = False

    @classmethod
    def parsetablevalues(cls, rankingsheet:"RankingSheetV0", tabledict: dict[str, Cell])-> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)

        ## Show has identifying information, so get that first before parsing the tabledict
        showstats = rankingsheet.record.showstats
        ident = tabledict[showstats.idvalue.lower()]
        if not ident:
            raise ValueError(f"Could not identify Episode {tabledict}")
        
        show: ExcelShow = showstats.shows[ident.value] # type: ignore ## Linter doesn't recognize ident.value
        name = show.cell_name

        ## Check for old alias first
        originalid = tabledict.get("seriesid",None)
        if not originalid:
            originalid = show.cell_originalid

        rank = tabledict.get(rankingsheet.RANKHEADER, None)
        oneliner = tabledict.get(rankingsheet.ONELINERHEADER, None)
        video = tabledict.get(rankingsheet.VIDEOHEADER, None)

        base.update({"name":name, "week": rankingsheet, "originalid":originalid, "show":show, "rank":rank, "oneliner":oneliner, "video":video})

        return base

    def __init__(self, name: Cell, week:"RankingSheet", rank: Cell, show: ExcelShow, oneliner: Cell|None = None, video: Cell|None = None):
        super().__init__(name= name, week = week, rank = rank, show = show)
        self.cell_oneliner = oneliner
        self.cell_video = video
        

class ExcelEpisodeV2(ExcelEpisodeV0):
    ## Added version 2
    episodenumber: int = -1

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV2", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        episodenumber = tabledict.get(rankingsheet.EPISODENUMBERHEADER, None)
        base.update({"episodenumber":episodenumber})
        return base

    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow, oneliner: Cell | None = None, video: Cell | None = None, episodenumber: Cell | None = None):
        super().__init__(name = name, week = week, rank = rank, show = show, oneliner = oneliner, video = video)
        self.cell_episodenumber = episodenumber

class ExcelEpisodeV2_2(ExcelEpisodeV2):
    ## Removed Version 2.2
    ## episodenumber

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV2_2", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        del base["episodenumber"]
        return base

    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow, oneliner: Cell | None = None, video: Cell | None = None):
        super().__init__(name = name, week = week, rank = rank, show = show, oneliner = oneliner, video = video, episodenumber = None)
        del self.cell_episodenumber

class ExcelEpisodeV2_6(ExcelEpisodeV2_2):
    ## Added Version 2.6
    date: datetime.date|str|None = None

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV2_6", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        date = tabledict.get(rankingsheet.DATEHEADER, None)
        base.update({"date":date})
        return base

    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow, oneliner: Cell | None = None, video: Cell | None = None, date: Cell | None = None):
        super().__init__(name = name, week = week, rank = rank, show = show, oneliner = oneliner, video = video)
        self.cell_date = date

class ExcelEpisodeV3(ExcelEpisodeV2_6):
    ## Added Version 3
    originalid: int = -1
    watched: bool = False
    ## Removed Version 3
    ## oneliner

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV3", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        del base["oneliner"]
        originalid = tabledict.get(rankingsheet.ORIGINALIDHEADER, None)
        watched = tabledict.get(rankingsheet.WATCHEDHEADER, None)
        base.update({"originalid":originalid, "watched":watched})
        return base

    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow,
                 video: Cell | None = None, date: Cell | None = None, originalid: Cell | None = None,
                 watched: Cell | None = None):
        super().__init__(name=name, week=week, rank=rank, show=show, video=video, date=date, oneliner= None)
        self.cell_originalid = originalid
        self.cell_watched = watched
        del self.cell_oneliner

class ExcelEpisodeV4_1(ExcelEpisodeV3):
    ## Added Version 4.1
    episodenumber: int = -1

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV4_1", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        episodenumber = tabledict.get(rankingsheet.EPISODENUMBERHEADER, None)
        base.update({"episodenumber":episodenumber})
        return base
    
    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow,
                    video: Cell | None = None, date: Cell | None = None, originalid: Cell | None = None,
                    watched: Cell | None = None, episodenumber: Cell | None = None):
            super().__init__(name=name, week=week, rank=rank, show=show, video=video, date=date, originalid=originalid, watched=watched)
            self.cell_episodenumber = episodenumber

class ExcelEpisodeV5_3(ExcelEpisodeV4_1):
    ## Removed Version 5.3
    ## video

    @classmethod
    def parsetablevalues(cls, rankingsheet: "RankingSheetV5_3", tabledict: dict[str, Cell]) -> dict[str, typing.Any]:
        base = super().parsetablevalues(rankingsheet, tabledict)
        del base["video"]
        return base
    
    def __init__(self, name: Cell, week: "RankingSheet", rank: Cell, show: ExcelShow,
                    date: Cell | None = None, originalid: Cell | None = None,
                    watched: Cell | None = None, episodenumber: Cell | None = None):
            super().__init__(name=name, week=week, rank=rank, show=show, date=date, originalid=originalid, watched=watched, episodenumber=episodenumber, video = None)
            del self.cell_video
    
class FirstEpisodeRatingTable():
    pass

class ExcelRankingSheet(RankingSheet):
    RANKHEADER="rank"
    WEEKRE=re.compile(r'''.*week\s*(?P<week>\d+)''',re.IGNORECASE)
    HYPELIST: typing.Type[HypeList] = HypeListV1
    EPISODECLASS = ExcelEpisode

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
        ws = WEEKRE.search(table.displayName)
        if not ws: raise ValueError(f"Invalid Worksheet Name: does not contain a week number: {table.displayName}")
        weeknumber=int(ws.group("number"))
        if not hypelist:
            _hypelist = None
        else:
            _hypelist = self.HYPELIST(hypelist,self)

        ## DEV NOTE: We're initilizing episodes as an empty dict so that parseepisodes (and its super/dependent)
        ##           functions need access to the record (at the moment, record.showstats specifically)
        ##           The alternative would be to update all parseepisodes and parse functions on RankingSheet
        ##           and Episode to accept record as an argument
        super().__init__(record=record, weeknumber=weeknumber, episodes={}, hypelist=_hypelist)
        episodes = self.parseepisodes(table)
        self.episodes.update(episodes)

    @property
    def table(self):
        return self._table
    @property
    def record(self):
        return self._record
    
    def parseepisodes(self, table: EnhancedTable)-> EpisodeDict:
        return dict()

class RankingSheetV0(ExcelRankingSheet):
    """ Ranking Sheet for Record Versions prior to 4"""
    HYPELIST = HypeListV1
    EPISODECLASS = ExcelEpisodeV0

    ONELINERHEADER = "oneliner"
    VIDEOHEADER = "video"

    record: ExcelSeasonRecord


    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, record: ExcelSeasonRecord):
        super().__init__(table = table, hypelist = hypelist, record = record)

    def parseepisodes(self, table: Tables.EnhancedTable)-> EpisodeDict:
        shows: EpisodeDict = dict()
        ## Index-0 of todicts is keys()
        episodes = table.todicts(keyfactory = DEFAULTKEYFACTORY, attribute="cell")[1:]
        for tabledict in episodes:
            episode = self.EPISODECLASS.parse(self, tabledict)
            if episode:
                shows[episode.name] = episode
        return shows

class RankingSheetV2(RankingSheetV0):
    EPISODECLASS = ExcelEpisodeV2

    EPISODENUMBERHEADER = "seasonnumber"

class RankingSheetV2_2(RankingSheetV2):
    EPISODECLASS = ExcelEpisodeV2_2

class RankingSheetV2_6(RankingSheetV2_2):
    EPISODECLASS = ExcelEpisodeV2_6

    DATEHEADER = "date"


class RankingSheetV3(RankingSheetV2_6):
    HYPELIST = HypeListV1
    EPISODECLASS = ExcelEpisodeV3

    ORIGINALIDHEADER = "originalid"
    WATCHEDHEADER = "watched"

    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, cuttable: Tables.EnhancedTable|None,
                 rounduptable: Tables.EnhancedTable|None, record: ExcelSeasonRecord):
        super().__init__(table=table, hypelist=hypelist, record=record)
        self.cuttable = cuttable
        self.rounduptable = rounduptable


class RankingSheetV3_1(RankingSheetV3):
    HYPELIST: typing.Type[HypeListV1] = HypeListV1
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None, cuttable: Tables.EnhancedTable|None,
                 rounduptable: Tables.EnhancedTable|None, rounduprenewaltable: Tables.EnhancedTable|None,
                 record: ExcelSeasonRecord):
        super().__init__(table=table, hypelist=hypelist, cuttable=cuttable, rounduptable=rounduptable, record = record)
        self.rounduprenewaltable = rounduprenewaltable

class RankingSheetV4(RankingSheetV3_1):
    HYPELIST: typing.Type[HypeListv4] = HypeListv4
    def __init__(self, table: Tables.EnhancedTable, hypelist: Tables.EnhancedTable|None,
                 cuttable: Tables.EnhancedTable|None, rounduptable: Tables.EnhancedTable|None,
                 rounduprenewaltable: Tables.EnhancedTable|None, record: ExcelSeasonRecord, hypehistory: Tables.EnhancedTable|None = None):
        ## Do not pass hypehistory to super().__init__ since it has a different instantiation signature
        super().__init__(table, None, cuttable, rounduptable, rounduprenewaltable, record)
        if hypelist:
            self.hypelist = RankingSheetV4.HYPELIST(hypelist, self, hypehistory)

class RankingSheetV4_1(RankingSheetV4):
    EPISODECLASS = ExcelEpisodeV4_1

    EPISODENUMBERHEADER = "episodenumber"

class RankingSheetV5_3(RankingSheetV4_1):
    EPISODECLASS = ExcelEpisodeV5_3

## Saved for easier reference
RankingSheetVersions = RankingSheet|RankingSheetV0|RankingSheetV2|RankingSheetV2_2|\
    RankingSheetV2_6|RankingSheetV3|RankingSheetV3_1|RankingSheetV4|RankingSheetV4_1|RankingSheetV5_3