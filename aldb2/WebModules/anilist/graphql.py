## Custom Module
from alcustoms import graphql_query,web
from alcustoms.web import requests as alrequests
from alcustoms.graphql_query import Enum,EnumList,DeferredField,Field,IntList,StrList

""" GraphQL API Module

"""

API_URL = r"https://graphql.anilist.co"
HEADERS = {'Content-Type': 'application/json',
            'Accept': 'application/json'}

def query_api(querystring,variables = None, session = None):
    """ Queries the graphql api with the given querystring """
    if variables is None: variables = dict()
    if session is None: session = alrequests.getbasicsession()
    if isinstance(querystring,graphql_query.Query):
        querystring = querystring.getquery()
    return alrequests.POST_json(API_URL,session = session, headers = HEADERS,
                                  json = dict(query=querystring,variables=variables))

for constant in (
    "ID","ID_DESC", ## ActivitySort
    "TEXT","ANIME_LIST","MANGA_LIST","MESSAGE","MEDIA_LIST", ## ActivityType
    "ID","ID_DESC","MEDIA_ID","MEDIA_ID_DESC","TIME","TIME_DESC","EPISODE","EPISODE_DESC", ## AiringSort
    "MAIN","SUPPORTING","BACKGROUND", ## CharacterRole
    "ID","ID_DESC","ROLE","ROLE_DESC","SEARCH_MATCH", ## CharacterSort
    "TV", "TV_SHORT", "MOVIE", "SPECIAL", "OVA", "ONA", "MUSIC", "MANGA", "NOVEL", "ONE_SHOT", ## MediaFormat
    "MEDIA_ID","MEDIA_ID_DESC","SCORE","SCORE_DESC","STATUS","STATUS_DESC","PROGRESS","PROGRESS_DESC","PROGRESS_VOLUMNS",      ## MediaListSort
    "PROGRESS_VOLUMNS_DESC","REPEAT","REPEAT_DESC","PRIORTIY","PRIORITY_DESC","STARTED_ON","STARTED_ON_DESC","FINISHED_ON",    ## MediaListSort cont
    "FINISHED_ON_DESC","ADDED_TIME","ADDED_TIME_DESC","UPDATED_TIME","UPDATED_TIME_DESC",                                       ## MediaListSort cont
    "CURRENT","PLANNING","COMPLETED","DROPPED","PAUSED","REPEATING", ## MediaListStatus
    "RATED","POPULAR", ## MediaRankType
    "ADAPTATION","PREQUEL","SEQUEL","PARENT","SIDE_STORY","CHARACTER","SUMMARY","ALTERNATIVE","SPIN_OFF","OTHER", ## MediaRelation
    "WINTER","SPRING","SUMMER","FALL", ## MediaSeason
    "ID","ID_DESC","TITLE_ROMAJI","TITLE_ROMAJI_DESC","TITLE_ENGLISH","TITLE_ENGLISH_DESC","TITLE_NATIVE","TITLE_NATIVE_DESC", ## MediaSort
    "TYPE","TYPE_DESC","FORMAT","FORMAT_DESC","START_DATE","START_DATE_DESC","END_DATE","END_DATE_DESC","SCORE","SCORE_DESC",  ## MediaSort cont.
    "POPULARITY","POPULARITY_DESC","TRENDING","TRENDING_DESC","EPISODES","EPISODES_DESC","DURATION","DURATION_DESC","STATUS",  ## MediaSort cont.
    "STATUS_DESC","CHAPTERS","CHAPTERS_DESC","VOLUMNS","VOLUMNS_DESC","UPDATED_AT","UPDATED_AT_DESC","SEARCH_MATCH",           ## MediaSort cont.
    "FINISHED","RELEASING","NOT_YET_RELEASED","CANCELLED", ## MediaStatus
    "ORIGINAL","MANGA","LIGHT_NOVEL","VISUAL_NOVEL","VIDEO_GAME","OTHER", #MediaSource                 
    "ID","ID_DESC","MEDIA_ID","MEDIA_ID_DESC","DATE","DATE_DESC","SCORE","SCORE_DESC","POPULARITY","POPULARITY_DESC","TRENDING","TRENDING_DESC","EPISODE","EPISODE_DESC", ## MediaTrendSort
    "ANIME","MANGA", ## MediaType
    "ACTIVITY_MESSAGE","ACTIVITY_REPLY","FOLLOWING","ACTIVITY_MENTION","THREAD_COMMENT_MENTION","THREAD_SUBSCRIBED",    ## NotificationType
    "THREAD_COMMENT_REPLY","AIRING","ACTIVITY_LIKE","ACTIVITY_REPLY_LIKE","THREAD_LIKE","THREAD_COMMENT_LIKE",           ## NotificationType cont.
    "NO_VOTE","UP_VOTE","DOWN_VOTE", ## ReviewRating
    "ID","ID_DESC","SCORE","SCORE_DESC","RATING","RATING_DESC","CREATED_AT","CREATED_AT_DESC","UPDATED_AT","UPDATED_AT_DESC", ## ReviewSort
    "POINT_100","POINT_10_DECIMAL","POINT_10","POINT_5","POINT_3", ## ScoreFormat
    "JAPANESE","ENGLISH","KOREAN","ITALIAN","SPANISH","PORTUGUESE","FRENCH","GERMAN","HEBREW","HUNGARIAN", ## StaffLanguage
    "ID","ID_DESC","ROLE","ROLE_DESC","LANGUAGE","LANGUAGE_DESC","SEARCH_MATCH", ## StaffSort
    "ID","ID_DESC","NAME","NAME_DESC","SEARCH_MATCH", ## StudioSort
    "ID","ID_DESC","TITLE","TITLE_DESC","CREATED_AT","UPDATED_AT","UPDATED_AT_DESC","RELIED_AT","REPLIED_AT_DESC",  ## ThreadSort
    "REPLY_COUNT","REPLY_COUNT_DESC","VIEW_COUNT","VIEW_COUNT_DESC","IS_STICKY","SEARCH_MATCH"                      ## ThreadSort cont.
    "ID","ID_DESC","USERNAME","USERNAME_DESC","WATCHED_TIME","WATCHED_TIME_DESC","CHAPTERS_READ","CHAPTERS_READ_DESC","SEARCH_MATCH", ## UserSort
    "ROMAJI","ENGLISH","NATIVE","ROMAJI_STYLISED","ENGLISH_STYLISED","NATIVE_STYLISED", ## UserTitleLanguage
    ):
    globals()[constant.replace(" ","_")] = graphql_query.Constant(constant)
