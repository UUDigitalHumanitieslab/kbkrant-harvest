# kbkrant-harvest

working environment for harvesting the Databank Digitale Dagbladen


## Initial setup

Create and activate a virtualenv, then

```console
$ pip install pip-tools
$ pip-sync
$ python -m oaiharvest.registry add -p didl kb http://services.kb.nl/mdo/oai/KEY
    # enter destination directory in the prompt (not inside this directory)
```

where `KEY` should be a valid API key.


## Harvesting the metadata

This will harvest the entire set in one go:

```console
$ python -m oaiharvest.harvest -s DDD kb
```

To restrict harvesting to the night, add the `--between` argument, like this:

```console
$ python -m oaiharvest.harvest -s DDD -b 19:00 06:00 kb
```

Run this in a `screen` session so you can logout from the harvesting server without interrupting the process.


## Preventing filesystem problems

Run the `organize.py` over the harvesting directory at least every 15 minutes using a cron job. You need to have a crontab entry that looks like this:

    14,29,44,59 0-5,19-23 * * * /absolute/path/to/virtualenv/bin/python /absolute/path/to/organize.py /absolute/path/to/harvesting/dir
