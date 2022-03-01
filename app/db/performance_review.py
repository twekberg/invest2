"""
Details regarding the performance_review table.
"""


import app.db


my_table = 'performance_review'


class PerformanceReview(object):
    def __init__(self):
        self.database = inv.db.database
        self.rows = self.database.fetch_all(my_table)
        for row in self.rows:
            row['end_date'] = self.database.fix_date(row['end_date'])
        self.database.add(my_table, self)
