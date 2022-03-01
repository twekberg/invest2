"""
Render the stock charts for one or more stocks.
"""

from app.db.trade_confirmation import TradeConfirmation
from app.db.trade_history import TradeHistory
from app.db.account import Account
from app.db import database
from app.pdf_chart import render_chart

import argparse
from datetime import datetime, timedelta
import calendar
import logging
import os
import os.path
import sqlite3
import re


log = logging.getLogger(__name__)

db_file = '../investments.db'


def build_parser():
    parser = argparse.ArgumentParser(description = globals()['__doc__'],
                                     formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.usage = 'python -m app.commands.render_charts [options]'
    parser.add_argument('stocks', nargs='*',
                        default=None,
                        help='One or more stocks. Default: all stocks')
    parser.add_argument('-o', '--out_dir',
                        default='../charts',
                        help='Directory to write the chart PDFs. '
                        'Default: %(default)s.')
    return parser



class RenderChart(object):
    def __init__(self, args, accounts=None):
        self.args = args
        th = TradeHistory()
        if accounts:
            self.accounts = accounts
        else:
            self.accounts = Account()
        self.trade_histories = database.databases['trade_history']
        # The current stock have this history_date
        self.last_history_date = max([trade_hist['history_date']
                                      for trade_hist in self.trade_histories.rows])

    def report(self):
        """
        Render charts for all stocks, or the ones specified.
        If args.out_dir is none, collect the charts to render by the caller.
        """
        charts = []
        for (account, symbol) in self.get_open_stocks():
            if self.args.stocks:
                if symbol in self.args.stocks:
                    th = self.trade_histories.fetch(account, symbol)
                else:
                    th = None
            else:
                th = self.trade_histories.fetch(account, symbol)
            if th:
                data1 = []
                data2 = []
                for h in th:
                    # Convert date to a float yyyy.yearFraction.
                    hd = h['history_date']
                    # Create a datetime, with the year and month from
                    # hd, and the end of month day (from
                    # calendar.monthrange).  With timetuple one can
                    # get the day of the year, and the convert to a
                    # fraction.  Use 366 to account for leap years
                    # that have that many days.
                    frac = ((datetime(hd.year, hd.month, calendar.monthrange(hd.year, hd.month)[1])).timetuple().tm_yday - 1) / 366.0
                    data1.append((hd.year + frac, h['current_price']))
                    data2.append((hd.year + frac, h['unit_cost']))
                #print('\n'.join(sorted(['%d/%2d, %8.2f' % (int(x), (x % 1) * 12 + 1,y) for (x,y) in data1])))


                if self.args.out_dir:
                    filename = os.path.join(self.args.out_dir, '%s.pdf' % (symbol.replace('/', '-')))
                else:
                    filename = None
                chart = render_chart(filename,
                                     '%s %s' % (symbol,
                                                self.accounts.account_name_lookup(h['account'])),
                                     [data1, data2], ('price', 'cost'))
                if not filename:
                    charts.append(chart)
        return charts


    def get_open_stocks(self):
        """
        Get list of all open stocks. We don't care about the ones
        that are already sold.
        Returns a list of (account, symbol) tuples.
        """
        stocks = []
        for trade_hist in self.trade_histories.rows:
            if trade_hist['history_date'] == self.last_history_date:
                stocks.append((trade_hist['account'], (trade_hist['symbol'])))
        stocks = sorted(stocks)
        print('# stocks', len(stocks))
        prev_account = None
        for (account, symbol) in stocks:
            if prev_account != account:
                count = 0
            count += 1
            print(count, account, symbol)
            prev_account = account
        return stocks


def action(args):
    """
    Load the parts in the spreadsheet
    """
    r = RenderChart(args)
    r.report()

    
if __name__ == '__main__':
    action(build_parser().parse_args())
