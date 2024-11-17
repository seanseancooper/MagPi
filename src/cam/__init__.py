from src.cam.CAMController import CAMController
from src.lib.rest_server import RESTServer as RESTServer

if __name__ == '__main__':
    c = CAMController()
    RESTServer(c.create_app()).run()
    c.run()
