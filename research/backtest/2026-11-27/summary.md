# Бэктест сигналов · 2026-11-27
111 тикеров, 2020-02-25 — 2026-09-04, удержание 5 торговых дней. Опцион: недельный ATM по Блэку–Шоулзу (IV = max(HV20, HV60)×1.15, +5% на спред), до экспирации. Статистика по дням: каждый день весит одинаково. t скорректирован на перекрытие окон (÷√5); |t| > 2 — заметно.

## Сигналы целиком

| signal | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | 1580 | 167790 | 0.5 | 0.2 | 53.7 | -15.0 | -84.6 | 15.0 | 2.92 |
| fade short: spike on a volume spike (news) | 1327 | 5772 | -0.6 | -0.2 | 44.4 | -34.6 | -100.0 | 9.3 | -1.78 |
| fade short: spike, no volume spike | 1483 | 24212 | -0.7 | -0.4 | 44.9 | -36.7 | -100.0 | 10.3 | -3.53 |
| rebound long: drop on a volume spike (news) | 1143 | 4870 | 0.5 | 0.2 | 53.2 | -21.3 | -86.6 | 17.7 | 1.42 |
| rebound long: fell with its sector, no volume spike | 1377 | 11673 | 0.4 | 0.1 | 55.9 | -20.7 | -74.0 | 17.4 | 1.45 |
| rebound long: own drop, no volume spike | 974 | 2271 | 0.9 | 0.7 | 54.7 | 3.2 | -69.5 | 20.1 | 2.27 |
| trend long | 1568 | 24122 | 0.6 | 0.3 | 54.0 | -14.0 | -83.6 | 14.5 | 3.03 |
| trend long, already stretched | 1492 | 22513 | 0.8 | 0.5 | 54.9 | -13.8 | -81.5 | 13.7 | 3.44 |
| trend short | 1561 | 22268 | -0.5 | -0.2 | 46.5 | -33.0 | -100.0 | 11.5 | -2.20 |
| trend short, already stretched | 1397 | 11961 | -0.5 | -0.2 | 44.0 | -35.1 | -100.0 | 13.1 | -1.82 |

## Сигналы по периодам (до/после 2023-06-30)

