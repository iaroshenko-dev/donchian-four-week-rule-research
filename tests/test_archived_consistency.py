"""Offline, built-in unittest checks on the research output provided with the repo."""
from pathlib import Path
import unittest
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results'

class ArchivedResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=pd.read_csv(DATA/'summary.csv')
        cls.boot=pd.read_csv(DATA/'block_bootstrap.csv')

    def select(self,strategy,period,mult=1):
        q=self.summary
        z=q[(q.strategy==strategy)&(q.period==period)&(q.cost_mult==mult)]
        self.assertEqual(len(z),1)
        return z.iloc[0]

    def test_closed_modern_result(self):
        s=self.select('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2009')
        self.assertAlmostEqual(s.ann_arith,0.000923,delta=1e-5)
        self.assertAlmostEqual(s.sharpe,0.008,delta=0.002)

    def test_historical_positive(self):
        s=self.select('DONCHIAN_20D_CLOSE_CONTINUOUS','MOP_1985_2009')
        self.assertGreater(s.ann_arith,0.08)
        self.assertGreater(s.sharpe,0.8)

    def test_net_less_than_gross(self):
        a=self.select('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2009',0)
        b=self.select('DONCHIAN_20D_CLOSE_CONTINUOUS','POST_2009',1)
        self.assertGreater(a.ann_arith,b.ann_arith)

    def test_bootstrap_not_significant(self):
        b=self.boot
        z=b[(b.strategy=='DONCHIAN_20D_CLOSE_CONTINUOUS')&(b.period=='POST_2009')]
        self.assertEqual(len(z),1)
        self.assertLess(z.iloc[0].boot95_lo,0)
        self.assertGreater(z.iloc[0].boot95_hi,0)

if __name__=='__main__': unittest.main()
