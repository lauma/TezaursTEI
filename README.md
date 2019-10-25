# TezaursTEI

Script to prepare an offline TEI export out of the Tezaurs.lv database - currently very minimalistic - only main lexeme and gloss texts.

Requires psycopg2, which doesn't install cleanly on OSX and requires that postgresql is installed via brew (not the downloaded .dmg installer) and the following

`export PATH=$PATH:/Library/PostgreSQL/11/bin/`

`pip3 install psycopg2`
