# Бэктест сигналов · 2026-11-27
112 тикеров, 2020-02-25 — 2026-09-04, удержание 5 торговых дней. Опцион: недельный ATM по Блэку–Шоулзу (IV = max(HV20, HV60)×1.15, +5% на спред), до экспирации. Статистика по дням: каждый день весит одинаково. t скорректирован на перекрытие окон (÷√5); |t| > 2 — заметно.

## Сигналы целиком

| signal | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | 1580 | 169370 | 0.5 | 0.2 | 53.7 | -14.9 | -84.5 | 15.0 | 2.93 |
| fade short: spike on a volume spike (news) | 1333 | 5842 | -0.5 | -0.2 | 44.6 | -34.6 | -100.0 | 9.4 | -1.73 |
| fade short: spike, no volume spike | 1483 | 24455 | -0.7 | -0.4 | 44.8 | -36.7 | -100.0 | 10.3 | -3.55 |
| rebound long: drop on a volume spike (news) | 1145 | 4922 | 0.5 | 0.2 | 53.2 | -21.2 | -86.6 | 17.7 | 1.36 |
| rebound long: fell with its sector, no volume spike | 1377 | 11782 | 0.4 | 0.1 | 56.0 | -20.2 | -73.7 | 17.5 | 1.54 |
| rebound long: own drop, no volume spike | 976 | 2293 | 0.8 | 0.5 | 54.5 | 1.6 | -71.8 | 19.9 | 2.06 |
| trend long | 1568 | 24423 | 0.6 | 0.3 | 54.1 | -14.2 | -83.4 | 14.5 | 3.04 |
| trend long, already stretched | 1494 | 22776 | 0.8 | 0.5 | 54.9 | -13.8 | -81.4 | 13.7 | 3.36 |
| trend short | 1561 | 22481 | -0.6 | -0.2 | 46.5 | -33.0 | -100.0 | 11.5 | -2.21 |
| trend short, already stretched | 1397 | 12072 | -0.5 | -0.2 | 43.9 | -35.1 | -100.0 | 13.1 | -1.84 |

## Сигналы по периодам (до/после 2023-06-30)

| signal | period | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | in-sample | 844 | 88001 | 0.5 | 0.2 | 53.4 | -17.6 | -85.7 | 14.5 | 1.62 |
| baseline: any stock, long | out-of-sample | 736 | 81369 | 0.6 | 0.3 | 54.0 | -11.8 | -83.0 | 15.6 | 2.84 |
| fade short: spike on a volume spike (news) | in-sample | 684 | 2681 | -0.2 | 0.1 | 44.3 | -34.3 | -100.0 | 10.1 | -0.46 |
| fade short: spike on a volume spike (news) | out-of-sample | 649 | 3161 | -0.9 | -0.6 | 44.8 | -35.0 | -100.0 | 8.9 | -1.95 |
| fade short: spike, no volume spike | in-sample | 773 | 12080 | -0.8 | -0.5 | 45.4 | -41.8 | -100.0 | 10.0 | -2.81 |
| fade short: spike, no volume spike | out-of-sample | 710 | 12375 | -0.6 | -0.3 | 44.3 | -31.1 | -100.0 | 10.6 | -2.18 |
| rebound long: drop on a volume spike (news) | in-sample | 564 | 2664 | 0.5 | 0.3 | 50.3 | -20.4 | -98.7 | 19.3 | 0.77 |
| rebound long: drop on a volume spike (news) | out-of-sample | 581 | 2258 | 0.5 | 0.1 | 56.6 | -22.1 | -75.0 | 15.9 | 1.29 |
| rebound long: fell with its sector, no volume spike | in-sample | 699 | 6101 | 0.3 | 0.1 | 55.7 | -20.9 | -74.2 | 17.9 | 0.76 |
| rebound long: fell with its sector, no volume spike | out-of-sample | 678 | 5681 | 0.5 | 0.1 | 56.4 | -19.5 | -73.1 | 17.0 | 1.61 |
| rebound long: own drop, no volume spike | in-sample | 467 | 1053 | 1.0 | 0.7 | 52.5 | 2.0 | -85.1 | 20.4 | 1.48 |
| rebound long: own drop, no volume spike | out-of-sample | 509 | 1240 | 0.7 | 0.4 | 56.1 | 1.3 | -63.4 | 19.4 | 1.45 |
| trend long | in-sample | 838 | 12188 | 0.5 | 0.2 | 53.7 | -18.2 | -85.2 | 13.0 | 1.67 |
| trend long | out-of-sample | 730 | 12235 | 0.8 | 0.4 | 54.5 | -9.7 | -81.9 | 16.0 | 2.74 |
| trend long, already stretched | in-sample | 783 | 10817 | 0.8 | 0.5 | 53.9 | -16.4 | -84.9 | 12.8 | 2.50 |
| trend long, already stretched | out-of-sample | 711 | 11959 | 0.7 | 0.4 | 55.9 | -10.9 | -78.2 | 14.5 | 2.26 |
| trend short | in-sample | 828 | 11535 | -0.5 | -0.2 | 46.6 | -31.3 | -100.0 | 11.6 | -1.13 |
| trend short | out-of-sample | 733 | 10946 | -0.7 | -0.3 | 46.3 | -34.9 | -100.0 | 11.4 | -2.38 |
| trend short, already stretched | in-sample | 711 | 6240 | -0.5 | -0.3 | 45.6 | -32.8 | -100.0 | 15.1 | -1.07 |
| trend short, already stretched | out-of-sample | 686 | 5832 | -0.5 | -0.2 | 42.1 | -37.5 | -100.0 | 11.0 | -1.75 |

