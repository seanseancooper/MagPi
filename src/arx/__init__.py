from src.arx.ARXController import ARXController
from src.lib.rest_server import RESTServer as RESTServer

if __name__ == '__main__':
    a = ARXController()
    RESTServer(a.create_app()).run()
    a.run()
