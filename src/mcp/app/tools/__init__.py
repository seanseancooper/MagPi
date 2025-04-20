from .get_signal_data import get_signal_data
from .get_worker_metadata import get_worker_metadata
import openai

import time

last_call_time = 0
MIN_INTERVAL = 30  # seconds

def call_openai_throttled(prompt):
    global last_call_time
    now = time.time()
    if now - last_call_time < MIN_INTERVAL:
        wait = MIN_INTERVAL - (now - last_call_time)
        print(f"Throttled. Waiting {wait:.2f}s")
        time.sleep(wait)
    last_call_time = time.time()
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