## Сигналы по VIX

| signal | vix_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | VIX<17 | 536 | 58662 | 0.4 | 0.1 | 52.2 | -15.2 | -90.8 | 14.9 | 1.73 |
| baseline: any stock, long | 17-22 | 510 | 55109 | 0.4 | 0.2 | 52.5 | -18.4 | -89.6 | 14.3 | 1.24 |
| baseline: any stock, long | 22-28 | 328 | 34397 | 0.4 | 0.3 | 53.4 | -18.3 | -85.4 | 14.4 | 1.00 |
| baseline: any stock, long | VIX>=28 | 206 | 21202 | 1.7 | 0.6 | 61.5 | -0.3 | -53.2 | 18.2 | 1.97 |
| fade short: spike on a volume spike (news) | VIX<17 | 502 | 2855 | -0.7 | -0.5 | 43.9 | -38.6 | -100.0 | 9.1 | -1.69 |
| fade short: spike on a volume spike (news) | 17-22 | 435 | 1680 | -0.6 | -0.4 | 44.6 | -36.2 | -100.0 | 9.3 | -1.15 |
| fade short: spike on a volume spike (news) | 22-28 | 262 | 1000 | -0.6 | -0.3 | 45.5 | -32.8 | -100.0 | 9.7 | -0.75 |
| fade short: spike on a volume spike (news) | VIX>=28 | 134 | 307 | 0.5 | 1.5 | 47.6 | -18.1 | -100.0 | 12.4 | 0.40 |
| fade short: spike, no volume spike | VIX<17 | 535 | 10638 | -0.6 | -0.4 | 45.3 | -34.8 | -100.0 | 11.1 | -2.27 |
| fade short: spike, no volume spike | 17-22 | 491 | 8282 | -0.6 | -0.4 | 44.8 | -34.8 | -100.0 | 10.0 | -1.78 |
| fade short: spike, no volume spike | 22-28 | 312 | 4453 | -0.5 | -0.3 | 45.7 | -35.1 | -100.0 | 9.7 | -0.91 |
| fade short: spike, no volume spike | VIX>=28 | 145 | 1082 | -2.5 | -0.7 | 37.2 | -53.5 | -100.0 | 5.5 | -2.29 |
| rebound long: drop on a volume spike (news) | VIX<17 | 386 | 1082 | 0.2 | 0.0 | 51.6 | -25.1 | -96.4 | 12.8 | 0.53 |
| rebound long: drop on a volume spike (news) | 17-22 | 384 | 1336 | 0.1 | -0.1 | 50.7 | -28.6 | -97.2 | 13.8 | 0.23 |
| rebound long: drop on a volume spike (news) | 22-28 | 229 | 1035 | 0.5 | 0.1 | 53.8 | -28.0 | -85.2 | 16.0 | 0.56 |
| rebound long: drop on a volume spike (news) | VIX>=28 | 146 | 1469 | 2.2 | 1.5 | 56.2 | 18.9 | -62.3 | 26.1 | 1.27 |
| rebound long: fell with its sector, no volume spike | VIX<17 | 471 | 2618 | 0.2 | -0.0 | 51.5 | -30.8 | -93.2 | 13.8 | 0.64 |
| rebound long: fell with its sector, no volume spike | 17-22 | 467 | 3931 | 0.3 | 0.0 | 53.9 | -18.7 | -84.4 | 15.8 | 0.65 |
| rebound long: fell with its sector, no volume spike | 22-28 | 271 | 2851 | 0.3 | 0.2 | 53.9 | -22.3 | -81.5 | 15.5 | 0.40 |
| rebound long: fell with its sector, no volume spike | VIX>=28 | 168 | 2382 | 1.7 | 0.8 | 67.0 | 8.3 | -13.3 | 26.7 | 1.35 |
| rebound long: own drop, no volume spike | VIX<17 | 346 | 729 | 0.3 | 0.1 | 52.1 | -10.5 | -88.9 | 17.7 | 0.55 |
| rebound long: own drop, no volume spike | 17-22 | 329 | 803 | 1.0 | 0.9 | 50.3 | 11.0 | -96.8 | 19.3 | 1.49 |
| rebound long: own drop, no volume spike | 22-28 | 175 | 437 | 1.3 | 1.1 | 61.3 | -8.3 | -45.3 | 21.1 | 1.65 |
| rebound long: own drop, no volume spike | VIX>=28 | 126 | 324 | 1.2 | 0.3 | 60.8 | 24.3 | -44.3 | 24.7 | 0.67 |
| trend long | VIX<17 | 534 | 9226 | 0.6 | 0.4 | 54.1 | -10.7 | -83.5 | 16.1 | 2.00 |
| trend long | 17-22 | 509 | 8411 | 0.3 | 0.1 | 51.0 | -20.5 | -95.8 | 12.7 | 0.90 |
| trend long | 22-28 | 328 | 4643 | 0.7 | 0.5 | 56.0 | -16.2 | -73.6 | 15.1 | 1.30 |
| trend long | VIX>=28 | 197 | 2143 | 1.6 | 0.4 | 62.0 | -4.2 | -58.4 | 13.9 | 2.05 |
| trend long, already stretched | VIX<17 | 534 | 10510 | 0.8 | 0.5 | 55.0 | -12.2 | -81.5 | 14.7 | 2.69 |
| trend long, already stretched | 17-22 | 492 | 7524 | 0.7 | 0.5 | 55.0 | -16.4 | -80.7 | 12.9 | 2.10 |
| trend long, already stretched | 22-28 | 322 | 3847 | 0.6 | 0.4 | 53.8 | -20.4 | -85.0 | 12.2 | 1.21 |
| trend long, already stretched | VIX>=28 | 146 | 895 | 1.3 | 0.1 | 58.1 | 3.9 | -68.3 | 14.5 | 0.95 |
| trend short | VIX<17 | 535 | 7102 | -0.2 | -0.0 | 48.7 | -32.2 | -100.0 | 11.6 | -0.85 |
| trend short | 17-22 | 508 | 7664 | -0.4 | -0.2 | 47.2 | -30.9 | -100.0 | 11.8 | -0.97 |
| trend short | 22-28 | 318 | 4327 | -0.2 | -0.0 | 48.0 | -29.7 | -100.0 | 12.7 | -0.34 |
| trend short | VIX>=28 | 200 | 3388 | -2.4 | -1.2 | 38.4 | -45.6 | -100.0 | 9.3 | -2.14 |
| trend short, already stretched | VIX<17 | 478 | 2653 | -0.4 | -0.2 | 46.5 | -40.4 | -100.0 | 11.3 | -1.19 |
| trend short, already stretched | 17-22 | 473 | 3822 | -0.3 | -0.1 | 46.4 | -31.4 | -100.0 | 13.5 | -0.70 |
| trend short, already stretched | 22-28 | 279 | 2507 | -0.4 | -0.2 | 46.5 | -36.5 | -100.0 | 12.8 | -0.53 |
| trend short, already stretched | VIX>=28 | 167 | 3090 | -1.8 | -0.9 | 36.6 | -28.1 | -100.0 | 14.4 | -1.26 |