del constant

ActivitySort = Enum(ID,ID_DESC)
ActivityType = Enum(TEXT,ANIME_LIST,MANGA_LIST,MESSAGE,MEDIA_LIST)
AiringSort = Enum(ID,ID_DESC,MEDIA_ID,MEDIA_ID_DESC,TIME,TIME_DESC,EPISODE,EPISODE_DESC)
CharacterRole = Enum(MAIN,SUPPORTING,BACKGROUND)
CharacterSort = Enum(ID,ID_DESC,ROLE,ROLE_DESC,SEARCH_MATCH)
MediaFormat = Enum(TV,TV_SHORT,MOVIE,SPECIAL,OVA,ONA,MUSIC,MANGA,NOVEL,ONE_SHOT)
MediaListSort = Enum(MEDIA_ID,MEDIA_ID_DESC,SCORE,SCORE_DESC,STATUS,STATUS_DESC,PROGRESS,PROGRESS_DESC,PROGRESS_VOLUMNS,
                 PROGRESS_VOLUMNS_DESC,REPEAT,REPEAT_DESC,PRIORTIY,PRIORITY_DESC,STARTED_ON,STARTED_ON_DESC,FINISHED_ON,
                 FINISHED_ON_DESC,ADDED_TIME,ADDED_TIME_DESC,UPDATED_TIME,UPDATED_TIME_DESC)
MediaListStatus = Enum(CURRENT,PLANNING,COMPLETED,DROPPED,PAUSED,REPEATING)
MediaRankType = Enum(RATED,POPULAR)
MediaRelation = Enum(ADAPTATION,PREQUEL,SEQUEL,PARENT,SIDE_STORY,CHARACTER,SUMMARY,ALTERNATIVE,SPIN_OFF,OTHER)
MediaSeason = Enum(WINTER,SPRING,SUMMER,FALL)
MediaSort = Enum(ID,ID_DESC,TITLE_ROMAJI,TITLE_ROMAJI_DESC,TITLE_ENGLISH,TITLE_ENGLISH_DESC,TITLE_NATIVE,TITLE_NATIVE_DESC,
                 TYPE,TYPE_DESC,FORMAT,FORMAT_DESC,START_DATE,START_DATE_DESC,END_DATE,END_DATE_DESC,SCORE,SCORE_DESC,
                 POPULARITY,POPULARITY_DESC,TRENDING,TRENDING_DESC,EPISODES,EPISODES_DESC,DURATION,DURATION_DESC,STATUS,
                 STATUS_DESC,CHAPTERS,CHAPTERS_DESC,VOLUMNS,VOLUMNS_DESC,UPDATED_AT,UPDATED_AT_DESC,SEARCH_MATCH)
