import time
import threading
from typing import Dict
import pandas as pd
from .utils import get_account_values


class MonitorConsole:
    def __init__(self, strategy, quote, delay_secs=5):
        self.strategy = strategy
        self.quote = quote
        self.delay_secs = delay_secs

    def start(self):
        thread = threading.Thread(target=self.process)
        thread.start()

    def process(self):
        account_values: Dict[float, pd.Dataframe] = {}
        while True:
            print(pd.Timestamp.now(tz="UTC"))
            print(time.time())
            # event.wait()
            # event.clear()

            df = get_account_values(self.strategy.interface, self.quote)
            account_values[time.time()] = df

            print(df)
            print(df[["available_amount", "hold_amount"]].sum())
            print()
            time.sleep(self.delay_secs)
            # time.sleep(60 * 60 * 4)
            # event.set()
