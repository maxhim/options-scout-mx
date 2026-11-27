# Бэктест сигналов · 2026-11-27
112 тикеров, 2020-02-25 — 2026-11-18, удержание 5 торговых дней. Опцион: недельный ATM по Блэку–Шоулзу (IV = max(HV20, HV60)×1.15, +5% на спред), до экспирации. Статистика по дням: каждый день весит одинаково. t скорректирован на перекрытие окон (÷√5); |t| > 2 — заметно.

## Сигналы целиком

| signal | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | 1694 | 182134 | 0.5 | 0.2 | 53.4 | -15.1 | -85.5 | 15.0 | 2.83 |
| fade short: spike on a volume spike (news) | 1426 | 6158 | -0.5 | -0.2 | 45.1 | -34.4 | -100.0 | 9.9 | -1.63 |
| fade short: spike, no volume spike | 1597 | 25887 | -0.7 | -0.4 | 45.2 | -36.2 | -100.0 | 10.4 | -3.38 |
| rebound long: drop on a volume spike (news) | 1236 | 5286 | 0.5 | 0.3 | 53.1 | -20.2 | -86.9 | 17.7 | 1.51 |
| rebound long: fell with its sector, no volume spike | 1487 | 12771 | 0.4 | 0.1 | 55.3 | -20.8 | -76.3 | 17.2 | 1.33 |
| rebound long: own drop, no volume spike | 1062 | 2478 | 0.7 | 0.5 | 54.0 | 0.0 | -75.3 | 19.7 | 1.81 |
| trend long | 1682 | 26781 | 0.6 | 0.3 | 53.7 | -14.6 | -84.9 | 14.5 | 2.91 |
| trend long, already stretched | 1608 | 24013 | 0.7 | 0.4 | 54.5 | -15.2 | -82.6 | 13.6 | 3.07 |
| trend short | 1675 | 24567 | -0.5 | -0.2 | 46.9 | -32.4 | -100.0 | 11.6 | -2.14 |
| trend short, already stretched | 1508 | 13063 | -0.5 | -0.2 | 44.5 | -34.0 | -100.0 | 13.1 | -1.73 |

## Сигналы по периодам (до/после 2023-06-30)

