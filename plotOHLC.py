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
from collections import OrderedDict
import requests
from CONSTANTS import MARKET_TRADING_DATE, PS_PLOT_HEIGHT, PLOT_WIDTH, PS_ENDPOINT_PORT, OHLC_PLOT_HEIGHT

DEBUG = False
CANDLE_WIDTH = 0.7
ps_url = f'http://localhost:{PS_ENDPOINT_PORT}/ps-pressure-out'

data = None


def  createDFfromOrderBook(psOrders, DATE=MARKET_TRADING_DATE):
    index = pd.date_range(f'{DATE} 09:00:00', f'{DATE} 14:45:59', freq='S')
    prices = [None] * len(index)
    volumes = [None] * len(index)
    last = -1
    for order in psOrders:
        i = (order["hour"] - 9) * 3600 + order["minute"] * 60 + order["second"]  # MARKETHOUR
        if last < i: last = i
        prices[i] = order['price']
        volumes[i] = order['volume']

    return pd.Series(prices[:last], index=index[:last]), pd.Series(volumes[:last], index=index[:last])


def ohlcFromPrices(priceSeries, volumeSeries, sampleSize='1Min'):
    resampled = priceSeries.resample(sampleSize).agg(  # series.resample('60s')
        OrderedDict([
            ('open', 'first'),
            ('high', 'max'),
            ('low', 'min'),
            ('close', 'last'),]))
    dic = {}
    for key in ['open', 'high', 'low', 'close']:
        dic[key] = resampled[key].fillna(method='pad').values
    dic['date'] = list(map(lambda x: x[1], resampled.index[:len(resampled['open'])]))
    dic['vol'] = volumeSeries.resample('1Min').agg(sum).values
    df = pd.DataFrame.from_dict(dic).set_index('date')
    return df, dic, resampled


def filterOutNonTradingTime(df, num=None):
    def isValid(t):
        return start <= t <= lunch or noon <= t <= end
    start = pd.Timestamp(year=df.index[0].year, month=df.index[0].month, day=df.index[0].day, hour=9 , minute=0 , freq='T')
    lunch = pd.Timestamp(year=df.index[0].year, month=df.index[0].month, day=df.index[0].day, hour=11, minute=29, freq='T')
    noon =  pd.Timestamp(year=df.index[0].year, month=df.index[0].month, day=df.index[0].day, hour=13, minute=0 , freq='T')
    end =   pd.Timestamp(year=df.index[0].year, month=df.index[0].month, day=df.index[0].day, hour=14, minute=45, freq='T')
    # return [t for t in df.index if isValid(t)]
    # return [ start <= df.index]
    if num is not None: df['num'] = [num] * len(df)
    res = df[list(map(isValid, df.index))]

    return res


def createBuySellPlot(source):
    pBuySell = Figure(width=PLOT_WIDTH, height=PS_PLOT_HEIGHT,tools="pan, reset,ywheel_zoom , box_zoom",
                      name='pltBuySell')


    wz = WheelZoomTool(dimensions="width"); pBuySell.add_tools(wz); pBuySell.toolbar.active_scroll = wz
    pBuySell.toolbar.logo = None

    pBuySell.line(x='index', y='buyPressure', source=source, color='green',
                  legend_label="Tổng đặt mua", name="glyphSellPressure")
    pBuySell.line(x='index', y='sellPressure', source=source, color='red',
                  legend_label="Tổng đặt bán", name="glyphBuyPressure")
    pBuySell.axis[0].visible = False
    pBuySell.legend.location = "top_left"
    pBuySell.legend.click_policy = "hide"
    pBuySell.legend.background_fill_alpha = 0.0

    return pBuySell


def createColumnDataSource(ddf):
    dic = {key: ddf[key].values for key in ddf.columns}
    dic['index'] = list(map(lambda t: (t.hour * 3600 + t.minute * 60 + t.second) / 3600, ddf.index))
    source = ColumnDataSource(dic)
    return source


def plotPsTrimmed(source, OHLC_PLOT_HEIGHT=OHLC_PLOT_HEIGHT):          # Index is rather meaningless 'i'
    from bokeh.plotting import figure
    p = figure(tools= "pan,box_zoom,reset,save",
               plot_width=PLOT_WIDTH,
               plot_height=OHLC_PLOT_HEIGHT,
               title = "VN30F1M Future contract",
               name = "pltOHLC")

    p.segment('index', "high", 'index', 'low', source=source, color="black", name="glyphOHLCSegment")
    p.vbar(x='index', width=CANDLE_WIDTH/60, top='open', bottom='close', source=source,
           fill_color="green", line_color="black", line_width=0.4, name="glyphOHLCGreen")
    p.vbar('index', CANDLE_WIDTH/60, 'open', 'close', source=source, line_width=0.4,
           fill_color="red", line_color="black", alpha='redCandleAlpha', name="glyphOHLCRed" )

    p.add_tools(CrosshairTool(dimensions="both"))
    wheel_zoom = WheelZoomTool()
    p.add_tools(wheel_zoom)
    p.toolbar.active_scroll = wheel_zoom
    return p


def createOhlcSource(df):
    redCandleAlpha = [0] * len(df)
    for i in range(len(df)):
        if df.open.values[i] > df.close.values[i]: redCandleAlpha[i] = 1
    df['redCandleAlpha'] = redCandleAlpha
    return createColumnDataSource(df)


def requestPSData():
    global data
    res = requests.post(ps_url, json={})
    data = res.json() # ['ohlcDataDic', 'orders', 'psPressure']
    num_datapoints = len(data['orders']['index'])
    num_candles = len(data['ohlcDataDic']['open'])
    #if DEBUG: print(num_candles, num_datapoints)
    print(data.keys())
    return data['orders'], data['ohlcDataDic'], data['psPressure']


from bokeh.models import  ColumnDataSource
output_file("/tmp/show.html")
orders, sourceDic, pressure = requestPSData()
source = ColumnDataSource(sourceDic)
p = plotPsTrimmed(source)
show(p)


