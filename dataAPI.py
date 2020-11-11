from bokeh.models import ColumnDataSource
from CONSTANTS import SUU_URL, HOSE_URL, PS_ENDPOINT_PORT, PS_URL
import requests, json, pandas as pd

if not "DEBUG" in globals():
    DEBUG = False
    data = {"volumes": {}, "buySell": {}}

def requestHoseData():
    global data
    res = requests.post(HOSE_URL, json={})
    data = res.json()
    dicBS = {key: data['buySell'][key] for key in ['buyPressure', 'index', 'sellPressure']}
    sourceBuySell = ColumnDataSource(dicBS)  # ['buyPressure', 'index', 'sellPressure', 'time']

    dicVol = {key: data['volumes'][key] for key in ['index', 'nnBuy', 'nnSell', 'totalValue']}
    sourceVolume = ColumnDataSource(dicVol)  # ['index', 'nnBuy', 'nnSell', 'time', 'totalValue']

    return sourceBuySell, sourceVolume


def fetchSuuData():
    import urllib, json, pandas as pd
    with urllib.request.urlopen(SUU_URL) as url:
        data = json.loads(url.read().decode())
    return data


def requestPSData():
    global data
    res = requests.post(PS_URL, json={})
    data = res.json() # ['ohlcDataDic', 'orders', 'psPressure']
    #if DEBUG: print(len(data['ohlcDataDic']['open']), len(data['orders']['index']))
    return data['orders'], ColumnDataSource(data['ohlcDataDic']), data['psPressure']