| signal | period | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | in-sample | 844 | 88001 | 0.5 | 0.2 | 53.4 | -17.6 | -85.7 | 14.5 | 1.62 |
| baseline: any stock, long | out-of-sample | 850 | 94133 | 0.5 | 0.2 | 53.4 | -12.6 | -85.2 | 15.5 | 2.58 |
| fade short: spike on a volume spike (news) | in-sample | 684 | 2681 | -0.2 | 0.1 | 44.3 | -34.3 | -100.0 | 10.1 | -0.46 |
| fade short: spike on a volume spike (news) | out-of-sample | 742 | 3477 | -0.8 | -0.5 | 45.8 | -34.5 | -100.0 | 9.8 | -1.76 |
| fade short: spike, no volume spike | in-sample | 773 | 12080 | -0.8 | -0.5 | 45.4 | -41.8 | -100.0 | 10.0 | -2.81 |
| fade short: spike, no volume spike | out-of-sample | 824 | 13807 | -0.5 | -0.3 | 45.0 | -30.9 | -100.0 | 10.8 | -1.96 |
| rebound long: drop on a volume spike (news) | in-sample | 564 | 2664 | 0.5 | 0.3 | 50.3 | -20.4 | -98.7 | 19.3 | 0.77 |
| rebound long: drop on a volume spike (news) | out-of-sample | 672 | 2622 | 0.6 | 0.3 | 55.9 | -20.1 | -77.8 | 16.2 | 1.48 |
| rebound long: fell with its sector, no volume spike | in-sample | 699 | 6101 | 0.3 | 0.1 | 55.7 | -20.9 | -74.2 | 17.9 | 0.76 |
| rebound long: fell with its sector, no volume spike | out-of-sample | 788 | 6670 | 0.4 | 0.0 | 55.0 | -20.6 | -78.1 | 16.5 | 1.19 |
| rebound long: own drop, no volume spike | in-sample | 467 | 1053 | 1.0 | 0.7 | 52.5 | 2.0 | -85.1 | 20.4 | 1.48 |
| rebound long: own drop, no volume spike | out-of-sample | 595 | 1425 | 0.5 | 0.3 | 55.2 | -1.5 | -67.4 | 19.1 | 1.08 |
| trend long | in-sample | 838 | 12188 | 0.5 | 0.2 | 53.7 | -18.2 | -85.2 | 13.0 | 1.67 |
| trend long | out-of-sample | 844 | 14593 | 0.7 | 0.4 | 53.8 | -11.1 | -84.7 | 15.7 | 2.49 |
| trend long, already stretched | in-sample | 783 | 10817 | 0.8 | 0.5 | 53.9 | -16.4 | -84.9 | 12.8 | 2.50 |
| trend long, already stretched | out-of-sample | 825 | 13196 | 0.6 | 0.3 | 55.1 | -14.1 | -81.0 | 14.3 | 1.88 |
| trend short | in-sample | 828 | 11535 | -0.5 | -0.2 | 46.6 | -31.3 | -100.0 | 11.6 | -1.13 |
| trend short | out-of-sample | 847 | 13032 | -0.6 | -0.3 | 47.1 | -33.5 | -100.0 | 11.6 | -2.12 |
| trend short, already stretched | in-sample | 711 | 6240 | -0.5 | -0.3 | 45.6 | -32.8 | -100.0 | 15.1 | -1.07 |
| trend short, already stretched | out-of-sample | 797 | 6823 | -0.5 | -0.2 | 43.5 | -35.1 | -100.0 | 11.3 | -1.48 |

## Сигналы по VIX

