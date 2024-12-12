



class Bugger():

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    # Bugger: Uses ARX component to listen for and operationalize
    # spoken word commands from a library (project-keyword-spotter).
    # The library will use the Coral adapter to run inference on MFCC
    # slices in real time.
