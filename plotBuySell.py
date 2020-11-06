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
from CONSTANTS import HOSE_ENDPOINT_PORT, PLOT_WIDTH, PS_ENDPOINT_PORT

hose_url = f'http://localhost:{HOSE_ENDPOINT_PORT}/api/hose-indicators-outbound'
data = {"volumes": {}, "buySell": {}}
DEBUG = True


def updateSource(sourceOld, sourceNew):
    #sourceOld.data = dict(sourceNew.data)
    dic = {}
    i = len(sourceOld.data[list(sourceOld.data.keys())[0]]) - 1
    for key in sourceOld.data.keys():
        dic[key] = [[i, sourceNew.data[key][i]]]
    #print(dic)
    sourceOld.patch(dic)

    j = len(sourceNew.data[list(sourceNew.data.keys())[0]])
    if j > i:
        stream = {}
        for key in sourceNew.data.keys():
            stream[key] = sourceNew.data[key][i + 1: j]
        sourceOld.stream(stream)


def updateDoc(doc):
    #if DEBUG: print(f"updated {doc}")
    print("updated")
    sourceBuySell, sourceVolume = requestHoseData()

    ###################### Hose Buy, Sell #######################

    sourceBS = doc.get_model_by_name("glyphSellPressure").data_source
    lsource = len(sourceBS.data['index'])
    lnew = len(sourceBuySell.data['index'])
    if lnew > lsource:
        hoseUpdate = {key: sourceBuySell.data[key][lsource: lnew] for key in sourceBuySell.data.keys()}
        sourceBS.stream(hoseUpdate)

    ################# Liquidity *  nnBuy, nnSell #################

    sourceVol = doc.get_model_by_name("glyphTotalValue").data_source
    updateSource(sourceVol , sourceVolume) #update

    ######################### ohlcCandles #########################

    return

def createPlot():
    sourceBuySell, sourceVolume = requestHoseData()
    print(sourceBuySell)
    p = Figure(plot_width=PLOT_WIDTH, plot_height=600, name="pltBuySell")
    p.xaxis.ticker = [8.75, 9, 9.5, 10, 10.5, 11, 11.5, 13, 13.5, 14, 14.5, 14.75]
    p.xaxis.major_label_overrides = {
        8.5: "8:30", 8.75: "8:45", 9: "9:00", 9.5: "9:30", 10: "10:00",
        10.5: "10:30", 11: "11:00", 11.5: "11:30", 13: "13:00",
        13.5: "13:30", 14: "14:00", 14.5: "14:30", 14.75: "14:45"}
    p.line(x='index', y='buyPressure', source=sourceBuySell, color='green', name="glyphBuyPressure")
    p.line(x='index', y='sellPressure', source=sourceBuySell, color='red', name="glyphSellPressure")
    wz = WheelZoomTool(dimensions="height"); p.add_tools(wz); p.toolbar.active_scroll = wz

    pvol = Figure(plot_width=1200, plot_height=200, name="pltBuySell")
    p.vbar(x='index', top='totalValue', width=1 / 1.2 / 60, color='blue',
           source=sourceVolume, fill_alpha=0.3, name="glyphTotalValue")
    p.vbar(x='index', top='nnBuy', width=1/1.2/60, color='green', source=sourceVolume
           ,name="glyphNNBuy")
    p.vbar(x='index', top='nnSell', width=1/1.2/60, color='red', source=sourceVolume
           ,name="glyphNNSell")
    pvol.x_range  = p.x_range

    def activation_function():
        p._document.add_periodic_callback(lambda: updateDoc(p._document), 500)
        print("Document activated !")

    return column(p, pvol), activation_function, sourceBuySell, sourceVolume


def requestHoseData():
    global data
    res = requests.post(hose_url, json={})
    data = res.json()
    dicBS = {key: data['buySell'][key] for key in ['buyPressure', 'index', 'sellPressure']}
    sourceBuySell = ColumnDataSource(dicBS)  # ['buyPressure', 'index', 'sellPressure', 'time']

    dicVol = {key: data['volumes'][key] for key in ['index', 'nnBuy', 'nnSell', 'totalValue']}
    sourceVolume = ColumnDataSource(dicVol)  # ['index', 'nnBuy', 'nnSell', 'time', 'totalValue']

    return sourceBuySell, sourceVolume

















