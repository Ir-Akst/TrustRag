# Dataset Provenance & Split Integrity Audit

## 1. Fresh Holdout Splits
All Phase 38 evaluations were conducted on fresh datasets generated under :
1.  (=300$): 180 adversarial injection attacks across 4 unseen categories + 120 benign controls.
2.  (=150$): 100 indirect injection attacks across 5 structural bypass styles + 50 benign technical documents.
3.  (=270$): 30 samples per language across 9 languages (15 native, 15 transliterated).
4.  (=100$): Balanced 25-sample splits (Supported, Contradicted Semantic/Numeric, Unsupported, Partially Supported).

## 2. Zero Contamination Guarantee
None of the Phase 37 audit examples were reused or hardcoded. All test cases were generated from independent templates and synthetically varied prompts.
