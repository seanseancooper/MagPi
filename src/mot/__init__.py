from src.mot.MOTController import MOTController
from src.lib.rest_server import RESTServer as RESTServer

if __name__ == '__main__':
    m = MOTController()
    RESTServer(c.create_app()).run()
    m.run()