MediaSource = Enum(ORIGINAL,MANGA,LIGHT_NOVEL,VISUAL_NOVEL,VIDEO_GAME,OTHER)
MediaStatus = Enum(FINISHED, RELEASING,NOT_YET_RELEASED,CANCELLED)
MediaTrendSort = Enum(ID,ID_DESC,MEDIA_ID,MEDIA_ID_DESC,DATE,DATE_DESC,SCORE,SCORE_DESC,POPULARITY,POPULARITY_DESC,TRENDING,TRENDING_DESC,EPISODE,EPISODE_DESC)
MediaType = Enum(ANIME,MANGA)
NotificationType = Enum(ACTIVITY_MESSAGE,ACTIVITY_REPLY,FOLLOWING,ACTIVITY_MENTION,THREAD_COMMENT_MENTION,THREAD_SUBSCRIBED,
    THREAD_COMMENT_REPLY,AIRING,ACTIVITY_LIKE,ACTIVITY_REPLY_LIKE,THREAD_LIKE,THREAD_COMMENT_LIKE)
ReviewRating = Enum(NO_VOTE,UP_VOTE,DOWN_VOTE)
ReviewSort = Enum(ID,ID_DESC,SCORE,SCORE_DESC,RATING,RATING_DESC,CREATED_AT,CREATED_AT_DESC,UPDATED_AT,UPDATED_AT_DESC)
ScoreFormat = Enum(POINT_100,POINT_10_DECIMAL,POINT_10,POINT_5,POINT_3)
StaffLanguage = Enum(JAPANESE,ENGLISH,KOREAN,ITALIAN,SPANISH,PORTUGUESE,FRENCH,GERMAN,HEBREW,HUNGARIAN)
StaffSort = Enum(ID,ID_DESC,ROLE,ROLE_DESC,LANGUAGE,LANGUAGE_DESC,SEARCH_MATCH)
StudioSort = Enum(ID,ID_DESC,NAME,NAME_DESC,SEARCH_MATCH)
ThreadSort = Enum(ID,ID_DESC,TITLE,TITLE_DESC,CREATED_AT,UPDATED_AT,UPDATED_AT_DESC,RELIED_AT,REPLIED_AT_DESC,
    REPLY_COUNT,REPLY_COUNT_DESC,VIEW_COUNT,VIEW_COUNT_DESC,IS_STICKY,SEARCH_MATCH)
UserSort = Enum(ID,ID_DESC,USERNAME,USERNAME_DESC,WATCHED_TIME,WATCHED_TIME_DESC,CHAPTERS_READ,CHAPTERS_READ_DESC,SEARCH_MATCH)
UserTitleLanguage = Enum(ROMAJI,ENGLISH,NATIVE,ROMAJI_STYLISED,ENGLISH_STYLISED,NATIVE_STYLISED)

ActivitySortList = EnumList(ActivitySort)
ActivityTypeList = EnumList(ActivityType)
AiringSortList = EnumList(AiringSort)
CharacterSortList = EnumList(CharacterSort)
MediaFormatList = EnumList(MediaFormat)
MediaListSortList = EnumList(MediaListSort)
MediaSortList = EnumList(MediaSort)
MediaStatusList = EnumList(MediaStatus)
MediaTrendSortList = EnumList(MediaTrendSort)
ReviewSortList = EnumList(ReviewSort)
StaffSortList = EnumList(StaffSort)
StudioSortList = EnumList(StudioSort)
ThreadSortList = EnumList(ThreadSort)
UserSortList = EnumList(UserSort)

class PageInfo(graphql_query.Query):
    NAME = "pageInfo"
    FIELDS = ("total","perPage","currentPage","lastPage","hasNextPage")

class FuzzyDate(graphql_query.Query):
    FIELDS = ("year","month","day")
class startDate(FuzzyDate):
    NAME = "startDate"
class endDate(FuzzyDate):
    NAME = "endDate"

class Image(graphql_query.Query):
    FIELDS = ("large","medium")

class CharacterImage(Image):
    NAME = "image"

class MediaCoverImage(Image):
    NAME = "coverImage"

class StaffImage(Image):
    NAME = "image"

class UserAvatar(Image):
    NAME = "avatar"

class StatusDistribution(graphql_query.Query):
    NAME = "statusDistribution"
    FIELDS = ("status","amount")

class AnimeStatusDistribution(StatusDistribution): NAME= "animeStatusDistribution"
class MangaStatusDistribution(StatusDistribution): NAME= "mangaStatusDistribution"