| signal | vix_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | VIX<17 | 600 | 65830 | 0.3 | 0.1 | 51.9 | -16.3 | -92.3 | 14.6 | 1.45 |
| baseline: any stock, long | 17-22 | 554 | 60036 | 0.3 | 0.2 | 52.4 | -17.4 | -89.8 | 14.6 | 1.24 |
| baseline: any stock, long | 22-28 | 333 | 34954 | 0.4 | 0.3 | 53.2 | -18.4 | -86.2 | 14.4 | 0.98 |
| baseline: any stock, long | VIX>=28 | 207 | 21314 | 1.7 | 0.6 | 61.5 | -0.1 | -53.0 | 18.3 | 1.99 |
| fade short: spike on a volume spike (news) | VIX<17 | 552 | 3040 | -0.6 | -0.4 | 45.1 | -36.6 | -100.0 | 10.1 | -1.27 |
| fade short: spike on a volume spike (news) | 17-22 | 474 | 1800 | -0.7 | -0.5 | 44.5 | -37.4 | -100.0 | 9.2 | -1.30 |
| fade short: spike on a volume spike (news) | 22-28 | 265 | 1007 | -0.6 | -0.3 | 45.6 | -32.7 | -100.0 | 9.8 | -0.76 |
| fade short: spike on a volume spike (news) | VIX>=28 | 135 | 311 | 0.5 | 1.5 | 47.6 | -17.9 | -100.0 | 12.5 | 0.40 |
| fade short: spike, no volume spike | VIX<17 | 599 | 11526 | -0.4 | -0.3 | 46.1 | -33.7 | -100.0 | 11.4 | -1.72 |
| fade short: spike, no volume spike | 17-22 | 535 | 8792 | -0.6 | -0.4 | 44.6 | -34.6 | -100.0 | 10.1 | -1.94 |
| fade short: spike, no volume spike | 22-28 | 317 | 4483 | -0.5 | -0.3 | 45.7 | -35.4 | -100.0 | 9.7 | -0.91 |
| fade short: spike, no volume spike | VIX>=28 | 146 | 1086 | -2.4 | -0.7 | 37.4 | -53.7 | -100.0 | 5.5 | -2.28 |
| rebound long: drop on a volume spike (news) | VIX<17 | 428 | 1241 | 0.2 | 0.1 | 50.4 | -26.1 | -98.5 | 12.5 | 0.57 |
| rebound long: drop on a volume spike (news) | 17-22 | 427 | 1490 | 0.3 | 0.1 | 51.0 | -24.1 | -95.3 | 14.3 | 0.48 |
| rebound long: drop on a volume spike (news) | 22-28 | 234 | 1062 | 0.5 | 0.1 | 54.0 | -27.8 | -84.1 | 16.0 | 0.57 |
| rebound long: drop on a volume spike (news) | VIX>=28 | 147 | 1493 | 2.3 | 1.6 | 56.7 | 19.9 | -60.6 | 26.8 | 1.32 |
| rebound long: fell with its sector, no volume spike | VIX<17 | 531 | 3073 | 0.2 | -0.0 | 51.0 | -31.0 | -95.8 | 13.3 | 0.45 |
| rebound long: fell with its sector, no volume spike | 17-22 | 511 | 4378 | 0.2 | -0.0 | 53.2 | -18.7 | -86.9 | 16.0 | 0.45 |
| rebound long: fell with its sector, no volume spike | 22-28 | 276 | 2933 | 0.3 | 0.1 | 53.4 | -22.7 | -83.8 | 15.2 | 0.37 |
| rebound long: fell with its sector, no volume spike | VIX>=28 | 169 | 2387 | 1.7 | 0.8 | 67.1 | 8.5 | -13.2 | 26.6 | 1.37 |
| rebound long: own drop, no volume spike | VIX<17 | 395 | 835 | 0.2 | 0.0 | 52.2 | -12.1 | -88.0 | 17.1 | 0.32 |
| rebound long: own drop, no volume spike | 17-22 | 362 | 876 | 0.9 | 0.7 | 49.8 | 9.5 | -100.0 | 19.6 | 1.34 |
| rebound long: own drop, no volume spike | 22-28 | 179 | 443 | 1.2 | 1.0 | 60.9 | -9.4 | -45.8 | 20.8 | 1.51 |
| rebound long: own drop, no volume spike | VIX>=28 | 126 | 324 | 1.2 | 0.3 | 60.8 | 24.3 | -44.3 | 24.7 | 0.67 |
| trend long | VIX<17 | 598 | 10531 | 0.4 | 0.3 | 53.4 | -13.1 | -86.5 | 15.4 | 1.49 |
| trend long | 17-22 | 553 | 9337 | 0.4 | 0.2 | 51.0 | -19.1 | -95.4 | 13.3 | 1.09 |
| trend long | 22-28 | 333 | 4746 | 0.7 | 0.5 | 55.9 | -16.0 | -73.9 | 15.2 | 1.33 |
| trend long | VIX>=28 | 198 | 2167 | 1.6 | 0.4 | 61.8 | -4.4 | -58.8 | 13.7 | 2.04 |
| trend long, already stretched | VIX<17 | 598 | 11300 | 0.6 | 0.4 | 54.2 | -14.8 | -84.2 | 14.4 | 2.05 |
| trend long, already stretched | 17-22 | 536 | 7937 | 0.7 | 0.5 | 55.0 | -17.2 | -80.3 | 13.1 | 2.00 |
| trend long, already stretched | 22-28 | 327 | 3876 | 0.6 | 0.4 | 53.7 | -21.0 | -85.1 | 12.2 | 1.20 |
| trend long, already stretched | VIX>=28 | 147 | 900 | 1.3 | 0.1 | 58.0 | 3.4 | -69.1 | 14.4 | 0.95 |
| trend short | VIX<17 | 599 | 8314 | -0.2 | -0.1 | 48.4 | -32.3 | -100.0 | 11.3 | -0.94 |
| trend short | 17-22 | 552 | 8433 | -0.3 | -0.1 | 48.0 | -29.3 | -100.0 | 12.5 | -0.80 |
| trend short | 22-28 | 323 | 4417 | -0.2 | 0.0 | 48.3 | -29.7 | -100.0 | 12.5 | -0.31 |
| trend short | VIX>=28 | 201 | 3403 | -2.4 | -1.2 | 38.4 | -45.6 | -100.0 | 9.3 | -2.16 |
| trend short, already stretched | VIX<17 | 539 | 3116 | -0.4 | -0.2 | 46.9 | -39.0 | -100.0 | 11.0 | -1.09 |
| trend short, already stretched | 17-22 | 517 | 4234 | -0.2 | -0.0 | 47.1 | -29.3 | -100.0 | 14.0 | -0.55 |
| trend short, already stretched | 22-28 | 284 | 2600 | -0.3 | -0.2 | 47.2 | -36.3 | -100.0 | 12.8 | -0.51 |
| trend short, already stretched | VIX>=28 | 168 | 3113 | -1.8 | -1.0 | 36.4 | -28.4 | -100.0 | 14.4 | -1.31 |

