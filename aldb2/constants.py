import typing
DTFORMAT = "%d/%m/%Y %H:%M %z"

CATRANKSTYPE = typing.Literal["A","B", "C", "D"]
CATRANKS: typing.Tuple[CATRANKSTYPE, ...] = typing.get_args(CATRANKSTYPE)
SEASONSTYPE = typing.Literal["Winter","Spring","Summer","Fall"] 
SEASONS: typing.Tuple[SEASONSTYPE, ...] = typing.get_args(SEASONSTYPE)

SEASINDEXLEN = 6
SEASONALIASESTYPE = typing.Literal["winter"   , 0  , "0"   , "w"       , "wi"  , "win",
                 "spring"   , 1  , "1"   , "spring"  , "sp"  , "spr",
                 "summer"   , 2  , "2"   , "summer"  , "su"  , "sum",
                 "fall"     , 3  , "3"   , "f"       , "fa"  , "fal"]
SEASONALIASES: typing.Tuple[SEASONALIASESTYPE, ...] = typing.get_args(SEASONALIASESTYPE)

ANIMESEASONDESCRIPTOR = tuple[SEASONSTYPE, int]
class AnimeSeasonDict(typing.TypedDict):
    season: SEASONSTYPE
    year: int

def getseasonindex(season: str)-> int:
    """ Returns the index of a season alias per SEASONALIASES """
    if (not isinstance(season,str) and season not in SEASONALIASES)\
        or season.lower() not in SEASONALIASES:
        raise ValueError("season is not a Season Alias")
    return SEASONALIASES.index(season.lower()) // SEASINDEXLEN