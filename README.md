Invest
======


Used to store and mange investment detail from Stifel.
The python2 version of invest is broken. This reworks that code and uses python3.

Basic Installation
------------------

When developing, I typically install the requirements to a virtualenv,
then use the ``manage.py`` entry point for execution. You'll need pip,
virtualenv, and setuptools.

Create a virtualenv::

    python -m venv invest2-env
	dos2unix invest2-env/Scripts/activate
	source invest2-env/Scripts/activate
	pip install pip -U #Latest pip
	pip install -r requirements.txt


Commands
--------

Load database from spreadsheet::

	python -m app.commands.s2db

Generate multipage report with a graph for each stock::

	python -m app.commands.report

Puts PDF file in report.pdf.

2 profie/loss queries:

	app/commands/queries.sh
	
Output goes in sql/profit_loss_*.csv>

Generates a single chart for all stocks::

	python -m app.commands.render_charts

Output is in charts/*.pdf. Doesn't do well when the same stock is in
multiple accounts. Probably need to fix that. This command is less
needed since the report.pdf file has more data and handle the same
stock in multiple accounts.

Indicate whether a stock is long or short for all active stocks::

	python -m app.commands.stock_age

Output is to stdout. Can either be a CSV file (blank separator) or an
HTML file.

Generate the equivalent of the 1040 Schedule B part II, or Form 8949::

	python -m app.commands.stock_sales -h

Outputs HTML to stdout.

TODO
----

TODO:
Fix bug in stock_sales. Think about using an SQL query to group the data.
Look to see what is next.

DONE:
Got s2db (loader) working.
Got SQL runner working
Got render_charts to display big chart for all stocks.
Fixed errors in the spreadsheet for stock names / symbol.