## Сигналы по просадке S&P 500 от 3-мес. максимума

| signal | dd_b | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | SPX -10%+ | 177 | 18589 | 1.4 | 0.6 | 58.7 | -9.6 | -64.4 | 16.4 | 1.38 |
| baseline: any stock, long | SPX -5..-10% | 222 | 23731 | 0.5 | 0.1 | 54.8 | -10.8 | -78.2 | 16.0 | 0.74 |
| baseline: any stock, long | SPX near high | 1177 | 126630 | 0.4 | 0.2 | 52.8 | -16.4 | -88.4 | 14.6 | 2.72 |
| fade short: spike on a volume spike (news) | SPX -10%+ | 99 | 274 | 0.8 | 1.6 | 51.5 | -10.1 | -96.2 | 12.4 | 0.48 |
| fade short: spike on a volume spike (news) | SPX -5..-10% | 149 | 390 | -0.3 | -0.0 | 45.9 | -28.3 | -100.0 | 10.3 | -0.32 |
| fade short: spike on a volume spike (news) | SPX near high | 1081 | 5167 | -0.7 | -0.4 | 44.1 | -37.5 | -100.0 | 9.2 | -2.11 |
| fade short: spike, no volume spike | SPX -10%+ | 122 | 1317 | -1.5 | -0.3 | 41.5 | -43.4 | -100.0 | 6.2 | -1.34 |
| fade short: spike, no volume spike | SPX -5..-10% | 195 | 1705 | -0.6 | -0.2 | 40.7 | -25.2 | -100.0 | 10.1 | -0.69 |
| fade short: spike, no volume spike | SPX near high | 1164 | 21391 | -0.7 | -0.4 | 45.4 | -37.9 | -100.0 | 10.5 | -3.58 |
| rebound long: drop on a volume spike (news) | SPX -10%+ | 119 | 1171 | 2.5 | 2.1 | 52.5 | 13.0 | -87.1 | 23.7 | 1.22 |
| rebound long: drop on a volume spike (news) | SPX -5..-10% | 184 | 1098 | 0.2 | -0.1 | 57.5 | -14.6 | -62.4 | 19.9 | 0.22 |
| rebound long: drop on a volume spike (news) | SPX near high | 840 | 2613 | 0.3 | 0.0 | 52.0 | -27.5 | -92.2 | 14.3 | 0.82 |
| rebound long: fell with its sector, no volume spike | SPX -10%+ | 135 | 1670 | 2.2 | 1.6 | 63.0 | 12.6 | -35.6 | 23.8 | 1.33 |
| rebound long: fell with its sector, no volume spike | SPX -5..-10% | 206 | 3288 | 0.3 | -0.1 | 61.5 | -11.1 | -45.0 | 20.3 | 0.35 |
| rebound long: fell with its sector, no volume spike | SPX near high | 1032 | 6757 | 0.2 | -0.0 | 51.8 | -26.2 | -92.2 | 14.7 | 0.92 |
| rebound long: own drop, no volume spike | SPX -10%+ | 81 | 193 | 0.8 | 0.3 | 60.1 | 15.2 | -54.4 | 22.8 | 0.31 |
| rebound long: own drop, no volume spike | SPX -5..-10% | 161 | 459 | 1.6 | 1.3 | 59.3 | 12.9 | -41.9 | 21.6 | 1.55 |
| rebound long: own drop, no volume spike | SPX near high | 732 | 1634 | 0.6 | 0.4 | 52.3 | -2.6 | -86.1 | 19.0 | 1.69 |
| trend long | SPX -10%+ | 168 | 1259 | 0.7 | -0.1 | 56.2 | -19.7 | -79.4 | 9.8 | 0.74 |
| trend long | SPX -5..-10% | 222 | 2797 | 0.8 | 0.4 | 55.7 | -11.9 | -71.6 | 15.3 | 1.17 |
| trend long | SPX near high | 1174 | 20327 | 0.6 | 0.4 | 53.7 | -13.9 | -85.2 | 14.7 | 2.80 |
| trend long, already stretched | SPX -10%+ | 119 | 747 | 0.7 | 0.1 | 55.3 | -12.1 | -79.0 | 12.3 | 0.46 |
| trend long, already stretched | SPX -5..-10% | 200 | 1127 | 0.3 | -0.0 | 55.7 | -19.6 | -80.2 | 12.8 | 0.39 |
| trend long, already stretched | SPX near high | 1171 | 20856 | 0.8 | 0.6 | 54.9 | -12.8 | -81.5 | 13.8 | 4.17 |
| trend short | SPX -10%+ | 173 | 3584 | -2.2 | -1.3 | 38.3 | -42.9 | -100.0 | 8.1 | -1.75 |
| trend short | SPX -5..-10% | 220 | 3440 | -0.5 | -0.1 | 51.5 | -24.8 | -92.4 | 16.4 | -0.51 |
| trend short | SPX near high | 1164 | 15398 | -0.3 | -0.1 | 47.2 | -33.1 | -100.0 | 11.3 | -1.52 |
| trend short, already stretched | SPX -10%+ | 137 | 2511 | -2.2 | -1.8 | 39.2 | -31.3 | -100.0 | 15.1 | -1.30 |
| trend short, already stretched | SPX -5..-10% | 209 | 3014 | -0.1 | 0.1 | 41.6 | -20.9 | -100.0 | 12.3 | -0.14 |
| trend short, already stretched | SPX near high | 1047 | 6496 | -0.4 | -0.1 | 46.7 | -38.5 | -100.0 | 12.6 | -1.50 |

