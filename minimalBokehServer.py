from bokeh.server.server import Server
from bokeh.util.browser import view
from bokeh.document.document import Document
from bokeh.application.handlers import FunctionHandler
from bokeh.application.application import  Application
from commonOld import threading_func_wrapper
from plotBuySell import createPlot, requestData
from bokeh.layouts import column


BOKEH_PORT = 5010
if "docs" not in globals(): docs = []

def attachDocToServer(doc : Document):
    p, activate = createPlot()
    doc.add_root(column(p))
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


#%%
sourceBuySell, sourceVolume = requestData()
