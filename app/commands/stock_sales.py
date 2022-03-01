"""
Show stock sells detail by year.

Outputs HTML to view in a browser for the following:
 1040 Schedule B part II
 Form 8949
"""

from ..db.trade_confirmation import TradeConfirmation
from ..db.account import Account
from ..db.activity import Activity
from ..db import database

import argparse
from datetime import datetime
import logging
import sys


LOG = logging.getLogger(__name__)

# Constants used to access trade histories.
BUY = 1
SELL = 0

def build_parser():
    """
    Collect parameters.
    """
    parser = argparse.ArgumentParser(description = globals()['__doc__'],
                                     formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.usage = 'python -m app.commands.stock_sales [options]'
    parser.add_argument('-y', '--year', type=int,
                        default=datetime.now().year - 1,
                        help='The year to produce the report for. '
                        'Default: %(default)s.')
    parser.add_argument('-d', '--debug', default=False,
                        action='store_true',
                        help='Output debug info.'
                        ' Default: %(default)s.')
    parser.add_argument('-f', '--forms', nargs='*',
                        choices=('schedule-b', '8949', 'all'),
                        default='all',
                        help='Form to generate HTML for.'
                        ' Default: %(default)s.')
    return parser


class App(object):
    """
    Render reports for taxes. Used for data only, not submission.
    """
    def __init__(self, args):
        self.args = args
        self.account = Account()
        self.activity = Activity()
        self.trade_confirmations = database.fetch_all('trade_confirmation')
        for trade_c in self.trade_confirmations:
            trade_c['trade_date'] = database.fix_date(trade_c['trade_date'])
        for act in self.activity.rows:
            act['activity_date'] = database.fix_date(act['activity_date'])
        # As defined by the IRS.
        self.capital_asset = ['bond', 'preferred stock', 'stock']
        self.do_8949 = '8949' in args.forms or 'all' in args.forms
        self.do_schedule_b = 'schedule-b' in args.forms or 'all' in args.forms


    def is_leap(self, year):
        """
        Return True if this year is a leap year, False otherwise.
        """
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
        """
        Return the number of days in this year.
        """
        return 366 if self.is_leap(year) else 365


    def header_cell(self, contents):
        """
        Output a header table cell.
        """
        print("<th>%s</th>" % (contents,))


    def cell(self, contents, align_right=False):
        """
        Output a normal table cell.
        """
        print("<td%s>%s</td>" % (
            ' align="right"' if align_right else '', contents,))


    def cell_amount(self, dollars):
        """
        Output a normal table cell containing a dollar amount.
        """
        if dollars >= 0:
            self.cell("%9.2f" % dollars, True)
        else:
            self.cell("(%9.2f)" % (-dollars,), True)


    def collect_trades(self):
        """
        Match each SELL with its corresponding BUY. Return the
        transaction history for each symbol+account.
        """
        # Key is the symbol+account
        # value is dict, key=is_buy, value=list of tcs
        stock_histories = dict()
        for trade_c in self.trade_confirmations:
            if trade_c['trade_type'] in self.capital_asset:
                key = self.stock_history_key(trade_c)
                if key not in stock_histories:
                    stock_histories[key] = {BUY: [], SELL: []}
                stock_histories[key][trade_c['is_buy']].append(trade_c)
        if self.args.debug:
            for key in sorted(stock_histories.keys()):
                sys.stderr.write('stock_histories[%s]=%s\n'
                                 % (key, stock_histories[key]))
        return stock_histories


    def stock_history_key(self, trade_c):
        """
        Generate the key for a stock_history.
        """
        return trade_c['symbol'] + ' ' + trade_c['account']


    def match_trades(self):
        """
        Match sells with the curresponding buys, taking into account
        not selling off an entire position. returns array of buys and
        corresponding sells for stock symbol+account (matching_trades).
        """
        matching_trades = []
        stock_histories = self.collect_trades()
        for stock_history_key in sorted(stock_histories.keys()):
            stock_history = stock_histories[stock_history_key]
            buy_index = 0
            sell_index = 0
            buys = []
            sells = []
            while True:
                if sell_index >= len(stock_history[SELL]):
                    # Ran out of sell orders for this stock symbol+account. If
                    # there any buy orders left, they are assets we still own.
                    if buys or sells:
                        # We were in the middle of a transaction that need
                        # completing.
                        matching_trades.append((buys, sells))
                    break
                this_buy = stock_history[BUY][buy_index]
                buys.append(this_buy)
                this_sell = stock_history[SELL][sell_index]
                sells.append(this_sell)
                if this_buy['n_shares'] == this_sell['n_shares']:
                    # There are the same number of shares in the buy and sell
                    # orders.
                    matching_trades.append((buys, sells))
                    buy_index += 1
                    sell_index += 1
                    buys = []
                    sells = []
                elif this_buy['n_shares'] > this_sell['n_shares']:
                    # Need to calculate the share price for this buy if we
                    # haven't already done so.
                    if 'computed_share_price' in this_buy:
                        computed_share_price = this_buy['computed_share_price']
                    else:
                        # Haven't calculated it yet. Do so now.
                        computed_share_price = (this_buy['total'] + 0.0) / this_buy['n_shares']
                        this_buy['computed_share_price'] = computed_share_price
                    small_buy = this_buy.copy()
                    small_buy['n_shares'] = this_sell['n_shares']
                    small_buy['total'] = computed_share_price * small_buy['n_shares']
                    buys.pop() # pop this_buy
                    buys.append(small_buy)
                    # Make this buy order n_shares smaller by the
                    # n_shares in the sell order.
                    this_buy['n_shares'] -= this_sell['n_shares']
                    this_buy['total'] = computed_share_price * this_buy['n_shares']
                    sell_index += 1
                else:   # (this_buy['n_shares'] < this_sell['n_shares'])
                    # Need to calculate the share price for this sell if we
                    # haven't already done so.
                    if 'computed_share_price' in this_sell:
                        computed_share_price = this_sell['computed_share_price']
                    else:
                        # Haven't calculated it yet. Do so now.
                        computed_share_price = (this_sell['total'] + 0.0) / this_sell['n_shares']
                        # Save it for later.
                        this_sell['computed_share_price'] = computed_share_price
                    small_sell = this_sell.copy()
                    small_sell['n_shares'] = this_buy['n_shares']
                    small_sell['total'] = computed_share_price * small_sell['n_shares']
                    sells.pop() # pop this_sell
                    sells.append(small_sell)
                    matching_trades.append((buys, sells))
                    # The buy order is filled. Change this sell order
                    # to have the remaining shares.
                    buys = []
                    sells = []
                    this_sell['n_shares'] -= this_buy['n_shares']
                    this_sell['total'] = computed_share_price * this_sell['n_shares']
                    buy_index += 1
        return matching_trades


    def report(self, year):
        """
        Controller for report generation.
        """
        # HTML header
        print("""<html>
<head>
<style>
table, th, td {
    border: 1px solid black;
}
</style>
</head>
<body>
<h2>Details for IRS form 1040 Schedule B Parts I and II for %d</h2>""" % (year,))
        if self.do_schedule_b:
            self.render_schedule_b(year)
        if self.do_8949:
            self.render_8949(year)
        print("""</body>
</html>""")


    def render_schedule_b(self, year):
        """
        Render HTML for 1040 Schedule B Parts I and II for the dividends that are taxable
        this year.
        """
        # Name is the key
        interests = dict()
        dividends = dict()
        for act in self.activity.rows:
            if act['activity_date'].year != year:
                continue
            if self.account.taxable(act['account']):
                name = act['name']
                if act['activity_type'] == 'interest':
                    if name not in interests:
                        interests[name] = 0
                    interests[name] += act['amount']
                elif act['activity_type'] == 'dividend':
                    if name not in dividends:
                        dividends[name] = 0
                    dividends[name] += act['amount']
                
        # Have all of the detail, now render the report.
        # Printout the details needed by the IRS.
        print("""
<table>
<tr>
  <th colspan="2">
  Part I - Interest
  </th>
</tr>""")
        print("<tr>")
        self.header_cell('Payer')
        self.header_cell('Amount')
        print("</tr>")
        for payer in sorted(interests.keys(), key=lambda x:x.lower()):
            print("<tr>")
            self.cell(payer)
            self.cell_amount(interests[payer])
            print("</tr>")
        print("<tr>")
        self.cell('Total')
        self.cell_amount(sum(interests.values()))
        print("</tr>")
        print("</table>")

        print("""
<table>
<tr>
  <th colspan="2">
  Part II - Dividends
  </th>
</tr>""")
        print("<tr>")
        self.header_cell('Payer')
        self.header_cell('Amount')
        print("</tr>")
        for payer in sorted(dividends.keys(), key=lambda x:x.lower()):
            print("<tr>")
            self.cell(payer)
            self.cell_amount(dividends[payer])
            print("</tr>")
        print("<tr>")
        self.cell('Total')
        self.cell_amount(sum(dividends.values()))
        print("</tr>")
        print("</table>")


    def render_8949(self, year):
        """
        Render HTML for Form 8949 Parts I and II for the stock gains/losses
        that are taxable this year.
        """
        # These are all matching trades, not just this year's
        matching_trades = self.match_trades()


        print("<h3>Part II</h3>")
        # Print out the details needed by the IRS.
        print("""
<table>
<tr>
  <th colspan="8">
    Short term sells
  </th>
</tr>""")
        print("<tr>")
        self.header_cell('Description')
        self.header_cell('Acquired')
        self.header_cell('Date Sold')
        self.header_cell('Proceeds')
        self.header_cell('Cost')
        self.header_cell('(f)')
        self.header_cell('(g)')
        self.header_cell('Gain or (Loss)')
        print("</tr>")
        totals = dict(proceeds=0, cost=0, profit=0)
        for (buys, sells) in matching_trades:
            if len(buys) != 1 or len(sells) != 1:
                print('Multiple buys/sells:')
                print(buys)
                print(sells)
                sys.exit(1)
            buy = buys[0]
            sell = sells[0]
            if sell['trade_date'].year != year:
                # Trade for another year.
                continue

            if self.account.taxable(buy['account']):
                if ((sell['trade_date'] - buy['trade_date']).days
                        <= self.n_days(year)):
                    print("<tr>")
                    self.cell("%d sh. %s" % (buy['n_shares'], buy['name']))
                    self.cell(buy['trade_date'].strftime("%m/%d/%Y"))
                    self.cell(sell['trade_date'].strftime("%m/%d/%Y"))
                    proceeds = sell['total']
                    self.cell_amount(proceeds)
                    totals['proceeds'] += proceeds
                    cost = buy['total']
                    self.cell_amount(cost)
                    self.cell('&nbsp;') # F
                    self.cell('&nbsp;') # G
                    profit = proceeds - cost
                    totals['profit'] += profit
                    self.cell_amount(profit)
                    print("</tr>")
        print("<tr>")
        self.cell('Totals')
        self.cell('&nbsp;')
        self.cell('&nbsp;')
        self.cell_amount(totals['proceeds'])
        self.cell_amount(totals['cost'])
        self.cell('&nbsp;')
        self.cell('&nbsp;')
        self.cell_amount(totals['profit'])
        print("</tr>")
        print("""
</table>
<table>
<tr>
  <th colspan="8">
    Long term sells
  </th>
</tr>""")
        print("<tr>")
        self.header_cell('Description')
        self.header_cell('Acquired')
        self.header_cell('Date Sold')
        self.header_cell('Proceeds')
        self.header_cell('Cost')
        self.header_cell('(f)')
        self.header_cell('(g)')
        self.header_cell('Gain or (Loss)')
        print("</tr>")
        totals = dict(proceeds=0, cost=0, profit=0)
        for (buys, sells) in matching_trades:
            if len(buys) != 1 or len(sells) != 1:
                print('Multiple buys/sells:')
                print(buys)
                print(sells)
                sys.exit(1)
            buy = buys[0]
            sell = sells[0]
            if sell['trade_date'].year != year:
                # Trade for another year.
                continue

            if self.account.taxable(buy['account']):
                if ((sell['trade_date'] - buy['trade_date']).days
                        > self.n_days(year)):
                    print("<tr>")
                    self.cell("%d sh. %s" % (buy['n_shares'], buy['name']))
                    self.cell(buy['trade_date'].strftime("%m/%d/%Y"))
                    self.cell(sell['trade_date'].strftime("%m/%d/%Y"))
                    proceeds = sell['total']
                    self.cell_amount(proceeds)
                    totals['proceeds'] += proceeds
                    cost = buy['total']
                    self.cell_amount(cost)
                    self.cell('&nbsp;') # F
                    self.cell('&nbsp;') # G
                    profit = proceeds - cost
                    totals['profit'] += profit
                    self.cell_amount(profit)
                    print("</tr>")
        print("<tr>")
        self.cell('Totals')
        self.cell('&nbsp;')
        self.cell('&nbsp;')
        self.cell_amount(totals['proceeds'])
        self.cell_amount(totals['cost'])
        self.cell('&nbsp;')
        self.cell('&nbsp;')
        self.cell_amount(totals['profit'])
        print("</tr>")
        print("</table>")


def action(args):
    """
    Load the parts in the spreadsheet
    """
    app = App(args)
    app.report(args.year)


if __name__ == '__main__':
    action(build_parser().parse_args())
