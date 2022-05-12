REM Filtering by whitelist.
REM Whitelist format: each line contains one allowed entryword and optional tab-separated homonym index.
::python -m lv.ailab.teztei.tezaurs_dump mlvv_dv config/whitelist100.txt
::python -m lv.ailab.teztei.tezaurs_dump tezaurs_dv config/whitelist100.txt

REM Dumping whole dictionary.
::python -m lv.ailab.teztei.tezaurs_dump mlvv_dv
::python -m lv.ailab.teztei.tezaurs_dump llvv_dv
python -m lv.ailab.teztei.tezaurs_dump tezaurs_dv
pause