class ScoreDistribution(graphql_query.Query):
    NAME = "scoreDistribution"
    FIELDS = ("score","amount")

class AnimeScoreDistribution(ScoreDistribution): NAME= "animeScoreDistribution"
class MangaScoreDistribution(ScoreDistribution): NAME= "mangaScoreDistribution"

class MediaStats(graphql_query.Query):
    NAME = "stats"
    FIELDS = (ScoreDistribution,StatusDistribution)

class GenreStats(graphql_query.Query):
    FIELDS = ("genre","amount","meanScore","timeWatched")

class FavouredGenresOverview(GenreStats):
    NAME = "favouredGenresOverview"

class FavouredGenres(GenreStats):
    NAME = "favouredGenres"

class ListScoreStats(graphql_query.Query):
    FIELDS = ("meanScore","standardDeviation")

class AnimeListScores(ListScoreStats): NAME= "animeListScores"
class MangaListScores(ListScoreStats): NAME= "mangaListScores"

class MediaListTypeOptions(graphql_query.Query):
    FIELDS = ("sectionOrder","splitCompletedSectionByFormat","customLists","advancedScoring","advancedScoringEnabled")

class AnimeListTypeOptions(MediaListTypeOptions):
    NAME = "animeList"
class MangaListTypeOptions(MediaListTypeOptions):
    NAME = "mangaList"

class MediaListOptions(graphql_query.Query):
    NAME = "mediaListOptions"
    FIELDS = ("scoreFormat", "rowOrder","useLegacyLists",AnimeListTypeOptions,MangaListTypeOptions)

class MediaTag(graphql_query.Query):
    NAME = "tag"
    FIELDS = ("id","name","description","category","rank","isGeneralSpoiler","isMediaSpoiler","isAdult")

class MediaTags(MediaTag):
    NAME = "tags"

class TagStats(graphql_query.Query):
    FIELDS = (MediaTag,"amount","meanScore","timeWatched")

class FavouredTags(TagStats):
    NAME = "favouredTags"

class UserActivityHistory(graphql_query.Query):
    NAME = "activityHistory"
    FIELDS = ("date","amount","level")

class YearStats(graphql_query.Query):
    FIELDS = ("year","amount","meanScore")

class FavouredYears(YearStats):
    NAME = "favouredYears"

class FormatStats(graphql_query.Query):
    FIELDS = ("format","amount")

class FavouredFormat(FormatStats):
    NAME = "favouredFormat"

class StaffName(graphql_query.Query):
    NAME = "name"
    FIELDS = ("first","last","native")

class UserOptions(graphql_query.Query):
    NAME = "options"
    FIELDS = ("titleLanguage","displayAdultContent")

class ThreadCategory(graphql_query.Query):
    FIELDS = ("id","name")

class ThreadCategories(ThreadCategory):
    NAME = "categories"

class CharacterName(graphql_query.Query):
    NAME = "name"
    FIELDS = ("first","last","native","alternative")

class MediaTrailer(graphql_query.Query):
    NAME = "trailer"
    FIELDS = ("id","site")

class MediaExternalLink(graphql_query.Query):
    NAME = "externalLinks"
    FIELDS = ("id","url","site")

class StreamingEpisodes(graphql_query.Query):
    NAME = "streamingEpisodes"
    FIELDS = ("title","thumbnail","url","site")

class MediaRank(graphql_query.Query):
    FIELDS = ("id","rank","type","format","year","season","allTime","context")

class MediaRankings(MediaRank):
    NAME = "rankings"

class MediaTitle(graphql_query.Query):
    NAME = "title"
    FIELDS = (Field("romaji",stylized=bool),Field("english",stylized=bool),Field("native",stylized=bool),"userPreferred")

class MediaConnection(graphql_query.Query):
    NAME = "relations"
    FIELDS = [DeferredField("MediaEdges"),DeferredField("MediaNodes"),PageInfo]

class CharacterMedia(MediaConnection):
    NAME = "media"
    FILTERS = {
        "sort":MediaSort,
        "type":MediaType,
        "page":int,
        "perPage":int
        }

class Characters(graphql_query.Query):
    NAME = "characters"
    FIELDS = ("id",CharacterName, CharacterImage, Field("description",asHtml = bool),"isFavourite","siteUrl",CharacterMedia)

class CharacterNode(Characters):
    NAME = "node"

class CharacterNodes(Characters):
    NAME = "nodes"

class AnimeFavourites(MediaConnection):
    NAME = "anime"
    FILTERS = {
        "page":int,
        "perPage":int
        }

