REM Filtering by whitelist.
REM Whitelist format: each line contains one allowed entryword and optional tab-separated homonym index.
python tezaurs_dump.py mlvv whitelist100.txt
python tezaurs_dump.py tezaurs whitelist100.txt

REM Dumping whole dictionary (only entries of type "word").
python tezaurs_dump.py mlvv
python tezaurs_dump.py llvv
python tezaurs_dump.py tezaurs
pause