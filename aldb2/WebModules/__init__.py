## Builtin
import datetime
import urllib.request as urequest

EST = datetime.timezone(datetime.timedelta(hours = -5))
JST = datetime.timezone(datetime.timedelta(hours = 9))

def getseriespage(anime):
    '''Fetches and reads homepage into memory'''
    print('Getting Page for:', anime.title)
    url=anime.homepage
    html=urequest.urlopen(url).read()
    print('>>> Page Recieved')
    return html