## Сигналы по просадке S&P 500 от 3-мес. максимума

| signal | dd_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | SPX -10%+ | 177 | 18589 | 1.4 | 0.6 | 58.7 | -9.6 | -64.4 | 16.4 | 1.38 |
| baseline: any stock, long | SPX -5..-10% | 227 | 24288 | 0.5 | 0.1 | 54.6 | -11.2 | -79.2 | 15.9 | 0.73 |
| baseline: any stock, long | SPX near high | 1288 | 139061 | 0.4 | 0.2 | 52.6 | -16.5 | -89.4 | 14.7 | 2.55 |
| fade short: spike on a volume spike (news) | SPX -10%+ | 99 | 274 | 0.8 | 1.6 | 51.5 | -10.1 | -96.2 | 12.4 | 0.48 |
| fade short: spike on a volume spike (news) | SPX -5..-10% | 153 | 401 | -0.3 | -0.0 | 46.1 | -27.8 | -100.0 | 10.7 | -0.33 |
| fade short: spike on a volume spike (news) | SPX near high | 1172 | 5479 | -0.6 | -0.4 | 44.8 | -37.2 | -100.0 | 9.7 | -1.95 |
| fade short: spike, no volume spike | SPX -10%+ | 122 | 1317 | -1.5 | -0.3 | 41.5 | -43.4 | -100.0 | 6.2 | -1.34 |
| fade short: spike, no volume spike | SPX -5..-10% | 200 | 1732 | -0.5 | -0.2 | 40.9 | -26.1 | -100.0 | 10.1 | -0.67 |
| fade short: spike, no volume spike | SPX near high | 1275 | 22838 | -0.6 | -0.4 | 45.7 | -37.1 | -100.0 | 10.7 | -3.30 |
| rebound long: drop on a volume spike (news) | SPX -10%+ | 119 | 1171 | 2.5 | 2.1 | 52.5 | 13.0 | -87.1 | 23.7 | 1.22 |
| rebound long: drop on a volume spike (news) | SPX -5..-10% | 189 | 1146 | 0.2 | -0.1 | 58.0 | -14.5 | -56.8 | 20.8 | 0.26 |
| rebound long: drop on a volume spike (news) | SPX near high | 926 | 2929 | 0.3 | 0.1 | 51.7 | -25.6 | -93.7 | 14.3 | 1.02 |
| rebound long: fell with its sector, no volume spike | SPX -10%+ | 135 | 1670 | 2.2 | 1.6 | 63.0 | 12.6 | -35.6 | 23.8 | 1.33 |
| rebound long: fell with its sector, no volume spike | SPX -5..-10% | 211 | 3368 | 0.3 | -0.0 | 61.0 | -11.3 | -48.1 | 20.0 | 0.36 |
| rebound long: fell with its sector, no volume spike | SPX near high | 1139 | 7672 | 0.2 | -0.1 | 51.3 | -26.4 | -93.9 | 14.5 | 0.66 |
| rebound long: own drop, no volume spike | SPX -10%+ | 81 | 193 | 0.8 | 0.3 | 60.1 | 15.2 | -54.4 | 22.8 | 0.31 |
| rebound long: own drop, no volume spike | SPX -5..-10% | 164 | 464 | 1.5 | 1.2 | 58.8 | 11.0 | -44.1 | 21.3 | 1.43 |
| rebound long: own drop, no volume spike | SPX near high | 816 | 1818 | 0.5 | 0.3 | 52.1 | -3.7 | -86.3 | 18.9 | 1.42 |
| trend long | SPX -10%+ | 168 | 1259 | 0.7 | -0.1 | 56.2 | -19.7 | -79.4 | 9.8 | 0.74 |
| trend long | SPX -5..-10% | 227 | 2907 | 0.7 | 0.4 | 55.5 | -12.6 | -72.9 | 15.1 | 1.15 |
| trend long | SPX near high | 1285 | 22608 | 0.6 | 0.3 | 53.3 | -14.3 | -86.5 | 14.6 | 2.64 |
| trend long, already stretched | SPX -10%+ | 119 | 747 | 0.7 | 0.1 | 55.3 | -12.1 | -79.0 | 12.3 | 0.46 |
| trend long, already stretched | SPX -5..-10% | 205 | 1157 | 0.3 | -0.0 | 55.4 | -20.7 | -80.5 | 12.5 | 0.37 |
| trend long, already stretched | SPX near high | 1282 | 22105 | 0.7 | 0.5 | 54.5 | -14.5 | -83.0 | 13.7 | 3.65 |
| trend short | SPX -10%+ | 173 | 3584 | -2.2 | -1.3 | 38.3 | -42.9 | -100.0 | 8.1 | -1.75 |
| trend short | SPX -5..-10% | 225 | 3531 | -0.4 | -0.1 | 51.9 | -24.8 | -91.7 | 16.1 | -0.48 |
| trend short | SPX near high | 1275 | 17438 | -0.3 | -0.1 | 47.6 | -32.4 | -100.0 | 11.4 | -1.42 |
| trend short, already stretched | SPX -10%+ | 137 | 2511 | -2.2 | -1.8 | 39.2 | -31.3 | -100.0 | 15.1 | -1.30 |
| trend short, already stretched | SPX -5..-10% | 214 | 3123 | -0.1 | 0.1 | 42.0 | -21.3 | -100.0 | 12.2 | -0.18 |
| trend short, already stretched | SPX near high | 1155 | 7383 | -0.3 | -0.1 | 47.2 | -36.8 | -100.0 | 12.7 | -1.33 |

