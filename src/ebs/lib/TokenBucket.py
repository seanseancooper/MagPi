import time
import logging.handlers

wifi_logger = logging.getLogger('tokenbucket')


class TokenBucket:

    def __init__(self, tokens, time_unit, debug=False):
        self.tokens = tokens
        self.time_unit = time_unit
        self.DEBUG = debug
        self.bucket = tokens
        self.last_check = time.time()

    def __repr__(self):
        return f"tokens:{self.tokens} time_unit:{self.time_unit} bucket:{self.bucket} last_check:{self.last_check}"

    def handle(self, message):

        if message:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            print(f"[{__name__}]: TokenBucket contains: {self.bucket}: {time_passed}")

            # DBUG: convert self.bucket to a timedelta and move this internal to WifiScanner
            self.bucket = self.bucket + time_passed * (self.tokens / self.time_unit)

            if self.bucket > self.tokens:
                self.bucket = self.tokens

            if self.bucket < 1:
                print(f"[{__name__}]: TokenBucket message dropped: {str(message)} bucket contains: {self.bucket}")
                return None
            else:
                self.bucket = self.bucket - 1
                print(f"[{__name__}]: TokenBucket message returned: {str(message)} bucket contains: {self.bucket}")
                return message
