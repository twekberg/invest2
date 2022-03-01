"""
Show active stock position and its age.
"""

from app.db.trade_confirmation import TradeConfirmation
from app.db import database


import argparse
from datetime import datetime, timedelta
import logging
import os
import sqlite3
import re


LOG = logging.getLogger(__name__)

db_file = '../investments.db'

def build_parser():
    parser = argparse.ArgumentParser(description = globals()['__doc__'],
                                     formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.usage = 'python -m app.commands.stock_age [options]'
    parser.add_argument('-f', '--format', 
                        default='csv',
                        help='Format of the output: csv or html. '
                        'Default: %(default)s.')
    return parser


class App(object):
    def __init__(self, args):
        self.args = args
        self.db_open()
        self.trade_confirmations = database.fetch_all('trade_confirmation')
        # Retrieve only the date part.
        for tc in self.trade_confirmations:
            tc['trade_date'] = database.fix_date(tc['trade_date'])



    def db_open(self):
        self.con = sqlite3.connect(db_file)
        self.cur = self.con.cursor()


    def db_commit(self):
        self.con.commit()


    def db_close(self):
        self.con.close()

    def is_leap(self, year):
        if (year % 4) == 0:
            if (year % 100) == 0:
                if (year % 400) == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False


    def n_days(self, year):
        return 366 if self.is_leap(year) else 365


    def header_cell(self, contents):
        print("<th>%s</th>" % (contents,))


    def cell(self, contents, align_right=False):
        print("<td%s>%s</td>" % (' align="right"' if align_right else '', contents,))


    def cell_amount(self, dollars):
        if dollars >= 0:
            self.cell("%9.2f" % dollars, True)
        else:
            self.cell("(%9.2f)" % dollars, True)


    def report(self):
        # Note all stocks which have been already sold: close positions.
        # Collect the stock that were sold for the year.
        sales = []
        for tc in self.trade_confirmations:
            if not tc['is_buy'] and tc['trade_type'] == 'stock':
                sales.append(tc)
            # Initialize
            tc['open'] = True
        # Match the sales with a purchase.
        bots = []
        for sale in sales:
            found = False
            for tc in self.trade_confirmations:
                if sale['symbol'] == tc['symbol'] and tc['is_buy'] and tc['trade_type'] == 'stock':
                    found = True
                    tc['open'] = False
                    sale['open'] = False
                    bots.append(tc)
                    break
            if not found:
                print('Unable to find matching purchase for %s' % (sale['symbol'],))
                exit()
        for tc in sorted(self.trade_confirmations, key=lambda x: x['symbol']):
            if tc['open']:
                term = 'long ' if (datetime.now() - tc['trade_date']).days >= 365 else 'short'
                print(term, tc['symbol'], tc['account'], tc['n_shares'], tc['trade_date'])


def action(args):
    """
    Load the parts in the spreadsheet
    """
    app = App(args)
    app.report()
    app.db_close()


if __name__ == '__main__':
    action(build_parser().parse_args())
