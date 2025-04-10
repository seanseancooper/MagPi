from src.mot.MOTController import MOTController
from src.lib.rest_server import RESTServer

if __name__ == '__main__':
    m = MOTController()
    RESTServer(m.create_app()).run()
    m.run()