| signal | period | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | in-sample | 844 | 87157 | 0.5 | 0.2 | 53.5 | -17.5 | -85.6 | 14.5 | 1.64 |
| baseline: any stock, long | out-of-sample | 736 | 80633 | 0.6 | 0.2 | 53.9 | -12.1 | -83.4 | 15.5 | 2.79 |
| fade short: spike on a volume spike (news) | in-sample | 678 | 2652 | -0.2 | 0.1 | 44.2 | -34.2 | -100.0 | 10.0 | -0.50 |
| fade short: spike on a volume spike (news) | out-of-sample | 649 | 3120 | -0.9 | -0.6 | 44.6 | -35.1 | -100.0 | 8.8 | -1.98 |
| fade short: spike, no volume spike | in-sample | 773 | 12012 | -0.8 | -0.5 | 45.4 | -41.9 | -100.0 | 10.0 | -2.81 |
| fade short: spike, no volume spike | out-of-sample | 710 | 12200 | -0.6 | -0.3 | 44.5 | -31.0 | -100.0 | 10.6 | -2.15 |
| rebound long: drop on a volume spike (news) | in-sample | 562 | 2635 | 0.5 | 0.3 | 50.4 | -20.4 | -98.3 | 19.4 | 0.85 |
| rebound long: drop on a volume spike (news) | out-of-sample | 581 | 2235 | 0.5 | 0.1 | 56.5 | -22.1 | -75.4 | 15.7 | 1.27 |
| rebound long: fell with its sector, no volume spike | in-sample | 699 | 6007 | 0.3 | 0.1 | 55.6 | -21.3 | -74.2 | 17.9 | 0.71 |
| rebound long: fell with its sector, no volume spike | out-of-sample | 678 | 5666 | 0.5 | 0.1 | 56.3 | -20.2 | -73.5 | 16.9 | 1.52 |
| rebound long: own drop, no volume spike | in-sample | 465 | 1039 | 1.1 | 0.8 | 52.8 | 4.5 | -81.9 | 20.8 | 1.67 |
| rebound long: own drop, no volume spike | out-of-sample | 509 | 1232 | 0.8 | 0.5 | 56.2 | 2.1 | -62.9 | 19.6 | 1.55 |
| trend long | in-sample | 838 | 12084 | 0.5 | 0.2 | 53.7 | -17.9 | -85.2 | 13.1 | 1.70 |
| trend long | out-of-sample | 730 | 12038 | 0.8 | 0.4 | 54.3 | -9.6 | -82.4 | 15.9 | 2.69 |
| trend long, already stretched | in-sample | 781 | 10744 | 0.8 | 0.5 | 53.9 | -16.2 | -84.9 | 12.8 | 2.62 |
| trend long, already stretched | out-of-sample | 711 | 11769 | 0.7 | 0.4 | 55.8 | -11.2 | -78.6 | 14.5 | 2.25 |
| trend short | in-sample | 828 | 11373 | -0.4 | -0.1 | 46.7 | -31.2 | -100.0 | 11.7 | -1.11 |
| trend short | out-of-sample | 733 | 10895 | -0.7 | -0.3 | 46.4 | -35.0 | -100.0 | 11.4 | -2.39 |
| trend short, already stretched | in-sample | 711 | 6150 | -0.5 | -0.3 | 45.7 | -32.6 | -100.0 | 15.1 | -1.05 |
| trend short, already stretched | out-of-sample | 686 | 5811 | -0.5 | -0.2 | 42.2 | -37.6 | -100.0 | 11.0 | -1.75 |

## Сигналы по VIX

