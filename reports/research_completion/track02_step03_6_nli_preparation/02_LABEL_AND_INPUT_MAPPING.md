# TrustRAG — Track 2, Step 3.6: NLI Label and Input Mapping Protocol

## 1. Grounded Semantic Label Mapping

The dataset strictly avoids heuristic remapping of unsupported information:

| NLI Label | Target Class ID | Source Annotation Criteria | Semantic Definition |
| :--- | :---: | :--- | :--- |
| **`ENTAILMENT`** | `0` | `conflict_types == []` (0 conflicts, 0 baseless info) | The candidate hypothesis is fully supported and grounded by the context premise. |
| **`CONTRADICTION`** | `1` | `conflict_types` contains only `Evident Conflict` or `Subtle Conflict` | The candidate hypothesis directly contradicts factual statements in the context premise. |
| **`NEUTRAL`** | `2` | `conflict_types` contains only `Evident Baseless Info` or `Subtle Baseless Info` | The candidate hypothesis contains claims not mentioned in the context premise (unsupported, but not contradicted). |

### Concrete Annotation Breakdown in Training Set
- `CONTRADICTION`:
  - `('Evident Conflict',)`: 1,334 records
  - `('Subtle Conflict',)`: 73 records
  - `('Evident Conflict', 'Subtle Conflict')`: 13 records
- `ENTAILMENT`:
  - `()`: 6,707 records
- `NEUTRAL`:
  - `('Evident Baseless Info',)`: 1,792 records
  - `('Subtle Baseless Info',)`: 600 records
  - `('Evident Baseless Info', 'Subtle Baseless Info')`: 296 records

---

## 2. Text Input Serialization Protocol

Input text fields are extracted directly without heuristic modification:
- **Text A (Premise):** `record["premise"].strip()` (Source document or grounding context)
- **Text B (Hypothesis):** `record["hypothesis"].strip()` (Generated candidate claim or response)

Tokenizer cross-encoder formatting:
`[CLS] Premise [SEP] Hypothesis [SEP]`
Truncation: Max sequence length 128 tokens (or 512 for full training). Padding: `max_length`.
