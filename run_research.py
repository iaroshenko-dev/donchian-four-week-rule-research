from __future__ import annotations
import io, zipfile, math, random
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
WHL=ROOT/'data'/'trendfollowing-1.3.1-py3-none-any.whl'
OUT=ROOT/'generated'
OUT.mkdir(exist_ok=True)
AF=261
VOL_COM=60.0
TARGET_VOL_PER_ASSET=0.40
COST_MULTS=[0,1,2,3]


def read_resource(name):
    with zipfile.ZipFile(WHL) as z:
        return pd.read_csv(io.BytesIO(z.read(name)))

def load_wide(name):
    df=read_resource(name)
    df=df.rename(columns={df.columns[0]:'date'})
    df['date']=pd.to_datetime(df['date'])
    return df.set_index('date').sort_index()

prices=load_wide('trendfollowing/resources/futures/tf_system_data_prices.csv')
rets=load_wide('trendfollowing/resources/futures/tf_system_data_usd_returns.csv')
costs=load_wide('trendfollowing/resources/futures/tf_system_data_volume_costs.csv')
desc=read_resource('trendfollowing/resources/futures/tf_system_data_descriptive_df.csv')

# exact column alignment
cols=[c for c in prices.columns if c in rets.columns and c in costs.columns]
prices=prices[cols]
rets=rets[cols]
costs=costs[cols]

# start-end availability interval per instrument (avoid holiday-driven portfolio churn)
avail=pd.DataFrame(False,index=prices.index,columns=cols)
for c in cols:
    vv=prices[c].dropna()
    if len(vv):
        avail.loc[vv.index.min():vv.index.max(),c]=True

# ex-ante volatility, no use of today's return
vol=np.sqrt(AF * rets.pow(2).ewm(com=VOL_COM,adjust=False,min_periods=60).mean()).shift(1)


def stateful_signal(events: pd.DataFrame):
    # events are +1/-1/nan. Carry state. Before first event = nan.
    return events.ffill()

# Primary: prior 20 observed closes, exclude current
upper20=prices.rolling(20,min_periods=20).max().shift(1)
lower20=prices.rolling(20,min_periods=20).min().shift(1)
events20=pd.DataFrame(np.nan,index=prices.index,columns=cols)
events20=events20.mask(prices.gt(upper20),1.0)
events20=events20.mask(prices.lt(lower20),-1.0)
sig20=stateful_signal(events20).where(avail)

# Literal completed calendar-week close arm
weekly_hi=prices.resample('W-FRI').max()
weekly_lo=prices.resample('W-FRI').min()
roll4hi=weekly_hi.rolling(4,min_periods=4).max()
roll4lo=weekly_lo.rolling(4,min_periods=4).min()
# for date t, reference prior completed W-FRI week
week_end=pd.Series(prices.index.to_period('W-FRI').end_time.normalize(),index=prices.index)
ref_end=week_end-pd.Timedelta(days=7)
upper4w=pd.DataFrame(index=prices.index,columns=cols,dtype=float)
lower4w=pd.DataFrame(index=prices.index,columns=cols,dtype=float)
for c in cols:
    upper4w[c]=ref_end.map(roll4hi[c])
    lower4w[c]=ref_end.map(roll4lo[c])
events4=pd.DataFrame(np.nan,index=prices.index,columns=cols)
events4=events4.mask(prices.gt(upper4w),1.0)
events4=events4.mask(prices.lt(lower4w),-1.0)
sig4=stateful_signal(events4).where(avail)

# Always-long, same availability and vol validity
siglong=pd.DataFrame(1.0,index=prices.index,columns=cols).where(avail)


def decision_weights(signal):
    raw=signal * (TARGET_VOL_PER_ASSET / vol.replace(0,np.nan))
    valid=raw.notna() & avail
    n=valid.sum(axis=1).replace(0,np.nan)
    w=raw.div(n,axis=0)
    # Decision made at close t; apply t+1.
    return w.shift(1)


def backtest(signal, cost_mult=1):
    w=decision_weights(signal)
    # no pnl on unavailable return cells
    gross_inst=w * rets
    prev=w.shift(1)
    turn=(w-prev).abs()
    # first observation of a newly active weight represents opening trade: previous 0
    first_mask=w.notna() & prev.isna()
    turn=turn.mask(first_mask,w.abs())
    turn=turn.fillna(0.0)
    inst_cost=turn * costs * cost_mult
    net_inst=gross_inst.fillna(0.0)-inst_cost.fillna(0.0)
    gross=gross_inst.sum(axis=1,min_count=1).fillna(0.0)
    net=net_inst.sum(axis=1,min_count=1).fillna(0.0)
    turnover=turn.sum(axis=1)
    cost=inst_cost.sum(axis=1)
    lev=w.abs().sum(axis=1)
    active=w.notna().sum(axis=1)
    return dict(w=w,gross_inst=gross_inst,net_inst=net_inst,gross=gross,net=net,
                turnover=turnover,cost=cost,lev=lev,active=active)