## Сигналы: паника (VIX>=25 или S&P -7% от максимума) против спокойного рынка

| signal | panic | days | events | avg % | vs SPY % | hit % | option avg % | option median % | option x2 % | t |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline: any stock, long | False | 1177 | 127330 | 0.4 | 0.2 | 52.6 | -17.0 | -89.1 | 14.5 | 2.49 |
| baseline: any stock, long | True | 403 | 42040 | 1.0 | 0.4 | 57.0 | -8.8 | -70.0 | 16.6 | 1.74 |
| fade short: spike on a volume spike (news) | False | 1054 | 5011 | -0.7 | -0.4 | 44.2 | -36.7 | -100.0 | 8.9 | -2.02 |
| fade short: spike on a volume spike (news) | True | 279 | 831 | -0.1 | 0.5 | 47.1 | -26.6 | -100.0 | 12.6 | -0.11 |
| fade short: spike, no volume spike | False | 1165 | 20830 | -0.6 | -0.4 | 45.0 | -38.0 | -100.0 | 10.4 | -3.43 |
| fade short: spike, no volume spike | True | 318 | 3625 | -1.1 | -0.3 | 44.1 | -31.9 | -100.0 | 9.5 | -1.58 |
| rebound long: drop on a volume spike (news) | False | 862 | 2755 | 0.2 | -0.0 | 50.6 | -28.2 | -97.6 | 12.8 | 0.58 |
| rebound long: drop on a volume spike (news) | True | 283 | 2167 | 1.4 | 0.9 | 56.4 | 0.0 | -62.9 | 24.0 | 1.35 |
| rebound long: fell with its sector, no volume spike | False | 1051 | 7565 | 0.3 | 0.1 | 51.7 | -25.4 | -92.9 | 14.1 | 1.16 |
| rebound long: fell with its sector, no volume spike | True | 326 | 4217 | 0.8 | 0.4 | 63.8 | -3.8 | -30.5 | 23.5 | 1.01 |
| rebound long: own drop, no volume spike | False | 755 | 1719 | 0.7 | 0.5 | 52.3 | -3.5 | -85.4 | 18.4 | 1.77 |
| rebound long: own drop, no volume spike | True | 221 | 574 | 1.4 | 0.8 | 61.0 | 19.1 | -43.3 | 24.4 | 1.13 |
| trend long | False | 1174 | 20003 | 0.6 | 0.3 | 53.3 | -14.6 | -86.4 | 14.7 | 2.61 |
| trend long | True | 394 | 4420 | 0.9 | 0.3 | 57.3 | -12.9 | -70.0 | 13.9 | 1.63 |
| trend long, already stretched | False | 1163 | 20070 | 0.8 | 0.5 | 55.2 | -14.4 | -80.2 | 13.9 | 3.85 |
| trend long, already stretched | True | 331 | 2706 | 0.7 | 0.2 | 52.8 | -11.8 | -89.5 | 11.9 | 0.99 |
| trend short | False | 1172 | 16067 | -0.3 | -0.1 | 47.4 | -32.4 | -100.0 | 11.2 | -1.36 |
| trend short | True | 389 | 6414 | -1.3 | -0.7 | 44.3 | -34.7 | -100.0 | 12.3 | -1.76 |
| trend short, already stretched | False | 1063 | 7290 | -0.4 | -0.2 | 47.3 | -38.3 | -100.0 | 12.6 | -1.64 |
| trend short, already stretched | True | 334 | 4782 | -0.9 | -0.5 | 38.9 | -25.1 | -100.0 | 13.9 | -0.99 |

