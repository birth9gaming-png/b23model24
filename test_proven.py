"""Tests for the Vegas-anchored proven spots, the 'games like this' records and the play verdicts."""
import sys, unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))

import proven, situations


def row(home_spread, away_rank=None, home_rank=None, rival=False, neutral=False, **kw):
    r = dict(id='g', current_home=home_spread, neutral=neutral, kickoff=pd.Timestamp('2026-10-17T19:30Z'),
             rule_flags=dict(away_rank=away_rank, home_rank=home_rank, rival=rival, **kw), move_home=0.0)
    s = proven.anchor(pd.DataFrame([dict(r, stats_home=home_spread)]), {'g': r['rule_flags']}, 'CFB').iloc[0].to_dict()
    return s


class TestProven(unittest.TestCase):
    def test_star_is_home_only(self):
        home_fav = row(-6.5, away_rank=12, home_rank=5)           # ranked home favorite vs ranked team
        self.assertEqual(len(home_fav['proven']['home']), 1)
        self.assertAlmostEqual(home_fav['model_home'], -8.5)       # model moves 2 pts toward the home favorite
        road_fav = row(9.5, away_rank=8, home_rank=7)             # Notre Dame -9.5 at BYU
        self.assertEqual(road_fav['proven'], {'away': [], 'home': []})
        self.assertAlmostEqual(road_fav['model_home'], 9.5)        # sits on the Vegas line

    def test_rivalry_road_favorite(self):
        r = row(10.5, away_rank=4, home_rank=None, rival=True)    # ranked road favorite at unranked rival
        self.assertEqual([p['key'] for p in r['proven']['away']], ['rival_road_fav'])
        a = proven.assess('CFB', r, 'home')                         # the home dog side is a bad play
        self.assertEqual(a['verdict'], 'Bad play')

    def test_verdicts(self):
        nd = row(9.5, away_rank=8, home_rank=7)
        self.assertEqual(proven.assess('CFB', nd, 'away')['verdict'], 'Coin flip')
        self.assertEqual(proven.assess('CFB', row(-6.5, away_rank=12, home_rank=5), 'home')['verdict'], 'Good play')
        self.assertEqual(proven.assess('CFB', row(-6.5, away_rank=12, home_rank=5), 'away')['verdict'], 'Bad play')
        moved = dict(nd, move_home=-3.5)                            # market moved 3.5 away from the road favorite
        self.assertEqual(proven.assess('CFB', moved, 'away')['verdict'], 'Bad play')
        sharp = dict(nd, sharp_home=8.0)                            # sharp books only have ND -8
        a = proven.assess('CFB', sharp, 'away')
        self.assertEqual(a['verdict'], 'Bad play')
        self.assertTrue(any('sharp' in x for x in a['against']))

    def test_flags_need_both_halves(self):
        self.assertEqual(situations.verdict_of(40, 60, 40, 60), 'bad')
        self.assertIsNone(situations.verdict_of(40, 60, 60, 40))   # flipped between halves: not a flag
        self.assertIsNone(situations.verdict_of(10, 20, 10, 20))   # too few games
        self.assertEqual(situations.verdict_of(60, 40, 58, 42), 'good')
        recs = situations.lookup('CFB', dict(line=-9.5, home=0.0, road=1.0, own_rank=1.0, opp_rank=1.0))
        self.assertTrue(any(x['text'] == 'road favorites in a ranked-vs-ranked game' for x in recs))


if __name__ == '__main__':
    unittest.main()