class MangaFavourites(MediaConnection):
    NAME = "manga"
    FILTERS = {
        "page":int,
        "perPage":int
        }

class StaffMedia(MediaConnection):
    NAME = "staffMedia"
    FILTERS = {
        "sort":MediaSort,
        "type":MediaType,
        "page":int,
        "perPage":int
        }

class StudioMedia(MediaConnection):
    NAME = "media"
    FILTERS = {
        "sort":MediaSort,
        "isMain":bool,
        "page":int,
        "perPage":int
        }

class Studio(graphql_query.Query):
    FIELDS = ("id","name",StudioMedia,"siteUrl","isFavourite")

class StudioNode(Studio):
    NAME = "node"

class StudioNodes(StudioNode):
    NAME = "nodes"

class StudioEdges(graphql_query.Query):
    NAME = "edges"
    FIELDS = (StudioNode,"id","isMain","favouriteOrder")

class StudioConnection(graphql_query.Query):
    FIELDS = (StudioEdges, StudioNodes,PageInfo)

class MediaStudios(StudioConnection):
    NAME = "studios"
    FILTERS = {
        "sort":StudioSortList,
        "isMain":bool
        }

class StudioFavourites(StudioConnection):
    NAME = "studios"
    FILTERS = {
        "page":int,
        "perPage":int
        }

class StudioStats(graphql_query.Query):
    FIELDS = (Studio,"amount","meanScore","timeWatched")

class FavouredStudio(StudioStats):
    NAME = "favouredStudios"

class CharacterConnection(graphql_query.Query):
    NAME = "characters"
    FIELDS = [DeferredField("CharacterEdges"),CharacterNodes,PageInfo]
    FILTERS = {
        "sort":CharacterSort,
        "page":int,
        "perPage":int
        }

class MediaCharacters(CharacterConnection):
    FILTERS = {
        "sort":CharacterSortList,
        "role":CharacterRole,
        "page":int,
        "perPage":int
        }

class CharacterFavourites(CharacterConnection):
    NAME = "characters"
    FILTERS = {
        "page":int,
        "perPage":int
        }

class Staff(graphql_query.Query):
    FIELDS = ("id",StaffName,"language",StaffImage,Field("description",asHtml = bool),"isFavourite","siteUrl",StaffMedia,CharacterConnection)

class StaffNode(Staff):
    NAME = "node"

class StaffNodes(StaffNode):
    NAME = "nodes"

class StaffEdge(graphql_query.Query):
    FIELDS = (StaffNode,"id","role","favouriteOrder")

class StaffEdges(StaffEdge):
    NAME = "edges"

class StaffConnection(graphql_query.Query):
    FIELDS = (StaffEdges, StaffNodes, PageInfo)

class VoiceActors(Staff):
    NAME = "voiceActors"
    FILTERS = {
        "language":StaffLanguage,
        "sort":StaffSortList
        }

class MediaStaff(StaffConnection):
    NAME = "staff"
    FILTERS = {
        "sort":StaffSortList,
        "page":int,
        "perPage":int
        }

class StaffStats(graphql_query.Query):
    FIELDS = (Staff,"amount","meanScore","timeWatched")

class FavouredActors(StaffStats):
    NAME = "favouredActors"

class FavouredStaff(StaffStats):
    NAME = "favouredStaff"

class StaffFavourites(StaffConnection):
    NAME = "staff"
    FILTERS = {
        "page":int,
        "perPage":int
        }

class Favourites(graphql_query.Query):
    NAME = "favourites"
    FIELDS = (AnimeFavourites,MangaFavourites,CharacterFavourites,StaffFavourites,StudioFavourites)
    FILTERS = {
        "page":int
        }

class UserStats(graphql_query.Query):
    NAME = "stats"
    FIELDS = ("watchedTime","chaptersRead",UserActivityHistory,AnimeStatusDistribution,MangaStatusDistribution,
              AnimeScoreDistribution,MangaScoreDistribution,AnimeListScores,MangaListScores,FavouredGenresOverview,
              FavouredGenres,FavouredTags,FavouredActors,FavouredStaff,FavouredStudio,FavouredYears,FavouredFormat)

class User(graphql_query.Query):
    NAME = "user"
    FIELDS = ("id","name",Field("about",asHtml=bool),UserAvatar,"bannerImage","isFollowing",UserOptions,
              MediaListOptions,Favourites,UserStats,"unreadNotificationCount","siteUrl","donatorTier","updatedAt")

class Users(User):
    NAME = "users"
    FILTERS = {
        "id":int,
        "name":str,
        "search":str,
        "sort":UserSortList
        }

class Likes(User):
    NAME = "likes"

