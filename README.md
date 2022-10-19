# Tēzaurs.lv export tools

Scripts to prepare an offline TEI and LMF exports from the Tezaurs.lv database.

Requires psycopg2, which doesn't install cleanly on OSX and requires that postgresql is installed via brew (not the downloaded .dmg installer) and the following

`export PATH=$PATH:/Library/PostgreSQL/11/bin/`

`pip3 install psycopg2`

## ILI <-> PWN 3.0 mapping

To obtain correct LMF ili values, `config` folder must contain mapping file `ili-map-pwn30.tab` from https://github.com/globalwordnet/cili/blob/master/ili-map-pwn30.tab