| signal | vix_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | VIX<17 | 536 | 58126 | 0.4 | 0.1 | 52.1 | -15.4 | -91.1 | 14.8 | 1.69 |
| baseline: any stock, long | 17-22 | 510 | 54599 | 0.3 | 0.2 | 52.5 | -18.4 | -89.7 | 14.3 | 1.22 |
| baseline: any stock, long | 22-28 | 328 | 34069 | 0.4 | 0.3 | 53.4 | -18.3 | -85.4 | 14.4 | 1.00 |
| baseline: any stock, long | VIX>=28 | 206 | 20996 | 1.7 | 0.6 | 61.6 | -0.2 | -53.1 | 18.3 | 1.98 |
| fade short: spike on a volume spike (news) | VIX<17 | 501 | 2819 | -0.8 | -0.5 | 43.6 | -38.5 | -100.0 | 9.0 | -1.71 |
| fade short: spike on a volume spike (news) | 17-22 | 433 | 1659 | -0.7 | -0.4 | 44.5 | -36.1 | -100.0 | 9.4 | -1.21 |
| fade short: spike on a volume spike (news) | 22-28 | 262 | 995 | -0.6 | -0.3 | 45.5 | -32.9 | -100.0 | 9.5 | -0.75 |
| fade short: spike on a volume spike (news) | VIX>=28 | 131 | 299 | 0.6 | 1.6 | 46.8 | -18.4 | -100.0 | 11.7 | 0.43 |
| fade short: spike, no volume spike | VIX<17 | 535 | 10532 | -0.6 | -0.4 | 45.4 | -34.8 | -100.0 | 11.1 | -2.24 |
| fade short: spike, no volume spike | 17-22 | 491 | 8180 | -0.5 | -0.4 | 45.0 | -34.6 | -100.0 | 10.1 | -1.74 |
| fade short: spike, no volume spike | 22-28 | 312 | 4423 | -0.5 | -0.3 | 45.7 | -35.2 | -100.0 | 9.8 | -0.93 |
| fade short: spike, no volume spike | VIX>=28 | 145 | 1077 | -2.5 | -0.8 | 37.0 | -53.7 | -100.0 | 5.6 | -2.31 |
| rebound long: drop on a volume spike (news) | VIX<17 | 386 | 1076 | 0.2 | 0.0 | 51.6 | -25.1 | -96.4 | 12.8 | 0.54 |
| rebound long: drop on a volume spike (news) | 17-22 | 384 | 1326 | 0.1 | -0.1 | 50.8 | -28.6 | -96.3 | 13.7 | 0.22 |
| rebound long: drop on a volume spike (news) | 22-28 | 227 | 1011 | 0.6 | 0.2 | 54.1 | -27.2 | -84.0 | 16.3 | 0.73 |
| rebound long: drop on a volume spike (news) | VIX>=28 | 146 | 1457 | 2.1 | 1.4 | 55.9 | 17.3 | -62.9 | 25.9 | 1.25 |
| rebound long: fell with its sector, no volume spike | VIX<17 | 471 | 2604 | 0.2 | -0.1 | 51.4 | -31.6 | -93.8 | 13.6 | 0.55 |
| rebound long: fell with its sector, no volume spike | 17-22 | 467 | 3906 | 0.3 | 0.0 | 53.8 | -18.8 | -84.4 | 15.7 | 0.61 |
| rebound long: fell with its sector, no volume spike | 22-28 | 271 | 2812 | 0.2 | 0.1 | 53.8 | -23.2 | -81.9 | 15.4 | 0.33 |
| rebound long: fell with its sector, no volume spike | VIX>=28 | 168 | 2351 | 1.7 | 0.8 | 67.1 | 8.4 | -12.9 | 26.7 | 1.38 |
| rebound long: own drop, no volume spike | VIX<17 | 347 | 728 | 0.4 | 0.1 | 51.9 | -9.8 | -89.4 | 17.7 | 0.64 |
| rebound long: own drop, no volume spike | 17-22 | 327 | 793 | 1.1 | 0.9 | 50.8 | 12.1 | -93.6 | 19.7 | 1.57 |
| rebound long: own drop, no volume spike | 22-28 | 175 | 434 | 1.4 | 1.1 | 61.1 | -6.4 | -44.9 | 21.2 | 1.71 |
| rebound long: own drop, no volume spike | VIX>=28 | 125 | 316 | 1.6 | 0.7 | 62.0 | 29.9 | -38.5 | 25.3 | 0.87 |
| trend long | VIX<17 | 534 | 9090 | 0.6 | 0.4 | 53.9 | -10.9 | -84.3 | 15.9 | 1.94 |
| trend long | 17-22 | 509 | 8310 | 0.3 | 0.1 | 50.9 | -20.2 | -95.9 | 12.7 | 0.91 |
| trend long | 22-28 | 328 | 4598 | 0.7 | 0.5 | 56.1 | -15.6 | -72.8 | 15.2 | 1.35 |
| trend long | VIX>=28 | 197 | 2124 | 1.6 | 0.4 | 61.8 | -4.1 | -59.3 | 13.8 | 2.04 |
| trend long, already stretched | VIX<17 | 534 | 10384 | 0.7 | 0.5 | 55.1 | -12.7 | -81.4 | 14.7 | 2.68 |
| trend long, already stretched | 17-22 | 492 | 7417 | 0.7 | 0.5 | 54.8 | -16.4 | -81.5 | 12.9 | 2.07 |
| trend long, already stretched | 22-28 | 321 | 3824 | 0.6 | 0.4 | 53.8 | -19.9 | -85.0 | 12.2 | 1.32 |
| trend long, already stretched | VIX>=28 | 145 | 888 | 1.4 | 0.1 | 58.6 | 4.7 | -66.5 | 14.6 | 1.02 |
| trend short | VIX<17 | 535 | 7051 | -0.2 | -0.0 | 48.7 | -32.3 | -100.0 | 11.6 | -0.86 |
| trend short | 17-22 | 508 | 7583 | -0.4 | -0.2 | 47.2 | -30.7 | -100.0 | 11.8 | -0.95 |
| trend short | 22-28 | 318 | 4290 | -0.2 | -0.0 | 48.1 | -29.9 | -100.0 | 12.7 | -0.35 |
| trend short | VIX>=28 | 200 | 3344 | -2.4 | -1.2 | 38.4 | -45.7 | -100.0 | 9.3 | -2.14 |
| trend short, already stretched | VIX<17 | 478 | 2649 | -0.4 | -0.2 | 46.5 | -40.4 | -100.0 | 11.3 | -1.19 |
| trend short, already stretched | 17-22 | 473 | 3800 | -0.3 | -0.1 | 46.4 | -31.2 | -100.0 | 13.6 | -0.69 |
| trend short, already stretched | 22-28 | 279 | 2457 | -0.3 | -0.2 | 46.7 | -36.5 | -100.0 | 12.7 | -0.50 |
| trend short, already stretched | VIX>=28 | 167 | 3055 | -1.8 | -0.9 | 36.6 | -28.2 | -100.0 | 14.3 | -1.27 |

