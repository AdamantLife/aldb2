## Builtin
import os,os.path
import pathlib


#Program Data Directories
DATAPATH=(pathlib.Path(os.path.expandvars('%PROGRAMDATA%'))/'AdamantMedia/AL Anime Database/').resolve()
DATAPATH.mkdir(parents=True,exist_ok=True)

DATABASEPATH=(DATAPATH / "databases/").resolve()
DATABASEPATH.mkdir(parents = True, exist_ok = True)

PROGRAMPATH = pathlib.Path(__file__).resolve().parent