## Сигналы: паника (VIX>=25 или S&P -7% от максимума) против спокойного рынка

| signal | panic | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | False | 1288 | 139759 | 0.4 | 0.2 | 52.4 | -17.1 | -90.0 | 14.5 | 2.29 |
| baseline: any stock, long | True | 406 | 42375 | 1.0 | 0.4 | 56.9 | -8.8 | -70.1 | 16.6 | 1.75 |
| fade short: spike on a volume spike (news) | False | 1144 | 5317 | -0.6 | -0.4 | 44.8 | -36.4 | -100.0 | 9.5 | -1.87 |
| fade short: spike on a volume spike (news) | True | 282 | 841 | -0.1 | 0.5 | 47.2 | -26.1 | -100.0 | 12.8 | -0.11 |
| fade short: spike, no volume spike | False | 1276 | 22250 | -0.6 | -0.4 | 45.3 | -37.1 | -100.0 | 10.5 | -3.15 |
| fade short: spike, no volume spike | True | 321 | 3637 | -1.1 | -0.3 | 44.1 | -32.4 | -100.0 | 9.5 | -1.58 |
| rebound long: drop on a volume spike (news) | False | 950 | 3079 | 0.3 | 0.1 | 50.3 | -26.4 | -98.5 | 12.9 | 0.78 |
| rebound long: drop on a volume spike (news) | True | 286 | 2207 | 1.4 | 1.0 | 56.9 | 0.3 | -62.1 | 24.5 | 1.38 |
| rebound long: fell with its sector, no volume spike | False | 1158 | 8514 | 0.2 | 0.0 | 51.2 | -25.6 | -94.6 | 14.0 | 0.86 |
| rebound long: fell with its sector, no volume spike | True | 329 | 4257 | 0.9 | 0.4 | 63.6 | -3.8 | -30.9 | 23.4 | 1.03 |
| rebound long: own drop, no volume spike | False | 840 | 1903 | 0.5 | 0.4 | 52.0 | -4.8 | -87.5 | 18.2 | 1.43 |
| rebound long: own drop, no volume spike | True | 222 | 575 | 1.4 | 0.8 | 60.9 | 18.5 | -44.0 | 24.3 | 1.12 |
| trend long | False | 1285 | 22289 | 0.5 | 0.3 | 53.0 | -15.1 | -87.8 | 14.6 | 2.42 |
| trend long | True | 397 | 4492 | 0.9 | 0.3 | 57.3 | -13.0 | -70.2 | 13.8 | 1.63 |
| trend long, already stretched | False | 1274 | 21292 | 0.6 | 0.5 | 54.8 | -16.0 | -81.8 | 13.8 | 3.33 |
| trend long, already stretched | True | 334 | 2721 | 0.7 | 0.2 | 52.7 | -12.2 | -89.8 | 11.9 | 0.99 |
| trend short | False | 1283 | 18100 | -0.3 | -0.1 | 47.7 | -31.7 | -100.0 | 11.4 | -1.25 |
| trend short | True | 392 | 6467 | -1.3 | -0.7 | 44.4 | -34.7 | -100.0 | 12.3 | -1.77 |
| trend short, already stretched | False | 1171 | 8215 | -0.4 | -0.1 | 47.8 | -36.5 | -100.0 | 12.7 | -1.42 |
| trend short, already stretched | True | 337 | 4848 | -0.9 | -0.5 | 38.9 | -25.4 | -100.0 | 13.9 | -1.03 |

