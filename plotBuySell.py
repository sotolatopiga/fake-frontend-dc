import pandas as pd
from datetime import datetime
from commonOld import tik, tok
from bokeh.plotting import Figure, show, output_file
from bokeh.models import ColumnDataSource, Range1d, CrosshairTool, WheelZoomTool, CustomJS, Div
from bokeh.layouts import column, row, layout
from pandas import DataFrame
from os import listdir
from os.path import isfile, join
from flask import jsonify
import json, pickle
import time
import requests
from CONSTANTS import ENDPOINT_PORT

url = f'http://localhost:{ENDPOINT_PORT}/api/hose-indicators-outbound'
data = {"volumes": {}, "buySell": {}}
DEBUG = True

def update(doc):
    print(f"updated {doc}")
    source = doc.get_model_by_name("glyphSellPressure").data_source
    sourceBuySell, sourceVolume = requestData()
    lsource = len(source.data['index'])
    lnew = len(sourceBuySell.data['index'])
    if lnew > lsource:
        hoseUpdate = {key: sourceBuySell.data[key][lsource: lnew] for key in sourceBuySell.data.keys()}
        source.stream(hoseUpdate)
    #hoseUpdate = {key:sourceBuySell.data[key][oldCount: recent] for key in sourceBuySell.data.keys()}
    # currentSource.stream(hoseUpdate)
    return

def createPlot():
    sourceBuySell, sourceVolume = requestData()
    print(sourceBuySell)
    p = Figure(plot_width=1200, plot_height=600, name="pltBuySell")
    p.line(x='index', y='buyPressure', source=sourceBuySell, color='green', name="glyphBuyPressure")
    p.line(x='index', y='sellPressure', source=sourceBuySell, color='red', name="glyphSellPressure")
    def activation_function():
        p._document.add_periodic_callback(lambda: update(p._document), 500)
        print("Document activated !")
    return p, activation_function


def requestData():
    global data
    res = requests.post(url,json={})
    data = res.json()
    dic = {key: data['buySell'][key] for key in ['buyPressure', 'index', 'sellPressure']}
    sourceBuySell = ColumnDataSource(dic)  # ['buyPressure', 'index', 'sellPressure', 'time']
    if DEBUG: print(sourceBuySell.data['index'][-1])

    sourceVolume = ColumnDataSource(data['volumes'])  # ['index', 'nnBuy', 'nnSell', 'time', 'totalValue']
    if DEBUG: print(sourceVolume.data['index'][-1])

    return sourceBuySell, sourceVolume


#p, active = createPlot(); show(p)




















