"""
Details regarding the trade confirmation records.
"""


import app.db


my_table = 'trade_confirmation'


class TradeConfirmation(object):
    def __init__(self):
        self.database = inv.db.database
        self.rows = self.database.fetch_all(my_table)
        self.database.add(my_table, self)


    def fetch(self, symbol):
        """
        Fetch the rows that related to the stock symbol. Sort by trade_date.
        """
        rows = []
        for row in self.rows:
            row['trade_date'] = self.database.fix_date(row['trade_date'])
            if row['symbol'] == symbol:
                rows.append(row)
        return sorted(rows, key=lambda x: x['trade_date'])
