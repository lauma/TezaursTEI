# Tēzaurs.lv export tools

Scripts to prepare an offline TEI and LMF exports from the Tezaurs.lv database.
- TEI export is done according to TEI 5 Chapter 9 "Dictionaries": https://tei-c.org/release/doc/tei-p5-doc/en/html/DI.html
- LMF export is done according to Global Wordnet Asociation XML chapter: https://globalwordnet.github.io/schemas/#xml

## Development Notes
### Install

Requires psycopg2, which doesn't install cleanly on OSX and requires that postgresql is installed via brew (not the downloaded .dmg installer) and the following

```
export PATH=$PATH:/Library/PostgreSQL/11/bin/
pip3 install psycopg2
```

### ILI <-> PWN 3.0 mapping

To obtain correct LMF ili values, `config` folder must contain mapping file `ili-map-pwn30.tab` from https://github.com/globalwordnet/cili

### OMV validation

- The extensive validator is here: https://github.com/globalwordnet/OMW
- There is also Python package wm that contains simpler validator: https://wn.readthedocs.io/en/latest/cli.html . Command to use it is `python -m wn validate tezaurs_version-number_lmf.xml`
