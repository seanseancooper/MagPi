from GenericSpeechService import SpeechService





class ESpeakNGSpeechService(SpeechService):
    """ ESpeakNG specific implementation of speech using local espeak command.
     This is targeted to GNU platforms and is a secondary focus due to
     anticipated disconnected environment """

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c