class ReplyUser(User):
    NAME = "replyUser"

class ActivityReply(graphql_query.Query):
    FIELDS = ("id","userId","activityId",Field("text",asHtml = bool),"createdAt",User,Likes)

class ThreadComment(graphql_query.Query):
    FIELDS = ("id","userId","threadId",Field("comment",asHtml=bool),"siteUrl","createdAt","udpatedAt",User,Likes,"childComments")

class Media(graphql_query.Query):
    NAME = "Media"
    FIELDS = ["id","idMal",MediaTitle,"type","format","status","description",startDate,endDate,"season",
             "episodes","duration","chapters","volumes","contryOfOrigin","isLicensed","source","hashtag",
             MediaTrailer,"updatedAt",MediaCoverImage,"bannerImage","genres","synonyms","averageScore",
             "meanScore","popularity","trending",MediaTags,MediaConnection,MediaCharacters,MediaStaff,
             MediaStudios, "isFavourite", "isAdult",DeferredField("NextAiringSchedule"),
             DeferredField("MediaAiringSchedule"),DeferredField("MediaTrends"),MediaExternalLink,
             StreamingEpisodes,MediaRankings,DeferredField("MediaListEntry"),DeferredField("MediaReviews"),
             MediaStats,"siteUrl","autoCreateForumThread","modNotes"]
    FILTERS = {
        "id_in":graphql_query.IntList,
        }

class MediaNode(Media):
    NAME = "node"

class MediaNodes(MediaNode):
    NAME = "nodes"

class MediaEdges(graphql_query.Query):
    NAME = "edges"
    FIELDS = (MediaNode,"id","relationType","isMainStudio",Characters,"characterRole","staffRole",VoiceActors,"favouriteOrder")

class media(Media):
    ## AniList uses lower-case depending on situation
    NAME = "media"

class MediaCategories(Media):
    NAME = "mediaCategories"

class Thread(graphql_query.Query):
    FIELDS = ("id","title",Field("body",asHtml=bool),"userId","replyUserId","replyCommentId","replyCount","viewCount",
              "isLocked","isSticky","isSubscribed","repliedAt","createdAt","updatedAt",User,ReplyUser,Likes,"siteUrl",
              ThreadCategories,MediaCategories)

class CharacterEdges(graphql_query.Query):
    NAME = "edges"
    FIELDS = (CharacterNode, "id","role",VoiceActors,media,"favouriteOrder")

class AiringSchedule(graphql_query.Query):
    FIELDS = ("id","airingAt","timeUntilAiring","episode","mediaId",media)

class NextAiringSchedule(AiringSchedule):
    NAME= "nextAiringSchedule"

class AiringNode(AiringSchedule):
    NAME = "node"

class AiringNodes(AiringNode):
    NAME = "nodes"

class AiringEdges(graphql_query.Query):
    NAME = "edges"
    FIELDS = (AiringNode,"id")

class AiringScheduleConnection(graphql_query.Query):
    FIELDS = (AiringEdges,AiringNodes,PageInfo)

class MediaAiringSchedule(AiringScheduleConnection):
    NAME = "airingSchedule"
    FILTERS = {
        "notYetAired":bool,
        "page":int,
        "perPage":int,
        }

class MediaTrend(graphql_query.Query):
    FIELDS = ("mediaId","date","trending","averageScore","popularity","inProgress","releasing","episode",media)

class MediaTrendNode(MediaTrend):
    NAME = "node"

class MediaTrendNodes(MediaTrendNode):
    NAME = "nodes"

class MediaTrendEdges(graphql_query.Query):
    NAME = "edges"
    FIELDS = (MediaTrendNode,)

class MediaTrendsConnection(graphql_query.Query):
    FIELDS = (MediaTrendEdges,MediaTrendNodes,PageInfo)

class MediaTrends(MediaTrendsConnection):
    NAME = "trends"
    FILTERS = {
        "sort":MediaTrendSortList,
        "releasing":bool,
        "page":int,
        "perPage":int
        }

class MediaList(graphql_query.Query):
    FIELDS = ("id","userId","mediaId","status",Field("score",format = ScoreFormat),"progress","progressVolumes","repeat",
              "priority","private","notes","hiddenFromStatusLists",Field("customLists",asArray = bool),"advancedScores",
              "startedAt","completedAt","udpatedAt","createdAt",media,User)

class MediaListEntry(MediaList):
    NAME = "mediaListEntry"

class Review(graphql_query.Query):
    FIELDS = ("id","userId","mediaId","mediaType","summary",Field("body",asHtml = bool),"rating","ratingAmount",
              "userRating","score","private","siteUrl","createdAt","updatedAt",User,media)

