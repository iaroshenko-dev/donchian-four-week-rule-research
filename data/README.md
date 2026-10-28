# Dataset: external dependency

The original 84-market dataset is distributed within `trendfollowing==1.3.1`, created by Artur Sepp and Vladimir Lucic, not by the author of this repo. It is NOT bundled here. Version `1.3.1` has GPL-3.0-or-later licensing; consult its licensing terms before redistributing the wheel/data.

Download the precise version with:

```bash
python -m pip download --no-deps --only-binary=:all: trendfollowing==1.3.1 -d data
```

The runner expects `data/trendfollowing-1.3.1-py3-none-any.whl` (do not replace with a newer release).

SHA256 of the wheel used for the frozen 2026-10-14 research:

`76beb7a35b22cb2784df98bb20a6d9ca5803c4df761398b877db765bd6562c9a`

Sources: https://pypi.org/project/trendfollowing/1.3.1/ and https://github.com/ArturSepp/TrendFollowingSystems .

Original packaged data: daily benchmark/settlement prices, excess USD returns, modeled volume-based costs, instrument descriptions and OHLC for ES, GC and TY. Instruments have different inception dates; this is not a constant 84-contract panel in every year.