def daily_metrics(r,turnover=None,cost=None,lev=None,active=None):
    r=r.dropna()
    if len(r)<2:return {}
    ann=r.mean()*AF
    volann=r.std(ddof=1)*math.sqrt(AF)
    wealth=(1+r).cumprod()
    dd=wealth/wealth.cummax()-1
    years=(r.index[-1]-r.index[0]).days/365.25
    cagr=wealth.iloc[-1]**(1/years)-1 if years>0 and wealth.iloc[-1]>0 else np.nan
    out=dict(days=len(r),ann_arith=ann,ann_vol=volann,sharpe=ann/volann if volann>0 else np.nan,
             cagr=cagr,max_drawdown=dd.min(),skew=r.skew(),total_growth=wealth.iloc[-1]-1)
    if turnover is not None: out['ann_turnover']=turnover.reindex(r.index).mean()*AF
    if cost is not None: out['ann_cost_drag']=cost.reindex(r.index).mean()*AF
    if lev is not None: out['avg_gross_leverage']=lev.reindex(r.index).mean()
    if active is not None: out['avg_active']=active.reindex(r.index).mean()
    return out

PERIODS={
 'MOP_1985_2009':('1985-01-01','2009-12-31'),
 'POST_2009':('2010-01-01',None),
 'POST_2020':('2020-01-01',None),
}

results={}
summary=[]
for name,signal in [('DONCHIAN_20D_CLOSE_CONTINUOUS',sig20),('DONCHIAN_4_COMPLETED_WEEKS_CLOSE',sig4),('ALWAYS_LONG_SCALED',siglong)]:
    for cm in COST_MULTS:
        bt=backtest(signal,cm)
        results[(name,cm)]=bt
        for per,(start,end) in PERIODS.items():
            sl=slice(start,end)
            rr=bt['gross'].loc[sl] if cm==0 else bt['net'].loc[sl]
            mm=daily_metrics(rr,bt['turnover'].loc[sl],bt['cost'].loc[sl],bt['lev'].loc[sl],bt['active'].loc[sl])
            summary.append(dict(strategy=name,cost_mult=cm,period=per,**mm))
summary_df=pd.DataFrame(summary)
summary_df.to_csv(OUT/'summary.csv',index=False)

# calendar years and monthly returns primary/control 1x
calrows=[]
monthly_rows=[]
for name in ['DONCHIAN_20D_CLOSE_CONTINUOUS','DONCHIAN_4_COMPLETED_WEEKS_CLOSE','ALWAYS_LONG_SCALED']:
    bt=results[(name,1)]
    r=bt['net']
    yr=(1+r).groupby(r.index.year).prod()-1
    for y,v in yr.items():calrows.append(dict(strategy=name,year=y,return_net1x=v))
    mo=(1+r).resample('ME').prod()-1
    for d,v in mo.items():monthly_rows.append(dict(strategy=name,date=d,return_net1x=v))
pd.DataFrame(calrows).to_csv(OUT/'calendar_year_returns.csv',index=False)
pd.DataFrame(monthly_rows).to_csv(OUT/'monthly_returns.csv',index=False)

# block bootstrap on monthly returns: circular 12-month blocks, annualized arithmetic mean
def block_boot_monthly(m, nboot=10000, block=12, seed=20261014):
    x=np.asarray(m.dropna(),float)
    n=len(x)
    if n<24:return (np.nan,np.nan,np.nan)
    rng=np.random.default_rng(seed)
    means=np.empty(nboot)
    for b in range(nboot):
        vals=[]
        while len(vals)<n:
            s=int(rng.integers(0,n))
            vals.extend(x[(s+np.arange(block))%n])
        arr=np.asarray(vals[:n])
        means[b]=12*arr.mean()
    return np.quantile(means,.025),np.quantile(means,.975),np.mean(means<=0)

boots=[]
for name in ['DONCHIAN_20D_CLOSE_CONTINUOUS','DONCHIAN_4_COMPLETED_WEEKS_CLOSE','ALWAYS_LONG_SCALED']:
    r=results[(name,1)]['net']
    m=(1+r).resample('ME').prod()-1
    for per,(start,end) in {'POST_2009':('2010-01-01',None),'POST_2020':('2020-01-01',None)}.items():
        z=m.loc[slice(start,end)]
        lo,hi,p0=block_boot_monthly(z)
        boots.append(dict(strategy=name,period=per,months=len(z.dropna()),ann_arith_point=12*z.mean(),boot95_lo=lo,boot95_hi=hi,p_mean_le0=p0))
