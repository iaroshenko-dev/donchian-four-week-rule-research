"""Check rerun results against archived, frozen 2026-10-14 results."""
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
base=root/'results'
gen=root/'generated'
files=['summary.csv','block_bootstrap.csv','calendar_year_returns.csv','monthly_returns.csv',
       'ohlc_3market_diagnostic.csv','asset_class_attribution_post2009.csv',
       'signal_diagnostics.csv','year_concentration.csv']
for name in files:
    p=base/name; q=gen/name
    if not q.exists(): raise SystemExit(f'Missing rerun file {q}; first run python run_research.py')
    a=pd.read_csv(p); b=pd.read_csv(q)
    if a.shape!=b.shape or list(a.columns)!=list(b.columns):
        raise SystemExit(f'FAIL {name}: shape or columns mismatch: {a.shape}, {b.shape}')
    for col in a.columns:
        if pd.api.types.is_numeric_dtype(a[col]):
            if not np.allclose(a[col].to_numpy(dtype=float),b[col].to_numpy(dtype=float),
                               rtol=1e-8,atol=1e-9,equal_nan=True):
                diff=np.nanmax(np.abs(a[col].to_numpy(dtype=float)-b[col].to_numpy(dtype=float)))
                raise SystemExit(f'FAIL {name} / {col}: max abs difference {diff}')
        elif not a[col].fillna('').astype(str).equals(b[col].fillna('').astype(str)):
            raise SystemExit(f'FAIL {name} / {col}: categorical or date differences')
    print('PASS:',name,len(a),'rows')
print('Verified: all eight principal archived outputs match rerun.')
