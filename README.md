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

This would normally harvest the entire set in one go:

```console
$ python -m oaiharvest.harvest -s DDD kb
```

To restrict harvesting to the night, we add the `--between` argument, like this:

```console
$ python -m oaiharvest.harvest -s DDD -b 19:00 06:00 kb
```

We wrap this in a script of our own in order to capture the resumption tokens from `pyoai`:

```console
$ python harvest_metadata.py /path/to/tokens.log -s DDD -b 19:00 06:00 kb
```

Run the latter command in a `screen` session so you can logout from the harvesting server without interrupting the process.


## Preventing filesystem problems

Run the `organize.py` over the harvesting directory at least every 15 minutes using a cron job. You need to have a crontab entry that looks like this:

    14,29,44,59 0-5,19-23 * * * /absolute/path/to/virtualenv/bin/python /absolute/path/to/organize.py /absolute/path/to/harvesting/dir

This will compress the newspapers while moving them into subdirectories by the last two digits of their serial number. Every time it runs, it creates a manifest file that lists all newly organized newspapers. These manifests are fed into the OCR harvester.


## Harvesting the OCR

Harvesting the OCR is the slowest process, as every article has to be retrieved individually. We automate this with the `harvest_ocr.py` script. Invoke it like this:

```console
$ python harvest_ocr.py /path/to/harvesting/dir
```

This depends on there being manifests with downloaded metadata in the harvesting directory. You can run the OCR harvest in parallel with the metadata harvest and the `organize.py` cleaner.

Again, it is advised that you do this in a `screen` session so you can logout from the server while the process is running.


## Diagnostics

You should periodically check your `screen` session to verify that the harvesting scripts are still running properly. In addition to this, the contents of the harvesting directory carry information about the progress of the harvest.

The `manifests`, `in_progress` and `ocr_complete` directories contain manifest files in various stages of processing. Manifests in the first directory list newspapers of which the metadata have been downloaded but the OCR still have to be retrieved. Manifests move through `in_progress` and finally into `ocr_complete` complete as the article texts are collected. Each line in a manifest represents a single newspaper, so a crude indication of OCR harvesting progress can be obtained by comparing the total at the bottom of

```console
$ wc -l /path/to/harvesting/dir/manifests/*
```

to the total at the bottom of

```console
$ wc -l /path/to/harvesting/dir/ocr_complete/*
```

Keep in mind that this does not tell you how many of the newspapers in the manifest in `in_progress` have been processed. For a more precise indication of progress, you should compare the number of `*.didl.xml.gz` files (no OCR, minus one that should be in progress) to the number of `*.tgz` files (OCR complete), inside the two-digit subdirectories.
