from bokeh.server.server import Server
from bokeh.util.browser import view
from bokeh.document.document import Document
from bokeh.application.handlers import FunctionHandler
from bokeh.application.application import  Application
from commonOld import threading_func_wrapper
from plotBuySell import createPlots, requestHoseData, makeMasterPlot, fetchSuuData
from bokeh.layouts import column
from bokeh.models import ColumnDataSource


BOKEH_PORT = 5009
if "docs" not in globals():
    docs = []
    page = column()
    sourceBuySell: ColumnDataSource = ColumnDataSource({ # ['buyPressure', 'index', 'sellPressure', 'time']
        'buyPressure':[],
        'sellPressure':[],
        'index': [], })
    sourceVolume:ColumnDataSource = ColumnDataSource({ #  ['index', 'nnBuy', 'nnSell', 'time', 'totalValue']
        'index': [],
        'nnBuy': [],
        'nnSell': [],
        'totalValue': [],})


def attachDocToServer(doc : Document):
    global page, sourceVolume, sourceBuySell
    page, activate, sourceBuySell, sourceVolume = makeMasterPlot()
    doc.add_root(column(page))
    docs.append(doc)
    activate()


if __name__ == "__main__":
    s = Server({'/': Application(FunctionHandler(attachDocToServer))},
               num_proc=16,
               port=BOKEH_PORT,
               allow_websocket_origin=["*"])
    s.start()
    threading_func_wrapper(s.io_loop.start, delay=0.01)
    threading_func_wrapper(lambda: view(f"http://localhost:{BOKEH_PORT}"), 0.5)