## Стратегии целиком

| rule | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|
| now | 5048 | 50.1 | 0.0 | 0.1 | -25.5 | -99.1 | 13.1 | -128,741.1 |
| rebound only | 3093 | 52.6 | 0.3 | 0.1 | -12.8 | -89.5 | 16.3 | -39,549.6 |
| regime | 4979 | 51.8 | 0.4 | 0.3 | -20.8 | -93.4 | 14.0 | -103,746.2 |

## Стратегии по периодам

| rule | period | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | in-sample | 2500 | 49.2 | -0.0 | 0.1 | -26.9 | -100.0 | 12.3 | -67,226.5 |
| now | out-of-sample | 2548 | 50.9 | 0.1 | 0.1 | -24.1 | -96.8 | 13.8 | -61,514.6 |
| rebound only | in-sample | 1397 | 52.5 | 0.3 | 0.1 | -14.4 | -89.6 | 15.7 | -20,183.4 |
| rebound only | out-of-sample | 1696 | 52.7 | 0.4 | 0.1 | -11.4 | -88.7 | 16.8 | -19,366.2 |
| regime | in-sample | 2458 | 50.9 | 0.4 | 0.3 | -22.8 | -96.6 | 13.2 | -56,020.1 |
| regime | out-of-sample | 2521 | 52.6 | 0.5 | 0.3 | -18.9 | -91.8 | 14.8 | -47,726.1 |

## Стратегии по годам