class ReviewNode(Review):
    NAME = "node"

class ReviewNodes(ReviewNode):
    NAME = "nodes"

class ReviewEdge(graphql_query.Query):
    NAME = "edge"
    FIELDS = (ReviewNode,)

class ReviewEdges(ReviewEdge):
    NAME = "edges"

class ReviewConnection(graphql_query.Query):
    FIELDS = (ReviewEdges,ReviewNodes,PageInfo)

class MediaReviews(ReviewConnection):
    NAME = "reviews"
    FILTERS = {
        "limit":int,
        "sort":ReviewSortList,
        "page":int,
        "perPage":int
        }

class PageMedia(media):
    FILTERS = {
        "id":int,
        "idMal":int,
        "startDate":int,
        "season":MediaSeason,
        "seasonYear":int,
        "type":MediaType,
        "format":MediaFormat,
        "status":MediaStatus,
        "episodes":int,
        "duration":int,
        "chapters":int,
        "volumes": int,
        "isAdult" : bool,
        "genre" : str,
        "tag" : str,
        "tagCategory" : str,
        "onList" : bool,
        "averageScore" : int,
        "popularity" : int,
        "search" : str,
        "id_not" : int,
        "id_in" : IntList,
        "id_not_in" : IntList,
        "idMal_not" : int,
        "idMal_in" : IntList,
        "idMal_not_in" : IntList,
        "startDate_greater" : int,
        "startDate_lesser" : int,
        "startDate_like" : str,
        "endDate_greater" : int,
        "endDate_lesser" : int,
        "endDate_like" : str,
        "format_in" : MediaFormatList,
        "format_not" : MediaFormat,
        "format_not_in" : MediaFormatList,
        "status_in" : MediaStatusList,
        "status_not" : MediaStatus,
        "status_not_in" : MediaStatusList,
        "episodes_greater" : int,
        "episodes_lesser" : int,
        "duration_greater" : int,
        "duration_lesser" : int,
        "chapters_greater" : int,
        "chapters_lesser" : int,
        "volumes_greater" : int,
        "volumes_lesser" : int,
        "genre_in" : StrList,
        "genre_not_in" : StrList,
        "tag_in" : StrList,
        "tag_not_in" : StrList,
        "tagCategory_in" : StrList,
        "tagCategory_not_in" : StrList,
        "averageScore_not" : int,
        "averageScore_greater" : int,
        "averageScore_lesser" : int,
        "popularity_not" : int,
        "popularity_greater" : int,
        "popularity_lesser" : int,
        "sort" : MediaSortList
        }

class PageMediaList(MediaList):
    NAME = "mediaList"
    FILTERS = {
        "id":int,
        "userId":int,
        "userName":str,
        "type":MediaType,
        "status":MediaListStatus,
        "mediaId":int,
        "isFollowing":bool,
        "notes":str,
        "startedAt":int,
        "userId_in":IntList,
        "notes_like":str,
        "startedAt_greater":int,
        "startedAt_lesser":int,
        "startedAt_like":str,
        "completedAt_greater":int,
        "completedAt_lesser":int,
        "completedAt_like":str,
        "sort":MediaListSortList
        }

class PageAiringSchedules(AiringSchedule):
    NAME = "airingSchedules"
    FILTERS = {
        "id":int,
        "mediaId":int,
        "episode":int,
        "airingAt":int,
        "notYetAired":bool,
        "id_not":int,
        "id_in":IntList,
        "id_not_in":IntList,
        "mediaId_not":int,
        "mediaId_in":IntList,
        "mediaId_not_in":IntList,
        "episode_not":int,
        "episode_in":IntList,
        "episode_not_in":IntList,
        "episode_greater":int,
        "episode_lesser":int,
        "airingAt_greater":int,
        "airingAt_lesser":int,
        "sort":AiringSortList
        }

class PageMediaTrends(MediaTrend):
    NAME = "mediaTrends"
    FILTERS = {
        "mediaId":int,
        "date":int,
        "trending":int,
        "averageScore":int,
        "popularity":int,
        "episode":int,
        "releasing":bool,
        "mediaId_not":int,
        "mediaId_in":IntList,
        "mediaId_not_in":IntList,
        "date_greater":int,
        "date_lesser":int,
        "trending_greater":int,
        "trending_lesser":int,
        "tredning_not":int,
        "averageScore_greater":int,
        "averageScore_lesser":int,
        "averageScore_not":int,
        "popularity_greater":int,
        "popularity_lesser":int,
        "popularity_not":int,
        "episode_greater":int,
        "episode_lesser":int,
        "episode_not":int,
        "sort":MediaTrendSortList,
        }

