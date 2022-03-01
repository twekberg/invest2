"""
Page layout example using reportlab.

TODO:
For each graph, draw the gain and loss lines.
Sort the gain/loss tables on pages 43-44
"""

import argparse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.rl_config import defaultPageSize
import time
from datetime import datetime
import calendar

from app.db.account import Account
from app.db.performance_review import PerformanceReview
from app.db.trade_history import TradeHistory
from app.db import database
from app.pdf_chart import render_chart

from app.commands.render_charts import RenderChart

def build_parser():
    parser = argparse.ArgumentParser(description = globals()['__doc__'],
                                     formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--out_file',
                        default='../report.pdf',
                        help='The output PDF file. '
                        'Default: %(default)s.')
    parser.add_argument('-t', '--title',
                        default='Investment Report|for Thomas W. Ekberg',
                        help='Title for the report. '
                        'Separate multiple lines with a vertical bar (|). '
                        'Default: %(default)s.')
    parser.add_argument('-f', '--footer_title',
                        default='Page %p of %P|Investment Report|Printed %d %t',
                        help='Title for the page footer. Use | to separate pieces: '
                        'left(right)|center|right(left) for even (odd) pages. '
                        'Use %%p for current page, '
                        '%%P for total pages, %%d for date, %%t for time. '
                        'Default: %(default)s.')
    return parser


class DataItems():
    """
    Container for the data we need.
    """
    def __init__(self):
        # Account data
        self.account_titles = ['Name', 'Number']
        ac = Account()
        self.accounts = [[row['number'], row['name']] for row in ac.rows]
        self.account_number_to_name = dict(self.accounts)

        # Latest TradeHistoryData
        self.trade_history = []
        # Identify latest date
        th = TradeHistory()
        max_date = None
        for row in th.rows:
            if max_date:
                if row['history_date'] > max_date:
                    max_date = row['history_date']
            else:
                max_date = row['history_date']
        # Now that we have the latest date, create a dict, keyed by account type.
        # and the value is a row.
        all = dict()
        for ac_row in ac.rows:
            d = []
            all[ac_row['number']] = d
            for th_row in th.rows:
                if ac_row['number'] == th_row['account'] and \
                   th_row['history_date'] == max_date:
                    d.append(th_row)
        # Now we can render the lines.
        self.trailer_data = []
        for number in all.keys():
            d = []
            self.trailer_data.append(
                dict(title='%s - %s' % (number, self.account_number_to_name[number]),
                     column_headers=['Symbol', 'Quantity', 'Unit Cost',
                                     'Current Price', '-15%', '+30%'],
                     data = d))
            for th in all[number]:
                d.append([th['symbol'], th['n_shares'],
                          th['unit_cost'], th['current_price'],
                          '%3.2f' % (th['unit_cost'] * .85,),
                          '%3.2f' % (th['unit_cost'] * 1.30,)])

        # Performance data
        # Create a dict indexed by the account # with value (date,market value).
        self.performance_reviews_market = dict()
        pr = PerformanceReview()
        for (number, name) in self.accounts:
            self.performance_reviews_market[number] = []
            for row in pr.rows:
                if row['account'] == number:
                    # Convert date to a float yyyy.yearFraction.
                    ed = row['end_date']
                    # Create a datetime, with the year and month from
                    # ed, and the end of month day (from
                    # calendar.monthrange).  With timetuple one can
                    # get the day of the year, and the convert to a
                    # fraction.  Use 366 to account for leap years
                    # that have that many days.
                    frac = ((datetime(ed.year, ed.month, calendar.monthrange(ed.year, ed.month)[1])).timetuple().tm_yday - 1) / 366.0
                    self.performance_reviews_market[number].append(
                        (row['end_date'].year + frac,
                        row['end_market_value']))

        # Trade history
        class Args():
            def __init__(self):
                self.stocks = []
                self.out_dir = None
        self.charts = RenderChart(Args()).report()


