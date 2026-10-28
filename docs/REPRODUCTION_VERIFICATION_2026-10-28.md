# Проверка воспроизводимости — 28 октября 2026

Источник: сохранённый закрытый исследовательский архив `Quant_Research_6_Donchian_Final_2026-10-14.zip` и исходный wheel `trendfollowing-1.3.1-py3-none-any.whl`.

Проведена фактическая повторная генерация результатов скриптом `run_research.py` с тем же кодом расчёта (изменены только абсолютные пути). Проверен SHA256 исходного wheel.

**PASS:**

- summary.csv (36 строк)
- block_bootstrap.csv (6 строк)
- calendar_year_returns.csv (204 строки)
- monthly_returns.csv (2415 строк)
- ohlc_3market_diagnostic.csv (9 строк)
- asset_class_attribution_post2009.csv (7 строк)
- signal_diagnostics.csv (2 строки)
- year_concentration.csv (2 строки)

Сравнение: поля и формы таблиц совпадают, числа равны с относительной точностью до 1e-8 и абсолютной до 1e-9.

**Ограничения проверки:** это повторный прогон *той же реализации на тех же данных*, а не независимая вторичная имплементация логики, не тест рыночного исполнения и не доказательство корректности всех модельных предположений. Также при отсутствии отдельного QR2 проекта не регенерируется архивный `prior_QR2_TSMOM_benchmark.csv`, но он сохраняется и явно помечен как внешний бенчмарк.

Команды:

```bash
python scripts/fetch_data.py
python run_research.py
python scripts/verify_reproduction.py
python -m unittest discover -s tests -v
```
