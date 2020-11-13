import pandas as pd, urllib
from pandas import DataFrame
from datetime import datetime
from bokeh.plotting import Figure, show, output_file
from bokeh.events import ButtonClick
from bokeh.models import ColumnDataSource, Range1d, CrosshairTool, WheelZoomTool
from bokeh.models import Paragraph, CustomJS, Div, Button
from bokeh.layouts import column, row, layout
from bokeh.document.document import Document
from plotOHLC import requestPSData, createOhlcPlot, hookupFigure
import requests
from CONSTANTS import HOSE_ENDPOINT_PORT, PLOT_WIDTH, PS_ENDPOINT_PORT, OHLC_PLOT_HEIGHT
from CONSTANTS import BUYSELL_PLOT_HEIGHT, VOLUME_PLOT_HEIGHT, LIQUIDITY_ALPHA, SUU_URL, DIV_TEXT_WIDTH

if not "hose_url" in globals():
    hose_url = f'http://localhost:{HOSE_ENDPOINT_PORT}/api/hose-indicators-outbound'
    data = {"volumes": {}, "buySell": {}}
    DEBUG = True
    output_file("/tmp/foo_master_plots.html")


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


def createPlots():
    ######################################## BS Pressure Plot ########################################
    sourceBuySell, sourceVolume = requestHoseData()
    pBuySell = Figure(plot_width=PLOT_WIDTH, plot_height=BUYSELL_PLOT_HEIGHT, name="pltBuySell")
    pBuySell.xaxis.ticker = [8.75, 9, 9.5, 10, 10.5, 11, 11.5, 13, 13.5, 14, 14.5, 14.75]
    pBuySell.xaxis.major_label_overrides = {
        8.5: "8:30", 8.75: "8:45", 9: "9:00", 9.5: "9:30", 10: "10:00",
        10.5: "10:30", 11: "11:00", 11.5: "11:30", 13: "13:00",
        13.5: "13:30", 14: "14:00", 14.5: "14:30", 14.75: "14:45"}
    pBuySell.line(x='index', y='buyPressure', source=sourceBuySell, color='green',
                  legend_label="Tổng đặt mua", name="glyphSellPressure")
    pBuySell.line(x='index', y='sellPressure', source=sourceBuySell, color='red',
                  legend_label="Tổng đặt bán", name="glyphBuyPressure")
    wz = WheelZoomTool(dimensions="width"); pBuySell.add_tools(wz); pBuySell.toolbar.active_scroll = wz
    pBuySell.toolbar.logo = None
    pBuySell.axis[0].visible = False
    pBuySell.legend.location = "top_left"
    pBuySell.legend.click_policy = "hide"
    pBuySell.legend.background_fill_alpha = 0.0

    ######################################## Volume Plot ########################################
    pVolume = Figure(width=PLOT_WIDTH, height=VOLUME_PLOT_HEIGHT, tools="pan, reset",
                     name="pltVolume")
    pVolume.toolbar.logo = None
    wz = WheelZoomTool(dimensions="height"); pVolume.add_tools(wz); pVolume.toolbar.active_scroll = wz
    pVolume.vbar(x='index', top='totalValue', width=1 /60, color='blue',
           source=sourceVolume, fill_alpha=LIQUIDITY_ALPHA, line_alpha=LIQUIDITY_ALPHA,
                 name="glyphTotalValue", legend_label="Thanh khoản toàn tt")
    pVolume.vbar(x='index', top='nnBuy', width=1/1.2/60, color='green', source=sourceVolume
           ,name="glyphNNBuy",  legend_label="NN mua",)
    pVolume.vbar(x='index', top='nnSell', width=1/1.2/60, color='red', source=sourceVolume
           ,name="glyphNNSell", legend_label="NN bán",)
    pVolume.x_range  = pBuySell.x_range
    pVolume.y_range=Range1d(-10, 45)
    pVolume.legend.location = "top_left"
    pVolume.legend.click_policy = "hide"
    pVolume.legend.background_fill_alpha = 0.0

    ######################################### OHLC plot #########################################
    orders, source, pressure = requestPSData()
    plotOhlc = createOhlcPlot(source)
    pCandle, divCandle = hookupFigure(plotOhlc) # "divCustomJS" "pltOHLC" "glyphOHLCSegment"
    pDebug = Paragraph(text=f"""["num_ps_orders": "{len(orders['index'])}"]\n"""
                             """""",
                       width=DIV_TEXT_WIDTH, height=100, name="pDebug")

    ################################# Putting all plots together ################################
    def activation_function():
        pBuySell._document.add_periodic_callback(lambda: updateDoc(pBuySell._document), 500)
        print("Document activated !")

    return pCandle, pBuySell, pVolume, divCandle , activation_function, sourceBuySell, sourceVolume, pDebug


def requestHoseData():
    global data
    res = requests.post(hose_url, json={})
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