## Стратегии целиком

| rule | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|
| now | 4706 | 50.4 | 0.1 | 0.1 | -25.0 | -98.1 | 13.2 | -117,492.0 |
| rebound only | 2831 | 53.1 | 0.5 | 0.1 | -12.3 | -87.5 | 16.2 | -34,846.1 |
| regime | 4637 | 52.2 | 0.5 | 0.4 | -20.0 | -91.7 | 14.2 | -92,560.8 |

## Стратегии по периодам

| rule | period | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | in-sample | 2500 | 49.2 | -0.0 | 0.1 | -26.9 | -100.0 | 12.3 | -67,226.5 |
| now | out-of-sample | 2206 | 51.7 | 0.2 | 0.2 | -22.8 | -93.3 | 14.1 | -50,265.5 |
| rebound only | in-sample | 1397 | 52.5 | 0.3 | 0.1 | -14.4 | -89.6 | 15.7 | -20,183.4 |
| rebound only | out-of-sample | 1434 | 53.7 | 0.7 | 0.2 | -10.2 | -85.1 | 16.8 | -14,662.7 |
| regime | in-sample | 2458 | 50.9 | 0.4 | 0.3 | -22.8 | -96.6 | 13.2 | -56,020.1 |
| regime | out-of-sample | 2179 | 53.6 | 0.6 | 0.4 | -16.8 | -87.7 | 15.2 | -36,540.7 |

