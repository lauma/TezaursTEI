REM Filtering by whitelist.
REM Whitelist format: each line contains one allowed entryword and optional tab-separated homonym index.
::python -m lv.ailab.teztei.do_tei_dictionary_export mlvv_dv config/whitelist100.txt
::python -m lv.ailab.teztei.do_tei_dictionary_export tezaurs_dv config/whitelist100.txt

REM Exporting whole dictionary.
python -m lv.ailab.teztei.do_tei_dictionary_export mlvv_current
python -m lv.ailab.teztei.do_tei_dictionary_export llvv_current
python -m lv.ailab.teztei.do_tei_dictionary_export tezaurs_current
pause