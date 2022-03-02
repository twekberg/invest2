"""
Details regarding the trade activity
"""


import app.db
from app.db.trade_confirmation import TradeConfirmation


my_table = 'activity'


class Activity(object):
    def __init__(self):
        self.database = app.db.database
        self.rows = self.database.fetch_all(my_table)
        self.database.add(my_table, self)
        

    def fetch(self, symbol):
        """
        Fetch the rows that related to the stock symbol. Sort by activity_date.
        """
        rows = []
        for row in self.rows:
            row['activity_date'] = self.database.fix_date(row['activity_date'])
            if row['symbol'] == symbol:
                rows.append(row)
        return sorted(rows, key=lambda x: x['activity_date'])


    def fetch_activity(self, symbol, activity):
        """
        Fetch the rows that related to the stock symbol. Sort by activity_date.
        """
        rows = []
        for row in self.rows:
            row['activity_date'] = self.database.fix_date(row['activity_date'])
            if row['symbol'] == symbol and row['activity_type'] == activity:
                rows.append(row)
        return sorted(rows, key=lambda x: x['activity_date'])
