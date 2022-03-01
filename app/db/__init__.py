"""
Base for database operations.
"""

import sys
import logging
import sqlite3
import os.path
from datetime import datetime


log = logging.getLogger(__name__)


class Database(object):
    def __init__(self):
        self.con = sqlite3.connect(self.locate_db_file())
        self.cur = self.con.cursor()
        self.databases = dict()


    def add(self, name, database):
        self.databases[name] = database


    def locate_db_file(self):
        dbfile = 'investments.db'
        subdir_max = 10
        while not os.path.exists(dbfile):
            dbfile = '../' + dbfile
            subdir_max -= 1
            if not subdir_max:
                raise exception('Unable to locate database file')
        return dbfile


    def get_columns(self, table_name):
        """
        Get the column names for the specified table. Also initiates a SELECT * from the table.
        """
        sql = 'SELECT * FROM %s' % (table_name,)
        self.cur.execute(sql)

        return [d[0] for d in self.cur.description]


    def fetch_all(self, table_name):
        """
        Return all rows of a table as a list of dicts, where the keys for a dict are column names.
        """
        cols = self.get_columns(table_name)
        return [dict(zip(cols, row)) for row in self.cur.fetchall()]


    def fix_date(self, d):
        """
        Get just the date part of a date/time.
        """
        if isinstance(d, str) or isinstance(d, unicode):
            return datetime.strptime(d.split(' ', 1)[0], '%Y-%m-%d')
        return d


    def date_to_string(self, d):
        return d.strftime('%Y-%m-%d')


database = Database()


if __name__ == '__main__':
    print(database.fetch('trade_history')[0])