## Стратегии по годам

| rule | year | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | 2020 | 626 | 51.6 | 0.3 | 0.3 | -24.1 | -93.4 | 11.3 | -15,090.1 |
| now | 2021 | 756 | 50.5 | 0.1 | 0.1 | -28.3 | -96.8 | 12.6 | -21,368.9 |
| now | 2022 | 746 | 48.3 | -0.3 | -0.0 | -25.5 | -100.0 | 13.9 | -19,010.2 |
| now | 2023 | 749 | 48.2 | -0.3 | -0.3 | -28.8 | -100.0 | 11.7 | -21,595.3 |
| now | 2024 | 755 | 54.3 | 0.6 | 0.5 | -17.0 | -86.1 | 15.8 | -12,802.5 |
| now | 2025 | 750 | 49.9 | -0.1 | -0.1 | -28.3 | -100.0 | 12.5 | -21,195.1 |
| now | 2026 | 324 | 49.7 | 0.5 | 0.5 | -19.8 | -100.0 | 14.8 | -6,429.8 |
| rebound only | 2020 | 248 | 56.0 | 0.3 | -0.1 | -11.1 | -72.9 | 16.1 | -2,742.4 |
| rebound only | 2021 | 440 | 53.2 | 0.6 | 0.1 | -6.5 | -89.1 | 17.3 | -2,840.6 |
| rebound only | 2022 | 486 | 49.4 | -0.2 | 0.2 | -23.3 | -100.0 | 14.2 | -11,303.1 |
| rebound only | 2023 | 444 | 51.8 | 0.8 | 0.2 | -7.1 | -89.3 | 18.0 | -3,154.9 |
| rebound only | 2024 | 503 | 57.1 | 0.8 | 0.2 | -11.2 | -69.6 | 17.1 | -5,614.7 |
| rebound only | 2025 | 452 | 56.0 | 0.8 | 0.5 | -4.9 | -74.2 | 16.4 | -2,209.8 |
| rebound only | 2026 | 258 | 46.9 | -0.2 | -0.5 | -27.1 | -100.0 | 13.6 | -6,980.5 |
| regime | 2020 | 600 | 53.3 | 1.0 | 0.8 | -20.5 | -80.9 | 12.0 | -12,298.4 |
| regime | 2021 | 756 | 50.5 | 0.2 | 0.1 | -26.8 | -96.8 | 13.0 | -20,224.0 |
| regime | 2022 | 730 | 51.8 | 0.5 | 0.5 | -17.5 | -92.2 | 16.0 | -12,793.6 |
| regime | 2023 | 749 | 50.5 | 0.1 | -0.0 | -20.1 | -98.8 | 13.1 | -15,033.6 |
| regime | 2024 | 755 | 55.8 | 0.8 | 0.6 | -14.7 | -82.0 | 16.0 | -11,099.3 |
| regime | 2025 | 723 | 51.7 | 0.4 | 0.2 | -21.5 | -94.2 | 13.8 | -15,543.9 |
| regime | 2026 | 324 | 51.5 | 0.7 | 0.6 | -17.2 | -96.3 | 15.7 | -5,568.0 |

## Стратегии: паника против спокойного рынка

| rule | panic | trades | hit % | stock avg % | vs SPY % | option avg % | option median % | option x2 % | option P&L per $100 |
|---|---|---|---|---|---|---|---|---|---|
| now | False | 3529 | 50.8 | 0.3 | 0.3 | -24.9 | -97.0 | 13.3 | -87,908.3 |
| now | True | 1177 | 49.2 | -0.5 | -0.4 | -25.1 | -100.0 | 12.7 | -29,583.7 |
| rebound only | False | 2094 | 51.6 | 0.3 | 0.1 | -18.6 | -92.1 | 15.0 | -39,051.0 |
| rebound only | True | 737 | 57.5 | 0.9 | 0.2 | 5.7 | -65.3 | 19.8 | 4,204.9 |
| regime | False | 3528 | 50.8 | 0.3 | 0.3 | -25.1 | -97.2 | 13.2 | -88,405.4 |
| regime | True | 1109 | 56.7 | 1.1 | 0.7 | -3.7 | -73.6 | 17.3 | -4,155.4 |
