# Track 2, Step 3.4.2 — Section 02: Training Loss and Optimization Dynamics

## 1. Loss Progression

- **Initial Training Loss (Step 1):** `0.5788`
- **Final Training Loss (Step 1,000):** `0.2144`
- **Overall Average Training Loss:** `0.5065`

### 50-Step Logged Checkpoints:

| Step | Loss | Rolling Loss (50 steps) | Learning Rate | Process RSS | Available RAM | Elapsed Time |
|:----:|:----:|:-----------------------:|:-------------:|:-----------:|:-------------:|:------------:|
| 50 | 0.7417 | 0.7035 | 9.80e-06 | 2,354.8 MB | 4,339.1 MB | 101.7 s |
| 100 | 0.6059 | 0.6984 | 1.98e-05 | 2,417.0 MB | 4,589.4 MB | 166.0 s |
| 150 | 0.7185 | 0.6996 | 1.89e-05 | 2,391.6 MB | 4,660.7 MB | 231.6 s |
| 200 | 0.5512 | 0.6720 | 1.78e-05 | 2,417.1 MB | 4,483.7 MB | 293.9 s |
| 250 | 0.0048 | 0.3768 | 1.67e-05 | 2,363.1 MB | 4,694.8 MB | 355.9 s |
| 300 | 0.0160 | 0.2397 | 1.56e-05 | 2,412.6 MB | 4,696.4 MB | 418.4 s |
| 350 | 0.0060 | 0.0307 | 1.45e-05 | 2,426.5 MB | 4,605.3 MB | 490.8 s |
| 400 | 0.0050 | 0.1806 | 1.34e-05 | 2,417.5 MB | 4,841.0 MB | 557.0 s |
| 450 | 0.0029 | 0.1450 | 1.22e-05 | 2,399.2 MB | 4,990.1 MB | 617.9 s |
| 500 | 0.0042 | 0.0959 | 1.11e-05 | 2,444.5 MB | 4,925.6 MB | 679.3 s |
| 550 | 0.4569 | 1.1406 | 1.00e-05 | 2,361.3 MB | 4,980.5 MB | 740.1 s |
| 600 | 1.2020 | 0.6510 | 8.91e-06 | 2,388.3 MB | 4,918.3 MB | 801.0 s |
| 650 | 0.4984 | 0.6549 | 7.80e-06 | 2,370.3 MB | 4,824.3 MB | 862.0 s |
| 700 | 1.2151 | 0.6237 | 6.69e-06 | 2,419.9 MB | 4,670.8 MB | 923.0 s |
| 750 | 0.3505 | 0.6373 | 5.58e-06 | 2,415.4 MB | 4,870.5 MB | 984.1 s |
| 800 | 0.6333 | 0.6540 | 4.47e-06 | 2,388.4 MB | 5,024.0 MB | 1,045.4 s |
| 850 | 0.2794 | 0.5877 | 3.36e-06 | 2,390.6 MB | 5,017.9 MB | 1,107.1 s |
| 900 | 0.3549 | 0.5223 | 2.24e-06 | 2,388.4 MB | 4,996.0 MB | 1,169.9 s |
| 950 | 0.2124 | 0.4766 | 1.13e-06 | 2,422.2 MB | 4,974.1 MB | 1,232.0 s |
| 1000 | 0.2144 | 0.3397 | 2.22e-08 | 2,370.4 MB | 5,061.0 MB | 1,293.4 s |

---

## 2. Learning Dynamics Analysis

1. **Warmup Phase (Steps 1–100):** Learning rate scaled linearly from 0 to $2 	imes 10^{-5}$. The randomly initialized classification head stabilized, with rolling loss decreasing from 0.7035 to 0.6984.
2. **HaluEval Optimization (Steps 101–500):** Rapid descent in loss (reaching as low as 0.0029) as the model mastered the structured query-response pairs of HaluEval.
3. **RAGTruth Adaptation (Steps 501–1,000):** At step 500, the data shifted to RAGTruth records. An initial loss spike occurred (step 550 rolling loss: 1.1406) due to RAGTruth's more complex, long-context text distributions. The AdamW optimizer smoothly adapted, reducing rolling loss from 1.1406 down to **0.3397** by step 1,000 as learning rate decayed toward 0.