class Pages():
    def __init__(self, args, n_pages):
        self.PAGE_HEIGHT=defaultPageSize[1]
        self.PAGE_WIDTH=defaultPageSize[0]
        self.title = args.title
        self.footer_title = args.footer_title
        self.n_pages = n_pages
        self.now = datetime.now()


    def parse_footer(self, page):
        """
        Parse the footer making text substitutions and splitting the 3 parts.
        Returns a triple (inner_edge,center,outer_edge) for double-sided pages.
        """
        # Perform text substitution first.
        footer = self.footer_title.replace('%p', str(page)) \
                                  .replace('%P', str(self.n_pages)) \
                                  .replace('%d', self.now.strftime('%Y/%m/%d')) \
                                  .replace('%t', self.now.strftime('%H:%M:%S')) \
                                  .split('|')
        if page % 2 == 1:
            # Page numbers are on the outside edge of a double-sided page.
            footer.reverse()
        return footer


    def render_footer(self, canvas, doc):
        canvas.setFont('Times-Roman',9)
        (inside, center, outside) = self.parse_footer(doc.page)
        canvas.drawString(inch, 0.75 * inch, inside)
        canvas.drawCentredString(self.PAGE_WIDTH/2.0, 0.75 * inch, center)
        canvas.drawRightString(self.PAGE_WIDTH - inch, 0.75 * inch, outside)


    def first_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Bold',16)
        y = self.PAGE_HEIGHT - 108
        for title in self.title.split('|'):
            canvas.drawCentredString(self.PAGE_WIDTH/2.0, y, title)
            y -= 16
        self.render_footer(canvas, doc)
        canvas.restoreState()


    def later_pages(self, canvas, doc):
        canvas.saveState()
        self.render_footer(canvas, doc)
        canvas.restoreState()


class Action():
    def __init__(self, args):
        self.args = args
        self.data_items = DataItems()
        
    def render_investments(self):
        # Investment type table.
        account_data = self.data_items.accounts
        t=Table([self.data_items.account_titles] + account_data)
        t.setStyle(TableStyle([('TEXTCOLOR',     (0,0), (-1,0),colors.green),
                               ('FONT',          (0,0), (-1,0), 'Helvetica-Bold'),
                               ('FONTSIZE',      (0,0), (-1,0), 14),
                               ('TOPPADDING',    (0,0), (-1,0), 1),
                               ('BOTTOMPADDING', (0,0), (-1,0), 5),
                               ('INNERGRID',     (0,0), (-1,-1), 1.0, colors.black),
                               ('BOX',           (0,0), (-1,-1), 1.0, colors.black),]))
        return t


    def render_performance(self):
        perf_data = self.data_items.performance_reviews_market
        accounts = sorted(perf_data.keys())
        data = [perf_data[account] for account in accounts]
        drawing = render_chart(None, 'Performance Graphs',
                               data,
                               accounts,
                               width=500,
                               graph_width=500-100,
                               graph_y=0)
        return drawing


    def render_charts(self):
        return self.data_items.charts

    def render(self):
        charts = self.render_charts()
        n_charts = len(charts)
        n_pages = 1 + n_charts + 2
        pages = Pages(self.args, n_pages)
        doc = SimpleDocTemplate(self.args.out_file, pagesize=letter)
        self.styles = getSampleStyleSheet()

        elements = [Spacer(1, inch)]  # Start off with a spacer 1" high

        elements.append(self.render_investments())
       
        elements.append(self.render_performance())

        elements.append(PageBreak())

        # Rotate the charts (graphs) so they are in landscape orientation.
        # Translate (x,y) to specify a new origin in lower right part of the page.
        [(chart.rotate(90),chart.translate(-4 * inch, -5.0 * inch)) for chart in charts]
        elements += charts
        elements += self.render_loss_gain_chart()
        doc.build(elements, onFirstPage=pages.first_page, onLaterPages=pages.later_pages)


    def render_loss_gain_chart(self):
        elements = [PageBreak()]
        first = True
        for td in self.data_items.trailer_data:
            if first:
                first = False
            else:
                elements.append(Paragraph(
                    '<font name="Helvetica">%s</font>' % ('&nbsp;',),
                    self.styles["Normal"]))
            elements.append(Paragraph(
                '<font name="Helvetica">%s</font>' % (td['title'],),
                self.styles["Normal"]))
            elements.append(Paragraph(
                '<font name="Helvetica">%s</font>' % ('&nbsp;',),
                self.styles["Normal"]))
            elements.append(Table([td['column_headers']] + td['data'],
                                  rowHeights=[.228 * inch] * (len(td['data']) + 1),
                                  style = [
                                      ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                      ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                      ('FONTSIZE', (0, 0), (-1,-1), 8),
                                  ]))
        return elements


def action(args):
    action = Action(args)
    action.render()

    
if __name__ == '__main__':
    action(build_parser().parse_args())
