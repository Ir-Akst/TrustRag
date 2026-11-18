# TrustRAG — Track 2, Step 3.8: Training Execution Log & Telemetry Audit

## 1. Execution Parameters
- **Command Executed:** `tools/training/train_nli_classifier.py --authorize-nli-training --max-train-samples 1000 --max-val-samples 2662 --learning-rate 2e-5 --warmup-steps 100 --weight-decay 0.01 --seed 42`
- **CPU Concurrency:** 16 execution threads (`torch.set_num_threads(16)`).
- **Optimizer Steps:** 1,000 steps (Batch size 1, Gradient accumulation 1).
- **Loss Function:** PyTorch CrossEntropyLoss.
- **Precision:** FP32 runtime.

---

## 2. Periodic Step Telemetry (Every 50 Steps)

| Step | Loss | Rolling Loss (50s) | Learning Rate | RSS (MB) | Available RAM (MB) | Elapsed Time (s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
|   50 | 0.9896 | 1.1364 | 9.80e-06 | 2401.8 | 3745.2 | 771.5 |
|  100 | 0.7558 | 1.0892 | 1.98e-05 | 2402.1 | 4582.2 | 859.5 |
|  150 | 1.3737 | 1.1020 | 1.89e-05 | 2318.5 | 4327.6 | 949.7 |
|  200 | 1.4336 | 1.1805 | 1.78e-05 | 2408.9 | 4198.6 | 1034.8 |
|  250 | 0.4239 | 0.9993 | 1.67e-05 | 2392.4 | 4238.8 | 1118.8 |
|  300 | 0.0446 | 1.1161 | 1.56e-05 | 2381.9 | 4242.3 | 1202.6 |
|  350 | 0.1634 | 1.7085 | 1.45e-05 | 2406.6 | 4650.9 | 1287.3 |
|  400 | 3.8934 | 1.4246 | 1.34e-05 | 2414.9 | 4730.1 | 1370.6 |
|  450 | 1.4011 | 1.0806 | 1.22e-05 | 2425.4 | 4673.9 | 1453.6 |
|  500 | 0.0102 | 1.7154 | 1.11e-05 | 2415.6 | 4682.2 | 1537.2 |
|  550 | 0.9203 | 1.5057 | 1.00e-05 | 2375.9 | 4685.9 | 1620.4 |
|  600 | 0.0156 | 1.5036 | 8.91e-06 | 2390.1 | 4702.4 | 1703.9 |
|  650 | 1.3091 | 1.0961 | 7.80e-06 | 2367.6 | 4705.0 | 1786.1 |
|  700 | 1.1715 | 1.5495 | 6.69e-06 | 2394.6 | 4502.4 | 1871.3 |
|  750 | 3.3917 | 2.0389 | 5.58e-06 | 2395.0 | 4385.3 | 1958.2 |
|  800 | 1.4526 | 1.5662 | 4.47e-06 | 2407.8 | 4319.5 | 2053.0 |
|  850 | 1.2602 | 0.8828 | 3.36e-06 | 2409.3 | 4319.6 | 2147.0 |
|  900 | 0.3484 | 0.7761 | 2.24e-06 | 2406.6 | 4280.2 | 2240.9 |
|  950 | 1.8829 | 0.6955 | 1.13e-06 | 2399.9 | 4417.3 | 2330.5 |
| 1000 | 1.2853 | 1.5756 | 2.22e-08 | 2406.6 | 4532.6 | 2414.2 |

---

## 3. Watchdog Audit
- **RAM Breaches:** 0 (Minimum observed available RAM remained well above 700 MB cutoff).
- **Swap Growth Breaches:** 0 (Swap usage remained stable, growth < 500 MB).
- **Timeout Breaches:** 0 (Completed within the 3,600s ceiling).
