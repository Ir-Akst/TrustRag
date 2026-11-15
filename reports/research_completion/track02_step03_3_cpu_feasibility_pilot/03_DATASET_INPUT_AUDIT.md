# Track 2, Step 3.3 — Section 03: Real Dataset Input & Tokenization Audit

## 1. Input Source & Schema

Inputs were read directly from `data/processed/sft_v2/binary/train.jsonl`.
The dataset schema mandates:
- `example_id`: Unique identifier string.
- `question_or_claim`: The query or hypothesis statement.
- `context_or_evidence`: The retrieved grounding text.
- `candidate_response`: The model answer to evaluate.
- `binary_label`: String enum (`"FACTUAL"` | `"HALLUCINATED"`).

## 2. Label Mapping

In adherence to the binary classification schema:
- `"FACTUAL"` -> Class index `0`
- `"HALLUCINATED"` -> Class index `1`

## 3. Audited Pilot Examples

Three actual domain records were selected sequentially:

### Example 1:
- **Example ID:** `binary_halueval_train_halueval_0_factual`
- **Source:** `halueval` (Source ID: `0`)
- **Label:** `FACTUAL` (`0`)
- **Question:** *Which magazine was started first Arthur's Magazine or First for Women?*
- **Context:** *Arthur's Magazine (1844–1846) was an American literary periodical published in Philadelphia in the 19th century. First for Women is a woman's magazine published by Bauer Media Group in the USA.*
- **Candidate Response:** *Arthur's Magazine*
- **Active Tokens:** 62 / 128 (padded to 128)

### Example 2:
- **Example ID:** `binary_halueval_train_halueval_0_hallucinated`
- **Source:** `halueval` (Source ID: `0`)
- **Label:** `HALLUCINATED` (`1`)
- **Question:** *Which magazine was started first Arthur's Magazine or First for Women?*
- **Context:** *Arthur's Magazine (1844–1846) was an American literary periodical published in Philadelphia in the 19th century. First for Women is a woman's magazine published by Bauer Media Group in the USA.*
- **Candidate Response:** *First for Women was started first.*
- **Active Tokens:** 65 / 128 (padded to 128)

### Example 3:
- **Example ID:** `binary_halueval_train_halueval_1000_factual`
- **Source:** `halueval` (Source ID: `1000`)
- **Label:** `FACTUAL` (`0`)
- **Question:** *Ran Nakash, is an Israeli cruiserweight boxer, his only loss to date occurred on which date, against WBO Cruiserweight champion Marco Huck, a German professional boxer known for his aggressive style and punching power?*
- **Context:** *His only loss to date occurred on April 2, 2011 against WBO Cruiserweight champion Marco Huck. Muamer Hukić (born 11 November 1984), best known as Marco Huck, is a German professional boxer known for his aggressive style and punching power.*
- **Candidate Response:** *April 2, 2011*
- **Active Tokens:** 100 / 128 (padded to 128)