class PageThreads(Thread):
    NAME = "threads"
    FILTERS = {
        "id":int,
        "userId":int,
        "replyUserId":int,
        "subscribed":bool,
        "categoryId":int,
        "mediaCategoryId":int,
        "search":str,
        "id_in":IntList,
        "sort":ThreadSortList
        }

class PageReviews(Review):
    NAME = "reviews"
    FILTERS = {
        "id":int,
        "mediaId":int,
        "userId":int,
        "mediaType":MediaType,
        "sort":ReviewSortList
        }

class PageCharacters(Characters):
    FILTERS = {
        "id":int,
        "search":str,
        "id_not":int,
        "id_in":IntList,
        "id_not_in":IntList,
        "sort":CharacterSortList
        }

class PageStaff(Staff):
    NAME = "staff"
    FILTERS = {
        "id":int,
        "search":str,
        "id_not":int,
        "id_in":IntList,
        "id_not_in":IntList,
        "sort":StaffSortList
        }

class PageThreadComments(ThreadComment):
    NAME = "threadComments"
    FILTERS = {
        "id":int,
        "threadId":int,
        "userId":int,
        }

class PageFollowers(User):
    NAME = "followers"
    FILTERS = {
        "userId":int,
        "sort":UserSortList
        }

class PageFollowing(User):
    NAME = "following"
    FILTERS = {
        "userId":int,
        "sort":UserSortList
        }

class PageNotifications():## TODO NotificationUnions (Unions Forks into multiple possible Field-sets)
    NAME = "notifications"
    FILTERS = {
        "type":NotificationType,
        "resetNotificationCount":bool
        }

class PageActivities(): ## TODO
    NAME = "activities"
    FILTERS = {
        "id":int,
        "userId":int,
        "messengerId":int,
        "mediaId":int,
        "type":ActivityType,
        "isFollowing":bool,
        "hasReplies":bool,
        "hasRepliesOrTypeText":bool,
        "createdAt":int,
        "id_not":int,
        "id_in":IntList,
        "id_not_in":IntList,
        "userId_not":int,
        "userId_in":IntList,
        "userId_not_in":IntList,
        "messengerId_not":int,
        "messengerId_in":IntList,
        "messengerId_not_in":IntList,
        "mediaId_not":int,
        "mediaId_in":IntList,
        "mediaId_not_in":IntList,
        "type_not":ActivityType,
        "type_in":ActivityTypeList,
        "type_not_in":ActivityTypeList,
        "createdAt_greater":int,
        "createdAt_lesser":int,
        "sort":ActivitySortList
        }

class PageActivityReplies(ActivityReply):
    NAME = "activityReplies"
    FILTERS = {
        "id":int,
        "activityId":int
        }

class PageStudios(Studio):
    NAME = "studios"
    FILTERS = {
        "id":int,
        "search":str,
        "id_not":int,
        "id_in":IntList,
        "id_not_in":IntList,
        "sort":StudioSortList
        }

class Page(graphql_query.Query):
    NAME = "Page"
    FIELDS = (PageInfo,Users,PageMedia, PageCharacters, PageStaff, PageStudios,PageMediaList, PageAiringSchedules, PageMediaTrends, ## TODO: Add PageNotification
             PageFollowers,PageFollowing,PageActivityReplies,PageThreads,PageThreadComments,PageReviews) ## TODO: Add PageActivities

class QueryPage(Page):
    FILTERS = {
        "page":int,
        "perPage":int
        }

class Query(graphql_query.Query):
    NAME = "query"
    FIELDS = (QueryPage,)

graphql_query.updatedefferedfields(locals())

## Sanity Check
assert not [Q for Q in globals().values()
            if isinstance(Q,type)
            and issubclass(Q,graphql_query.Query)
            and any(
                isinstance(F,DeferredField) for F in Q.FIELDS
                )]


##################################################################
"""
                HELPER FUNCTIONS
                                                               """
##################################################################

def getpage(*fields,perPage = 50, page = None):
    """ A method for generating a QueryPage with default perPage of 50 and page of 1. """
    if page is None: page = 1
    if not isinstance(page,int) or page <= 0:
        raise ValueError("'page' must be a positive integer")
    return QueryPage(*fields,perPage = 50, page = page)

def getpageinfo(*fields):
    """ Generates a generic PageInfo Field with an automaticaly-added "hasNextPage" field"""
    if "hasNextPage" not in fields:
        fields = list(fields) + ["hasNextPage",]
    return PageInfo(*fields)