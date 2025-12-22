chcp 65001
REM Exporting filtered list of wordforms in ispell format.
python -m lv.ailab.tezwordforms.do_ispell_export tezaurs_2026_01 tezaurs_2026_01-inflections.jsonl
python -m lv.ailab.tezwordforms.do_ispell_export ltg_2026_01 ltg-inflections-2026_01.jsonl

pause