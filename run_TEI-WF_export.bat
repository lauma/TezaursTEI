chcp 65001
REM Exporting unfiltered list of wordforms in TEI format.
python -m lv.ailab.teztei.do_tei_wordform_export tezaurs_2026_01 tezaurs_2026_01-inflections.jsonl
python -m lv.ailab.teztei.do_tei_wordform_export ltg_2026_01 ltg-inflections-2026_01.jsonl

pause