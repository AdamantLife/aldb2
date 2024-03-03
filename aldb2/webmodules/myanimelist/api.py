## Builtin
import json
import re
import pathlib
import typing
import xml.etree.ElementTree as ElementTree
## Third Party
import requests
## This Module
from aldb2 import filestructure



MALRATINGSDICT={i:0 for i in range(1,11)}

MAL_APIURL=r"http://myanimelist.net/api/anime/search.xml?q={search}"
SCORERE=re.compile(r'''Score Stats''')
VOTESRE=re.compile(r'''\((?P<count>\d+) votes\)''')

OUTPUTLOCATION: pathlib.Path = (filestructure.DATAPATH / "mal").resolve()
STATSARCHIVELOCATION= str(OUTPUTLOCATION) + "votes {malid}.html"
if not OUTPUTLOCATION.exists(): OUTPUTLOCATION.mkdir(parents=True)

class UserData(typing.TypedDict):
    username: str
    password: str
    ## Typed dict does not naturally allow for extra keys
    extras: dict[str, typing.Any]

DEFAULTDATA: UserData ={'username':'','password':'', 'extras': {}}

def createdata():
    with open(MALDATLOCATION,'w') as f:
        json.dump(DEFAULTDATA,f)

def getdata()->UserData:
    with open(MALDATLOCATION,'r') as f:
        return json.load(f)
    
def updatedata(key: str,value: typing.Any):
    current=getdata()
    if key not in current['extras']: raise AttributeError("Invalid AniDB Data Key")
    current['extras'][key]=value
    savedata(current)

def savedata(newdata: UserData):
    current=getdata()
    for key,value in newdata['extras'].items():
        if key in current['extras']:
            current['extras'][key]=value
    with open(MALDATLOCATION,'w') as f:
        json.dump(current,f)

MALDATLOCATION: pathlib.Path=(filestructure.DATAPATH / "extra data" / "mal.data").resolve()
if not MALDATLOCATION.exists(): createdata()
olddata=getdata()
for key,value in DEFAULTDATA.items():
    if key not in olddata:
        olddata[key]=value
savedata(olddata)
del olddata


def getcredentials()-> tuple[str,str]:
    data=getdata()
    return data['username'],data['password']

def updatecredentials(username: str,password: str):
    data=getdata()
    data['username']=username
    data['password']=password
    savedata(data)

def malapi_search(searchvalue: str,username: str|None = None,password: str|None = None)->list[ElementTree.Element]|bool|None:
    if not username or not password:
        username,password=getcredentials()
        if not username or not password: return None
        updateflag=False
    else: updateflag=True
    if not searchvalue: return False
    url=MAL_APIURL.format(search=searchvalue)
    req=requests.get(url, auth=(username,password))
    if req.status_code!=200:
        return False
    if updateflag:
        updatecredentials(username,password)
    root=ElementTree.fromstring(req.text)
    entries=root.findall("entry")
    return entries