## Сигналы по просадке S&P 500 от 3-мес. максимума

| signal | dd_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | SPX -10%+ | 177 | 18412 | 1.4 | 0.6 | 58.7 | -9.6 | -64.2 | 16.4 | 1.40 |
| baseline: any stock, long | SPX -5..-10% | 222 | 23509 | 0.5 | 0.1 | 54.8 | -10.8 | -78.1 | 16.0 | 0.75 |
| baseline: any stock, long | SPX near high | 1177 | 125453 | 0.4 | 0.2 | 52.8 | -16.5 | -88.6 | 14.6 | 2.69 |
| fade short: spike on a volume spike (news) | SPX -10%+ | 97 | 270 | 0.9 | 1.8 | 51.5 | -9.4 | -96.2 | 12.2 | 0.56 |
| fade short: spike on a volume spike (news) | SPX -5..-10% | 148 | 387 | -0.4 | -0.0 | 45.7 | -29.2 | -100.0 | 10.1 | -0.37 |
| fade short: spike on a volume spike (news) | SPX near high | 1078 | 5104 | -0.7 | -0.5 | 43.9 | -37.4 | -100.0 | 9.1 | -2.17 |
| fade short: spike, no volume spike | SPX -10%+ | 122 | 1312 | -1.5 | -0.3 | 41.4 | -43.5 | -100.0 | 6.2 | -1.34 |
| fade short: spike, no volume spike | SPX -5..-10% | 195 | 1692 | -0.6 | -0.2 | 40.8 | -25.3 | -100.0 | 10.2 | -0.69 |
| fade short: spike, no volume spike | SPX near high | 1164 | 21166 | -0.7 | -0.4 | 45.5 | -37.8 | -100.0 | 10.6 | -3.55 |
| rebound long: drop on a volume spike (news) | SPX -10%+ | 119 | 1156 | 2.4 | 2.0 | 52.3 | 10.9 | -88.4 | 23.4 | 1.19 |
| rebound long: drop on a volume spike (news) | SPX -5..-10% | 183 | 1076 | 0.3 | -0.0 | 57.7 | -13.9 | -62.1 | 20.2 | 0.33 |
| rebound long: drop on a volume spike (news) | SPX near high | 839 | 2598 | 0.3 | 0.0 | 52.1 | -27.3 | -92.1 | 14.3 | 0.86 |
| rebound long: fell with its sector, no volume spike | SPX -10%+ | 135 | 1637 | 2.1 | 1.5 | 63.1 | 12.2 | -34.2 | 23.8 | 1.33 |
| rebound long: fell with its sector, no volume spike | SPX -5..-10% | 206 | 3257 | 0.3 | -0.1 | 61.5 | -11.5 | -45.4 | 20.2 | 0.32 |
| rebound long: fell with its sector, no volume spike | SPX near high | 1032 | 6714 | 0.2 | -0.0 | 51.7 | -26.7 | -92.6 | 14.6 | 0.82 |
| rebound long: own drop, no volume spike | SPX -10%+ | 80 | 185 | 1.3 | 0.8 | 60.5 | 21.3 | -48.9 | 23.2 | 0.48 |
| rebound long: own drop, no volume spike | SPX -5..-10% | 161 | 456 | 1.8 | 1.4 | 59.6 | 15.7 | -36.0 | 22.1 | 1.67 |
| rebound long: own drop, no volume spike | SPX near high | 731 | 1623 | 0.7 | 0.4 | 52.5 | -1.7 | -85.1 | 19.1 | 1.79 |
| trend long | SPX -10%+ | 168 | 1242 | 0.7 | -0.1 | 56.3 | -19.2 | -79.5 | 9.9 | 0.76 |
| trend long | SPX -5..-10% | 222 | 2771 | 0.8 | 0.4 | 55.7 | -11.4 | -71.6 | 15.3 | 1.19 |
| trend long | SPX near high | 1174 | 20069 | 0.6 | 0.4 | 53.6 | -13.9 | -85.4 | 14.6 | 2.78 |
| trend long, already stretched | SPX -10%+ | 119 | 745 | 0.8 | 0.1 | 55.4 | -12.1 | -78.9 | 12.3 | 0.48 |
| trend long, already stretched | SPX -5..-10% | 198 | 1123 | 0.4 | 0.0 | 55.8 | -18.8 | -80.0 | 12.7 | 0.52 |
| trend long, already stretched | SPX near high | 1171 | 20599 | 0.8 | 0.6 | 54.8 | -13.0 | -81.7 | 13.8 | 4.16 |
| trend short | SPX -10%+ | 173 | 3540 | -2.2 | -1.3 | 38.4 | -42.7 | -100.0 | 8.1 | -1.74 |
| trend short | SPX -5..-10% | 220 | 3401 | -0.5 | -0.1 | 51.6 | -25.3 | -92.4 | 16.3 | -0.52 |
| trend short | SPX near high | 1164 | 15270 | -0.3 | -0.1 | 47.3 | -33.0 | -100.0 | 11.3 | -1.51 |
| trend short, already stretched | SPX -10%+ | 137 | 2466 | -2.2 | -1.7 | 39.3 | -31.0 | -100.0 | 14.9 | -1.28 |
| trend short, already stretched | SPX -5..-10% | 209 | 2980 | -0.1 | 0.1 | 41.7 | -20.9 | -100.0 | 12.2 | -0.13 |
| trend short, already stretched | SPX near high | 1047 | 6464 | -0.4 | -0.1 | 46.8 | -38.5 | -100.0 | 12.6 | -1.49 |