pd.DataFrame(boots).to_csv(OUT/'block_bootstrap.csv',index=False)

# asset-class contributions: post2009 primary net1x
map_group=dict(zip(desc['ticker'],desc['group_data']))
inst=results[('DONCHIAN_20D_CLOSE_CONTINUOUS',1)]['net_inst'].loc['2010-01-01':]
group_rows=[]
for g in sorted(set(map_group.values())):
    cc=[c for c in cols if map_group.get(c)==g]
    if not cc:continue
    rr=inst[cc].sum(axis=1)
    group_rows.append(dict(group=g,ann_arith_contribution=AF*rr.mean(),total_arith=rr.sum(),n_instruments=len(cc)))
pd.DataFrame(group_rows).to_csv(OUT/'asset_class_attribution_post2009.csv',index=False)

# signal diagnostics
sigrows=[]
for name,s in [('DONCHIAN20',sig20),('DONCHIAN4W',sig4)]:
    changes=(s!=s.shift(1)) & s.notna() & s.shift(1).notna()
    sigrows.append(dict(signal=name,mean_active=s.notna().sum(axis=1).mean(),total_reversals=int(changes.sum().sum()),
                        avg_reversals_per_instrument=float(changes.sum().mean())))
pd.DataFrame(sigrows).to_csv(OUT/'signal_diagnostics.csv',index=False)

# OHLC diagnostic on ES, GC, TY; no portfolio costs, per-market sign performance after signal
with zipfile.ZipFile(WHL) as z:
    ohlc_specs={
      'ES':'trendfollowing/resources/futures/tf_system_data_ohlc_es1.csv',
      'GC':'trendfollowing/resources/futures/tf_system_data_ohlc_gc1.csv',
      'TY':'trendfollowing/resources/futures/tf_system_data_ohlc_ty1.csv'}
    ohrows=[]
    for tick,res in ohlc_specs.items():
        df=pd.read_csv(io.BytesIO(z.read(res)))
        df['date']=pd.to_datetime(df['date']); df=df.set_index('date').sort_index()
        wh=df['PX_HIGH'].resample('W-FRI').max(); wl=df['PX_LOW'].resample('W-FRI').min()
        r4h=wh.rolling(4,min_periods=4).max(); r4l=wl.rolling(4,min_periods=4).min()
        we=pd.Series(df.index.to_period('W-FRI').end_time.normalize(),index=df.index); ref=we-pd.Timedelta(days=7)
        uh=ref.map(r4h); ll=ref.map(r4l)
        ev=pd.Series(np.nan,index=df.index)
        up=df['PX_HIGH']>uh; dn=df['PX_LOW']<ll
        ev[up & ~dn]=1; ev[dn & ~up]=-1
        sig=ev.ffill().shift(1) # apply next day
        ret=df['PX_LAST'].pct_change()
        strat=sig*ret
        for per,(start,end) in PERIODS.items():
            zret=strat.loc[slice(start,end)].dropna()
            if len(zret)<2:continue
            m=daily_metrics(zret)
            ohrows.append(dict(ticker=tick,period=per,ambiguous_days=int((up&dn).loc[slice(start,end)].sum()),**m))
pd.DataFrame(ohrows).to_csv(OUT/'ohlc_3market_diagnostic.csv',index=False)

# concentration gate
cal=pd.DataFrame(calrows)
conc=[]
for name in ['DONCHIAN_20D_CLOSE_CONTINUOUS','DONCHIAN_4_COMPLETED_WEEKS_CLOSE']:
    z=cal[(cal.strategy==name)&(cal.year>=2010)]
    total=z.return_net1x.sum(); maxyr=z.return_net1x.max(); maxyear=int(z.loc[z.return_net1x.idxmax(),'year']) if len(z) else None
    share=maxyr/total if total>0 else np.nan
    conc.append(dict(strategy=name,post2009_sum_calendar_returns=total,best_year=maxyear,best_year_return=maxyr,best_year_share_of_positive_sum=share))
pd.DataFrame(conc).to_csv(OUT/'year_concentration.csv',index=False)

# Bring prior TSMOM benchmark rows
prior=ROOT/'quant_research_2_phase2'/'strategy_summary.csv'
if prior.exists():
    q=pd.read_csv(prior)
    q=q[(q.strategy=='TSMOM_scaled') & (q.cost_case=='net_1x') & (q.period.isin(['MOP_1985_2009','POST_2009','POST_2020']))]
    q.to_csv(OUT/'prior_QR2_TSMOM_benchmark.csv',index=False)

