REM Filtering by whitelist.
REM Whitelist format: each line contains one allowed entryword and optional tab-separated homonym index.
::python lv/ailab/teztei/tezaurs_dump.py mlvv_dv config/whitelist100.txt
::python lv/ailab/teztei/tezaurs_dump.py tezaurs_dv config/whitelist100.txt

REM Dumping whole dictionary (mwe entries excluded).
::python lv/ailab/teztei/tezaurs_dump.py mlvv_dv
::python lv/ailab/teztei/tezaurs_dump.py llvv_dv
python lv/ailab/teztei/tezaurs_dump.py tezaurs_dv
pause