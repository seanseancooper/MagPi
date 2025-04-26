from src.gps.GPSRetriever import GPSRetriever
from src.gps.GPSController import GPSController
from src.lib.rest_server import RESTServer

if __name__ == '__main__':
    g = GPSController()
    RESTServer(g.create_app()).run()
    g.run()