| rule | year | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | 2020 | 626 | 51.6 | 0.3 | 0.3 | -24.1 | -93.4 | 11.3 | -15,090.1 |
| now | 2021 | 756 | 50.5 | 0.1 | 0.1 | -28.3 | -96.8 | 12.6 | -21,368.9 |
| now | 2022 | 746 | 48.3 | -0.3 | -0.0 | -25.5 | -100.0 | 13.9 | -19,010.2 |
| now | 2023 | 749 | 48.2 | -0.3 | -0.3 | -28.8 | -100.0 | 11.7 | -21,595.3 |
| now | 2024 | 755 | 54.3 | 0.6 | 0.5 | -17.0 | -86.1 | 15.8 | -12,802.5 |
| now | 2025 | 750 | 49.9 | -0.1 | -0.1 | -28.3 | -100.0 | 12.5 | -21,195.1 |
| now | 2026 | 666 | 47.9 | -0.1 | -0.1 | -26.5 | -100.0 | 13.4 | -17,678.9 |
| rebound only | 2020 | 248 | 56.0 | 0.3 | -0.1 | -11.1 | -72.9 | 16.1 | -2,742.4 |
| rebound only | 2021 | 440 | 53.2 | 0.6 | 0.1 | -6.5 | -89.1 | 17.3 | -2,840.6 |
| rebound only | 2022 | 486 | 49.4 | -0.2 | 0.2 | -23.3 | -100.0 | 14.2 | -11,303.1 |
| rebound only | 2023 | 444 | 51.8 | 0.8 | 0.2 | -7.1 | -89.3 | 18.0 | -3,154.9 |
| rebound only | 2024 | 503 | 57.1 | 0.8 | 0.2 | -11.2 | -69.6 | 17.1 | -5,614.7 |
| rebound only | 2025 | 452 | 56.0 | 0.8 | 0.5 | -4.9 | -74.2 | 16.4 | -2,209.8 |
| rebound only | 2026 | 520 | 46.9 | -0.6 | -0.6 | -22.5 | -100.0 | 15.2 | -11,684.0 |
| regime | 2020 | 600 | 53.3 | 1.0 | 0.8 | -20.5 | -80.9 | 12.0 | -12,298.4 |
| regime | 2021 | 756 | 50.5 | 0.2 | 0.1 | -26.8 | -96.8 | 13.0 | -20,224.0 |
| regime | 2022 | 730 | 51.8 | 0.5 | 0.5 | -17.5 | -92.2 | 16.0 | -12,793.6 |
| regime | 2023 | 749 | 50.5 | 0.1 | -0.0 | -20.1 | -98.8 | 13.1 | -15,033.6 |
| regime | 2024 | 755 | 55.8 | 0.8 | 0.6 | -14.7 | -82.0 | 16.0 | -11,099.3 |
| regime | 2025 | 723 | 51.7 | 0.4 | 0.2 | -21.5 | -94.2 | 13.8 | -15,543.9 |
| regime | 2026 | 666 | 48.6 | 0.1 | -0.0 | -25.2 | -100.0 | 13.8 | -16,753.4 |

## Стратегии: паника против спокойного рынка

| rule | panic | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | False | 3862 | 50.4 | 0.2 | 0.2 | -25.5 | -98.3 | 13.2 | -98,598.5 |
| now | True | 1186 | 49.2 | -0.6 | -0.4 | -25.4 | -100.0 | 12.6 | -30,142.5 |
| rebound only | False | 2349 | 51.1 | 0.2 | 0.0 | -18.5 | -94.3 | 15.2 | -43,394.0 |
| rebound only | True | 744 | 57.4 | 0.8 | 0.2 | 5.2 | -65.5 | 19.6 | 3,844.4 |
| regime | False | 3861 | 50.4 | 0.2 | 0.2 | -25.7 | -98.5 | 13.1 | -99,036.1 |
| regime | True | 1118 | 56.5 | 1.1 | 0.6 | -4.2 | -74.5 | 17.2 | -4,710.1 |
