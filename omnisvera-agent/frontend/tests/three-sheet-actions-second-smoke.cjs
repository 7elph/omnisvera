// Fixed second half of the same native fixture test, never model-provided code.
process.env.OMNISVERA_QA_THREE_SHEET_BATCH='second';
require('./three-sheet-actions-smoke.cjs');