# final textual verdict
S=summary_df
B=pd.read_csv(OUT/'block_bootstrap.csv')
C=pd.read_csv(OUT/'year_concentration.csv')
def row(strategy,period,cost=1):
    return S[(S.strategy==strategy)&(S.period==period)&(S.cost_mult==cost)].iloc[0]
pr=row('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2009',1)
pr2=row('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2009',2)
rec=row('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2020',1)
al=row('ALWAYS_LONG_SCALED','POST_2009',1)
boot=B[(B.strategy=='DONCHIAN_20D_CLOSE_CONTINUOUS')&(B.period=='POST_2009')].iloc[0]
con=C[C.strategy=='DONCHIAN_20D_CLOSE_CONTINUOUS'].iloc[0]
# meaningful diversification proxy: Sharpe > always long OR correlation low + positive; strict gate uses outperform risk-adjusted
passes=[pr.ann_arith>0,boot.boot95_lo>0,pr.sharpe>0.4,pr2.ann_arith>0,
        (pd.isna(con.best_year_share_of_positive_sum) or con.best_year_share_of_positive_sum<=0.5),
        pr.sharpe>al.sharpe,rec.ann_arith>=0]
verdict='SERIOUS_CANDIDATE' if all(passes) else 'FAIL_PRIMARY_GATE'

lines=[
'Quant Research #6 — Donchian Four-Week Rule',
'============================================',
f'VERDICT: {verdict}','',
'PRIMARY broad 84-market close-confirmed 20D channel:',
f"1985-2009 net1x: ann={row('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009',1).ann_arith:.4%}, vol={row('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009',1).ann_vol:.4%}, Sharpe={row('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009',1).sharpe:.3f}, CAGR={row('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009',1).cagr:.4%}, MaxDD={row('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009',1).max_drawdown:.2%}",
f"2010-2026 net1x: ann={pr.ann_arith:.4%}, vol={pr.ann_vol:.4%}, Sharpe={pr.sharpe:.3f}, CAGR={pr.cagr:.4%}, MaxDD={pr.max_drawdown:.2%}",
f"2020-2026 net1x: ann={rec.ann_arith:.4%}, vol={rec.ann_vol:.4%}, Sharpe={rec.sharpe:.3f}, CAGR={rec.cagr:.4%}, MaxDD={rec.max_drawdown:.2%}",
f"2010+ bootstrap 95% annual arithmetic mean: [{boot.boot95_lo:.4%}, {boot.boot95_hi:.4%}], P<=0={boot.p_mean_le0:.4f}",
f"2010+ 2x-cost ann={pr2.ann_arith:.4%}, Sharpe={pr2.sharpe:.3f}",
f"2010+ AlwaysLong same-risk: ann={al.ann_arith:.4%}, vol={al.ann_vol:.4%}, Sharpe={al.sharpe:.3f}, CAGR={al.cagr:.4%}, MaxDD={al.max_drawdown:.2%}",
f"Best-year concentration share: {con.best_year_share_of_positive_sum if pd.notna(con.best_year_share_of_positive_sum) else float('nan'):.3f} (best year {int(con.best_year) if pd.notna(con.best_year) else 'NA'})",'',
'LITERAL 4-completed-calendar-week close robustness:',
f"2010+ net1x ann={row('DONCHIAN_4_COMPLETED_WEEKS_CLOSE','POST_2009',1).ann_arith:.4%}, vol={row('DONCHIAN_4_COMPLETED_WEEKS_CLOSE','POST_2009',1).ann_vol:.4%}, Sharpe={row('DONCHIAN_4_COMPLETED_WEEKS_CLOSE','POST_2009',1).sharpe:.3f}",
f"2020+ net1x ann={row('DONCHIAN_4_COMPLETED_WEEKS_CLOSE','POST_2020',1).ann_arith:.4%}, Sharpe={row('DONCHIAN_4_COMPLETED_WEEKS_CLOSE','POST_2020',1).sharpe:.3f}",'',
'Gate booleans: '+str(passes),
'Note: broad test uses daily close-confirmed channels because 84-market resource does not contain daily highs/lows. OHLC diagnostic for ES/GC/TY is reported separately.'
]
(OUT/'VERDICT.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))

# zip outputs + protocol + code
zip_path=ROOT/'generated'/'Quant_Research_6_Donchian_Reproduction.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zz:
    for p in OUT.rglob('*'):
        if p.is_file(): zz.write(p,p.relative_to(OUT))
    for p in [ROOT/'docs'/'Quant_Research_6_Donchian_Protocol_v0_1.md',ROOT/'quant_research_6_donchian.py']:
        zz.write(p,p.name)
print('ZIP',zip_path)
