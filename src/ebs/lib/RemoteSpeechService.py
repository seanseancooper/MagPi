from GenericSpeechService import SpeechService






class RemoteSpeechService(SpeechService):
    """ Remote implementation of speech using local Google Speech,
     or other online, network connected service. Notably, this would have a
      URL, a key, etc.

      this will be implemented later in an vendor specific subclass.
      Not on critical path due to anticipated disconnected environment"""

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c







