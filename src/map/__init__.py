from src.map.MAPController import MAPController
from src.lib.rest_server import RESTServer

if __name__ == '__main__':
    m = MAPController()
    RESTServer(m.create_app()).run()
    m.run()
