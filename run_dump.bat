REM Filtering by whitelist.
REM Whitelist format: each line contains one allowed entryword and optional tab-separated homonym index.
::python tezaurs_dump.py mlvv_dv whitelist100.txt
::python tezaurs_dump.py tezaurs_dv whitelist100.txt

REM Dumping whole dictionary (mwe entries excluded).
::python tezaurs_dump.py mlvv_dv
::python tezaurs_dump.py llvv_dv
python tezaurs_dump.py tezaurs_dv
pause