## Сигналы: паника (VIX>=25 или S&P -7% от максимума) против спокойного рынка

| signal | panic | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | False | 1177 | 126153 | 0.4 | 0.2 | 52.6 | -17.1 | -89.3 | 14.4 | 2.45 |
| baseline: any stock, long | True | 403 | 41637 | 1.0 | 0.4 | 57.0 | -8.7 | -69.9 | 16.6 | 1.75 |
| fade short: spike on a volume spike (news) | False | 1051 | 4952 | -0.7 | -0.5 | 44.0 | -36.7 | -100.0 | 8.9 | -2.09 |
| fade short: spike on a volume spike (news) | True | 276 | 820 | -0.1 | 0.6 | 46.7 | -26.9 | -100.0 | 12.2 | -0.09 |
| fade short: spike, no volume spike | False | 1165 | 20606 | -0.6 | -0.4 | 45.1 | -37.9 | -100.0 | 10.4 | -3.40 |
| fade short: spike, no volume spike | True | 318 | 3606 | -1.1 | -0.4 | 44.1 | -32.0 | -100.0 | 9.6 | -1.58 |
| rebound long: drop on a volume spike (news) | False | 861 | 2733 | 0.2 | -0.0 | 50.7 | -28.1 | -97.6 | 12.8 | 0.63 |
| rebound long: drop on a volume spike (news) | True | 282 | 2137 | 1.4 | 0.9 | 56.4 | -0.4 | -63.8 | 24.0 | 1.38 |
| rebound long: fell with its sector, no volume spike | False | 1051 | 7505 | 0.3 | 0.0 | 51.6 | -25.9 | -93.3 | 14.0 | 1.06 |
| rebound long: fell with its sector, no volume spike | True | 326 | 4168 | 0.8 | 0.4 | 63.8 | -4.1 | -30.2 | 23.6 | 1.00 |
| rebound long: own drop, no volume spike | False | 754 | 1707 | 0.7 | 0.5 | 52.4 | -2.4 | -84.7 | 18.6 | 1.89 |
| rebound long: own drop, no volume spike | True | 220 | 564 | 1.6 | 1.1 | 61.5 | 22.7 | -38.9 | 24.8 | 1.31 |
| trend long | False | 1174 | 19750 | 0.6 | 0.3 | 53.2 | -14.6 | -86.6 | 14.6 | 2.56 |
| trend long | True | 394 | 4372 | 0.9 | 0.3 | 57.4 | -12.3 | -69.9 | 13.9 | 1.67 |
| trend long, already stretched | False | 1163 | 19819 | 0.8 | 0.5 | 55.1 | -14.5 | -80.5 | 13.9 | 3.84 |
| trend long, already stretched | True | 329 | 2694 | 0.8 | 0.3 | 52.9 | -11.1 | -88.5 | 12.0 | 1.09 |
| trend short | False | 1172 | 15928 | -0.3 | -0.1 | 47.4 | -32.4 | -100.0 | 11.2 | -1.35 |
| trend short | True | 389 | 6340 | -1.3 | -0.7 | 44.4 | -34.8 | -100.0 | 12.3 | -1.76 |
| trend short, already stretched | False | 1063 | 7241 | -0.4 | -0.2 | 47.4 | -38.2 | -100.0 | 12.6 | -1.62 |
| trend short, already stretched | True | 334 | 4720 | -0.9 | -0.5 | 38.9 | -25.1 | -100.0 | 13.8 | -0.99 |

