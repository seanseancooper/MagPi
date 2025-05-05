from src.trx.TRXController import TRXController
from src.net.FlaskRESTServer import RESTServer

if __name__ == '__main__':
    t = TRXController()
    RESTServer(t.create_app()).run()
    t.run()
