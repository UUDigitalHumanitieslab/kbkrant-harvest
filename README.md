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

This does work, but it will start from scratch if you run the command again. In other words, you can't use this for incremental harvesting. Read on for a possible solution.


## Harvesting incrementally

You can start a full harvest in the background and suspend it immediately, storing the process ID in a file, like this:

```console
$ oai-harvest -s DDD kb &
$ echo $! >harvest.pid
$ kill -TSTP `cat harvest.pid`
```

To resume harvesting later, send the SIGCONT signal:

```console
$ kill -CONT `cat harvest.pid`
```

you can alternate between the SIGCONT and the SIGTSTP signals in order to harvest in start-stop cycles.

In order to stop harvesting completely before it is done, send SIGINT, which is `kill`'s default signal:

```console
$ kill `cat harvest.pid`
```
