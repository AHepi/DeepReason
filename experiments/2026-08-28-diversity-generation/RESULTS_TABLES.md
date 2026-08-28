
### Leg 1 — M1@Nmin at τ = 0.7454 (single linkage), n_min = 30

Mean over 9 repetitions, with (min–max) across those repetitions.

| arm | decay | geometry | technique | overall |
|---|---|---|---|---|
| A direct | 1.0 (1–1) | 1.0 (1–1) | 1.0 (1–1) | **1.0** |
| B stratified | 1.1 (1–2) | 1.0 (1–1) | 1.1 (1–2) | **1.1** |
| C verbalized sampling | 8.6 (5–16) | 1.0 (1–1) | 3.1 (1–5) | **4.2** |
| D stratified + VS | 3.2 (1–6) | 1.0 (1–1) | 3.2 (1–7) | **2.5** |

### Leg 1 — M2 (mean pairwise distance, threshold-free)

| arm | decay | geometry | technique | overall |
|---|---|---|---|---|
| A direct | 0.2078 | 0.0964 | 0.1798 | **0.1614** |
| B stratified | 0.2475 | 0.2027 | 0.2461 | **0.2321** |
| C verbalized sampling | 0.3272 | 0.1357 | 0.3021 | **0.2550** |
| D stratified + VS | 0.3241 | 0.2468 | 0.3288 | **0.2999** |

### Leg 1 — M3 (yield) and token spend

| arm | calls | valid candidates | parse fail | empty | off-format count | off-format prob | invalid % | tokens | tokens/candidate |
|---|---|---|---|---|---|---|---|---|---|
| A direct | 1620 | 1616 | 4 | 0 | 0 | 0 | 0.25% | 366,537 | 226.8 |
| B stratified | 1647 | 1608 | 12 | 0 | 0 | 0 | 0.73% | 435,302 | 270.7 |
| C verbalized sampling | 162 | 1579 | 4 | 1 | 0 | 0 | 0.31% | 148,795 | 94.2 |
| D stratified + VS | 189 | 1609 | 1 | 2 | 1 | 0 | 0.16% | 167,537 | 104.1 |

### Leg 1 — τ sensitivity (M1@Nmin, overall mean)

| arm | τ=0.6 | τ=0.65 | τ=0.7 | τ=0.75 | τ=0.8 | τ=0.85 | τ=0.9 |
|---|---|---|---|---|---|---|---|
| A direct | 1.0 | 1.0 | 1.0 | 1.0 | 1.3 | 5.6 | 15.0 |
| B stratified | 1.0 | 1.0 | 1.0 | 1.1 | 2.0 | 3.7 | 14.0 |
| C verbalized sampling | 1.0 | 1.0 | 1.1 | 4.8 | 13.7 | 17.6 | 21.6 |
| D stratified + VS | 1.0 | 1.0 | 1.2 | 2.8 | 9.7 | 18.8 | 26.7 |

### Leg 1 — verdicts

| | claim | verdict |
|---|---|---|
| **H1** | B > A on M1 (stratification; note row 5, grade B) | **INCONCLUSIVE** |
| **H2** | C > A on M1 (verbalized sampling; note row 7, grade C) | **INCONCLUSIVE** |
| **H3** | D >= B and D >= C on M1 | **INCONCLUSIVE** |
| **H4** | C's gain does not come with M3 degradation (<= 5pp over A) | **SUPPORTED** |

### Leg 2 — M1@Nmin at τ = 0.76 (complete linkage), n_min = 49

Mean over 9 repetitions, with (min–max) across those repetitions.

| arm | decay | geometry | technique | overall |
|---|---|---|---|---|
| A direct | 8.0 (7–11) | 1.7 (1–3) | 5.6 (4–7) | **5.1** |
| B stratified | 5.7 (5–8) | 6.0 (5–8) | 7.7 (5–11) | **6.4** |
| C verbalized sampling | 27.0 (23–31) | 3.4 (2–6) | 22.3 (20–25) | **17.6** |
| D stratified + VS | 23.7 (19–31) | 12.0 (9–17) | 24.2 (17–30) | **20.0** |

### Leg 2 — M2 (mean pairwise distance, threshold-free)

| arm | decay | geometry | technique | overall |
|---|---|---|---|---|
| A direct | 0.2010 | 0.1073 | 0.1781 | **0.1621** |
| B stratified | 0.2683 | 0.2359 | 0.2865 | **0.2636** |
| C verbalized sampling | 0.3199 | 0.1512 | 0.2993 | **0.2568** |
| D stratified + VS | 0.3390 | 0.2623 | 0.3425 | **0.3146** |

### Leg 2 — M3 (yield) and token spend

| arm | calls | valid candidates | parse fail | empty | off-format count | off-format prob | invalid % | tokens | tokens/candidate |
|---|---|---|---|---|---|---|---|---|---|
| A direct | 1620 | 1614 | 6 | 0 | 0 | 0 | 0.37% | 364,687 | 226.0 |
| B stratified | 1647 | 1611 | 9 | 0 | 0 | 0 | 0.55% | 437,457 | 271.5 |
| C verbalized sampling | 162 | 1589 | 3 | 1 | 0 | 0 | 0.25% | 150,324 | 94.6 |
| D stratified + VS | 189 | 1568 | 5 | 3 | 1 | 0 | 0.42% | 172,861 | 110.2 |

### Leg 2 — τ sensitivity (M1@Nmin, overall mean)

| arm | τ=0.72 | τ=0.74 | τ=0.76 | τ=0.78 | τ=0.8 |
|---|---|---|---|---|---|
| A direct | 3.1 | 3.9 | 5.1 | 6.9 | 8.9 |
| B stratified | 5.2 | 5.7 | 6.4 | 7.4 | 9.0 |
| C verbalized sampling | 13.0 | 15.1 | 17.6 | 21.0 | 24.3 |
| D stratified + VS | 13.0 | 16.7 | 20.0 | 23.8 | 28.1 |

### Leg 2 — verdicts

| | claim | verdict |
|---|---|---|
| **H1** | B > A on M1 (stratification; note row 5, grade B) | **INCONCLUSIVE** |
| **H2** | C > A on M1 (verbalized sampling; note row 7, grade C) | **INCONCLUSIVE** |
| **H3** | D >= B and D >= C on M1 | **INCONCLUSIVE** |
| **H4** | C's gain does not come with M3 degradation (<= 5pp over A) | **SUPPORTED** |

H4 detail: invalid rate A 0.37% vs C 0.25%, gap -0.12 percentage points (threshold: +5.00).
