"""
Details regarding the account table
"""


import app.db


my_table = 'account'


class Account(object):
    def __init__(self):
        self.database = inv.db.database
        self.rows = self.database.fetch_all(my_table)
        self.database.add(my_table, self)


    def account_name_lookup(self, account_number):
        for row in self.rows:
            if row['number'] == account_number:
                return row['name']
        return None


    def taxable(self, account_number):
        return 'IRA' not in self.account_name_lookup(account_number)
