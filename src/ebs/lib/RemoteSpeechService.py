from SpeechService import SpeechService






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


# def synthesize_text():
#     """Synthesizes speech from the input string of text."""
#     from google.cloud import texttospeech
#
#     text = "Hello there."
#     client = texttospeech.TextToSpeechClient()
#
#     input_text = texttospeech.SynthesisInput(text=text)
#
#     # Note: the voice can also be specified by name.
#     # Names of voices can be retrieved with client.list_voices().
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US",
#         name="en-US-Standard-C",
#         ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
#     )
#
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )
#
#     response = client.synthesize_speech(
#         request={"input": input_text, "voice": voice, "audio_config": audio_config}
#     )
#
#     # The response's audio_content is binary.
#     with open("output.mp3", "wb") as out:
#         out.write(response.audio_content)
#         print('Audio content written to file "output.mp3"')
#
#




