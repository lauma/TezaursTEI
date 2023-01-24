REM Exporting Wordnet LMF from dictionary.
python -m lv.ailab.tezlmf.do_lmf_wordnet_export tezaurs_current
::python -m lv.ailab.tezlmf.do_lmf_wordnet_export tezaurs_dv

REM Validation.
::python -m wn validate tezaurs_current_lmf.xml
::python -m wn validate tezaurs_dv_lmf.xml
pause