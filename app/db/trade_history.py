"""
Details regarding the trade history
"""


import app.db


my_table = 'trade_history'


class TradeHistory(object):
    def __init__(self):
        self.database = app.db.database
        self.rows = self.database.fetch_all(my_table)
        self.database.add(my_table, self)


    def fetch(self, account, symbol):
        """
        Fetch the rows in an account that relate to a stock symbol.
        Sort by history_date.
        """
        rows = []
        for row in self.rows:
            if row['symbol'][0] == '#':
                # Ignore commentary.
                continue
            row['history_date'] = self.database.fix_date(row['history_date'])
            # Add computed values
            row['unit_delta'] = row['current_price'] - row['unit_cost']
            row['cum_delta'] = row['unit_delta'] * row['n_shares']
            if row['account'] == account and row['symbol'] == symbol:
                rows.append(row)
        return sorted(rows, key=lambda x: x['history_date'])
