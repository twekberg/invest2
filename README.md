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

TODO:
Look to see what is next.

DONE:
Got s2db (loader) working.
