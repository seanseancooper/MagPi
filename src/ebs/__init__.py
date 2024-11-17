from src.ebs.EBSController import EBSController
from src.lib.rest_server import RESTServer as RESTServer

if __name__ == '__main__':
    e = EBSController()
    RESTServer(e.create_app()).run()
    e.run()