def hookUpPlots(pCandle, pBuySell, pVolume, divCandle, divText, crosshairTool, pDebug):
    pCandle.x_range = pBuySell.x_range
    pVolume.x_range = pBuySell.x_range
    pCandle.add_tools(crosshairTool)
    pBuySell.add_tools(crosshairTool)
    pVolume.add_tools(crosshairTool)
    pCandle.xaxis.ticker = [8.75, 9, 9.5, 10, 10.5, 11, 11.5, 13, 13.5, 14, 14.5, 14.75]
    pCandle.xaxis.major_label_overrides = {
        8.5:"8:30", 8.75:"8:45", 9:"9:00", 9.5:"9:30", 10:"10:00",
        10.5:"10:30", 11:"11:00", 11.5:"11:30", 13:"13:00",
        13.5:"13:30", 14:"14:00", 14.5:"14:30", 14.75:"14:45"}
    pBuySell.xaxis.ticker = pCandle.xaxis.ticker
    pVolume.xaxis.ticker = pCandle.xaxis.ticker
    pVolume.xaxis.major_label_overrides = pCandle.xaxis.major_label_overrides

    def btnStart_clicked(event):
        btnStart._document.get_model_by_name("btnStart").label = "Started!"
        # activation_function()

    def activation_function():
        btnStart._document.add_periodic_callback(lambda: updateDoc(btnStart._document), 1000)
        btnStart._document.get_model_by_name("btnStart").label = "Started!"
        btnStart.disabled = True

    pLabel = Paragraph(text="Debug information (please ignore): ", width=pDebug.width, height=10, name="pLabel")
    btnStart = Button(label="Start automatic update", button_type="success", name="btnStart")
    btnStart.on_event(ButtonClick, btnStart_clicked)
    return row(column(pCandle, pBuySell, pVolume), column(divCandle, btnStart, divText, pLabel, pDebug)), \
           activation_function


def makeMasterPlot():
    pCandle, pBuySell, pVolume, divCandle, activation_function, sourceBuySell, sourceVolume, pDebug = createPlots()
    divText = Div(text="Live info here...", width=DIV_TEXT_WIDTH, height=500, height_policy="fixed", name="divText")

    page, activate = hookUpPlots(pCandle, pBuySell, pVolume, divCandle, divText, CrosshairTool(dimensions="both"), pDebug)
    return page, activate, sourceBuySell, sourceVolume


def updateText(doc: Document, sourceBuySell, sourceVolume, psOrders, psDataSource, psPressure, suuData):
    dt = doc.get_model_by_name("divText")

    text = f"Số lượng Hose data point đã scraped được: <br/> {len(sourceBuySell.data['buyPressure'])}<br/>"
    text += f"Số order phái sinh đã match trong ngày: <br/>{len(psOrders['index'])} <br/>"

    text += f"Dư mua: {sourceBuySell.data['buyPressure'][-1]:.2f}  &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"
    text += f"Dư bán: {sourceBuySell.data['sellPressure'][-1]:.2f} <br/>"
    # TODO: add Aggregate nnBuy & nnSell
    # text += f"NN mua(total): {sourceBuySell.iloc[-1]['nnBuy']:.2f} &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"
    # text += f"NN bán(total): {idf.iloc[-1]['nnSell']:.2f} <br/>"

    ############################################ HOSE Indicators ############################################
    currentSource: ColumnDataSource = doc.get_model_by_name("glyphBuyPressure").data_source  # upBuySell
    n_recent_buysell = len(sourceBuySell.data['buyPressure'])
    n_old_buysell = len(currentSource.data['buyPressure'])
    numHoseUpdates = n_recent_buysell - n_old_buysell

    hoseUpdate = {key: sourceBuySell.data[key][n_old_buysell: n_recent_buysell] for key in sourceBuySell.data.keys()}
    currentSource.stream(hoseUpdate)
    text += f"<br/><br/>Số data-points mới cho HOSE chưa được cập nhật: <br/>{numHoseUpdates}<br/>"

    ############################################### Ps Candles ##############################################
    psSource: ColumnDataSource = doc.get_model_by_name("glyphOHLCSegment").data_source
    nPSCandles = len(psSource.data['open'])
    nPSOrders = len(psSource.data['open']) # TODO: fixed this num thing      nPSOrders = psSource.data['num'][0]
    nUnupdatedPSOrders = len(psOrders) - nPSOrders

    text += f"Số data-point mới cho Phái Sinh chưa được cập nhật: <br/> {len(psDataSource.data['index']) - nPSCandles}<br/>"  # update
    if nUnupdatedPSOrders > 0:
        pass

    ############################################### Ps Pressure ##############################################
    if (datetime.now().hour * 60 + datetime.now().minute) > 14 * 60 + 30:
        dt.text = text
        return

    text += f"psBuyPressure: &nbsp&nbsp{ psPressure['psBuyPressure']:.2f} <br/>psSellPressure:&nbsp&nbsp {psPressure['psSellPressure']:.2f} <br/>"
    text += f"buyVolumes: {psPressure['volBuys']} &nbsp&nbsp (total {psPressure['totalVolBuys']}) <br/> "
    text += f"sellVolumes: {psPressure['volSells']} &nbsp&nbsp (total {psPressure['totalVolSells']}) <br/> "

    ############################################### Suu ##############################################
    text += f"""<br/>foreignerBuyVolume: {suuData["foreignerBuyVolume"]}, &nbsp&nbsp  foreignerSellVolume {suuData["foreignerSellVolume"]}<br/> """
    text += f"""totalBidVolume: {suuData["totalBidVolume"]}, &nbsp&nbsp  totalOfferVolume {suuData["totalOfferVolume"]}<br/> """

    dt.text = text


def updateDoc(doc: Document):
    #if DEBUG: print(f"updated {doc}")
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
    psOrders, psDataSource, psPressure = requestPSData()
    sourcePs = doc.get_model_by_name("glyphOHLCSegment").data_source
    updateSource(sourcePs, psDataSource)

    ######################### Text Display #########################
    suuData = None
    updateText(doc, sourceBuySell, sourceVolume, psOrders, psDataSource, psPressure, suuData = fetchSuuData())

# page, _, _, _ = makeMasterPlot()
# show(page)





