// Fixed second half of the same native fixture test, never model-provided code.
process.env.OMNISVERA_QA_HEMOMANCY_BATCH='second';
require('./hemomancy-weapons-smoke.cjs');