## Стратегии целиком

| rule | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|
| now | 4707 | 50.4 | 0.1 | 0.1 | -24.8 | -97.9 | 13.1 | -116,592.0 |
| rebound only | 2819 | 52.9 | 0.5 | 0.1 | -12.3 | -88.4 | 16.3 | -34,726.5 |
| regime | 4634 | 52.2 | 0.5 | 0.4 | -19.8 | -91.7 | 14.2 | -91,549.0 |

## Стратегии по периодам

| rule | period | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | in-sample | 2500 | 49.4 | 0.0 | 0.1 | -25.9 | -100.0 | 12.3 | -64,868.9 |
| now | out-of-sample | 2207 | 51.6 | 0.2 | 0.1 | -23.4 | -93.4 | 13.9 | -51,723.1 |
| rebound only | in-sample | 1387 | 52.1 | 0.3 | 0.1 | -14.2 | -90.3 | 15.9 | -19,640.3 |
| rebound only | out-of-sample | 1432 | 53.6 | 0.6 | 0.2 | -10.5 | -85.7 | 16.8 | -15,086.2 |
| regime | in-sample | 2455 | 51.0 | 0.4 | 0.3 | -22.0 | -96.3 | 13.2 | -54,120.9 |
| regime | out-of-sample | 2179 | 53.6 | 0.6 | 0.4 | -17.2 | -87.7 | 15.2 | -37,428.1 |

## Стратегии по годам

