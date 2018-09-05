DTFORMAT = "%d/%m/%Y %H:%M %z"

CATRANKS = ["A","B", "C", "D"]
SEASONS = ['Winter','Spring','Summer','Fall']

SEASINDEXLEN = 6
SEASONALIASES = ["winter"   , 0  , "0"   , "w"       , "wi"  , "win",
                 "spring"   , 1  , "1"   , "spring"  , "sp"  , "spr",
                 "summer"   , 2  , "2"   , "summer"  , "su"  , "sum",
                 "fall"     , 3  , "3"   , "f"       , "fa"  , "fal"]

def getseasonindex(season):
    """ Returns the index of a season alias per SEASONALIASES """
    if (not isinstance(season,str) and season not in SEASONALIASES)\
        or season.lower() not in SEASONALIASES:
        raise ValueError("season is not a Season Alias")
    return SEASONALIASES.index(season.lower()) // SEASINDEXLEN