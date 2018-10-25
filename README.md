# kbkrant-harvest

working environment for harvesting the Databank Digitale Dagbladen


## Initial setup

Create and activate a virtualenv, then

```console
$ pip install pip-tools
$ pip-sync
$ oai-reg add -p didl kb http://services.kb.nl/mdo/oai
    # enter destination directory in the prompt (not inside this directory)
```


## A single harvesting step

In theory, this should harvest a limited number of DDD records:

```console
# $LIMIT should be an integer of choice (sets the number of records)
$ oai-harvest -s DDD -l $LIMIT kb
```

In practice, it doesn't work because of https://github.com/infrae/pyoai/pull/30. Next step is likely to fork `pyoai` in order to fix the issue ourselves.