| rule | year | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | 2020 | 626 | 51.8 | 0.4 | 0.3 | -23.0 | -93.2 | 11.3 | -14,418.6 |
| now | 2021 | 756 | 50.4 | 0.1 | 0.2 | -26.5 | -97.5 | 12.4 | -20,035.1 |
| now | 2022 | 746 | 48.5 | -0.2 | 0.0 | -25.1 | -100.0 | 14.1 | -18,702.3 |
| now | 2023 | 749 | 48.2 | -0.3 | -0.3 | -28.7 | -100.0 | 11.9 | -21,506.6 |
| now | 2024 | 756 | 54.4 | 0.5 | 0.5 | -18.2 | -85.8 | 15.5 | -13,791.7 |
| now | 2025 | 750 | 49.7 | -0.1 | -0.1 | -28.4 | -100.0 | 12.4 | -21,295.3 |
| now | 2026 | 324 | 49.7 | 0.3 | 0.3 | -21.1 | -100.0 | 14.2 | -6,842.4 |
| rebound only | 2020 | 245 | 55.9 | 0.4 | 0.0 | -9.3 | -73.8 | 16.7 | -2,287.3 |
| rebound only | 2021 | 439 | 53.3 | 0.7 | 0.1 | -5.9 | -88.6 | 17.3 | -2,584.3 |
| rebound only | 2022 | 482 | 48.8 | -0.2 | 0.2 | -23.2 | -100.0 | 14.5 | -11,192.7 |
| rebound only | 2023 | 441 | 51.0 | 0.7 | 0.2 | -8.4 | -91.6 | 17.9 | -3,682.6 |
| rebound only | 2024 | 502 | 57.0 | 0.8 | 0.2 | -11.5 | -69.7 | 16.9 | -5,751.2 |
| rebound only | 2025 | 452 | 55.8 | 0.8 | 0.5 | -5.0 | -74.7 | 16.4 | -2,247.9 |
| rebound only | 2026 | 258 | 46.9 | -0.2 | -0.5 | -27.1 | -100.0 | 13.6 | -6,980.5 |
| regime | 2020 | 598 | 52.8 | 1.0 | 0.8 | -21.3 | -83.9 | 11.9 | -12,754.8 |
| regime | 2021 | 756 | 50.8 | 0.2 | 0.1 | -24.5 | -95.9 | 13.0 | -18,485.4 |
| regime | 2022 | 729 | 52.0 | 0.6 | 0.5 | -16.8 | -91.6 | 16.2 | -12,239.1 |
| regime | 2023 | 749 | 50.5 | 0.1 | -0.0 | -19.7 | -98.8 | 13.4 | -14,731.3 |
| regime | 2024 | 755 | 55.6 | 0.7 | 0.6 | -16.0 | -82.2 | 15.6 | -12,108.6 |
| regime | 2025 | 723 | 51.7 | 0.5 | 0.3 | -21.2 | -92.9 | 14.0 | -15,331.2 |
| regime | 2026 | 324 | 51.9 | 0.5 | 0.5 | -18.2 | -95.1 | 15.4 | -5,898.6 |

## Стратегии: паника против спокойного рынка

| rule | panic | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | False | 3530 | 50.8 | 0.3 | 0.3 | -24.9 | -97.0 | 13.2 | -87,734.1 |
| now | True | 1177 | 49.4 | -0.5 | -0.3 | -24.5 | -100.0 | 12.6 | -28,858.0 |
| rebound only | False | 2086 | 51.2 | 0.3 | 0.1 | -18.8 | -93.8 | 15.0 | -39,321.1 |
| rebound only | True | 733 | 57.6 | 0.9 | 0.3 | 6.3 | -65.0 | 20.2 | 4,594.6 |
| regime | False | 3528 | 50.8 | 0.3 | 0.3 | -24.9 | -97.0 | 13.1 | -87,733.7 |
| regime | True | 1106 | 56.6 | 1.2 | 0.7 | -3.4 | -74.5 | 17.5 | -3,815.3 |
