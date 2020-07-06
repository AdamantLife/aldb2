## Builtin
import json
import re
import xml.etree.ElementTree as ElementTree
## Third Party
import requests
## This Module
from aldb2 import filestructure



MALRATINGSDICT={i:0 for i in range(1,11)}

MAL_APIURL=r"http://myanimelist.net/api/anime/search.xml?q={search}"
SCORERE=re.compile('''Score Stats''')
VOTESRE=re.compile('''\((?P<count>\d+) votes\)''')

OUTPUTLOCATION= (filestructure.DATAPATH / "mal").resolve()
STATSARCHIVELOCATION= str(OUTPUTLOCATION) + "votes {malid}.html"
if not OUTPUTLOCATION.exists(): OUTPUTLOCATION.mkdir(parents=True)

DEFAULTDATA={'username':'','password':''}

def createdata():
    with open(MALDATLOCATION,'w') as f:
        json.dump(DEFAULTDATA,f)

def getdata():
    with open(MALDATLOCATION,'r') as f:
        return json.load(f)
def updatedata(key,value):
    current=getdata()
    if key not in current: raise AttributeError("Invalid AniDB Data Key")
    current[key]=value
    savedata(current)

def savedata(newdata):
    current=getdata()
    out=dict(current)
    for key,value in newdata.items():
        if key in current:
            out[key]=value
    with open(MALDATLOCATION,'w') as f:
        json.dump(out,f)

MALDATLOCATION=(filestructure.DATAPATH / "extra data" / "mal.data").resolve()
if not MALDATLOCATION.exists(): createdata()
olddata=getdata()
for key,value in DEFAULTDATA.items():
    if key not in olddata:
        olddata[key]=value
savedata(olddata)
del olddata


def getcredentials():
    data=getdata()
    return data['username'],data['password']
def updatecredentials(username,password):
    data=getdata()
    data['username']=username
    data['password']=password
    savedata(data)

def malapi_search(searchvalue,username=None,password=None):
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