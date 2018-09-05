## Testing Module
import unittest
## Test Module
from aldb2.Anime import anime
## Builtin
import copy
import json
import random

with open("anime.json",'r') as f:
    DATA = json.load(f)
del f

class BaseCase(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(DATA)

class AnimeSeasonDictCase(BaseCase):

    @property
    def goodseasons(self):
        """ Helper property for returning a reference to the Good Seasons dict """
        return copy.deepcopy(self.data['Test Seasons']['Good Seasons'])

    @property
    def badseasons(self):
        """ Helper property for returning a reference to the Bad Seasons dict """
        return copy.deepcopy(self.data['Test Seasons']['Bad Seasons'])

    def test_getseasonhash(self):
        """ Tests the accuracy of getseasonhash """
        seasons = self.goodseasons
        for season in seasons:
            with self.subTest(season = season):
                self.assertEqual(anime.getseasonhash(season['season']),hash(season['hash']))

    def test_sortseasons(self):
        """ Tests that sort seasons returns the list of seasons in the correct order """
        goodseasons = self.goodseasons
        seasons = [season['season'] for season in goodseasons]
        shuffledseasons = random.sample(seasons,k = len(seasons))
        ## On the 1-in-a-million chance that we don't shuffle well the first time
        if seasons == shuffledseasons:
            shuffledseasons = random.sample(seasons,k = len(seasons))
        self.assertNotEqual(seasons,shuffledseasons)
        for i,season in enumerate(anime.sortseasondicts(shuffledseasons)):
            with self.subTest(i = i, season = season):
                self.assertEqual(goodseasons[i]['season'],season)

    def test_sumseasondicts(self):
        """ Tests that sumseasons flattens lists of anime seasons and orders them """
        
        baseseasons = [season['season'] for season in self.goodseasons]
        ## Duplicate entries
        goodseasons = [baseseasons,baseseasons]
        ## We now have two of all seasons
        self.assertEqual(sum(len(seasons) for seasons in goodseasons), len(baseseasons)*2)
        goodseasons = anime.sumseasondicts(goodseasons)
        ## Check that it's the correct length
        self.assertEqual(len(goodseasons),len(baseseasons))
        ## Check that all seasons are present
        self.assertTrue(all(season in baseseasons for season in goodseasons))
        self.assertTrue(all(season in goodseasons for season in baseseasons))
        
    def test_parseanimeseason_good(self):
        """ Tests that good anime seasons are properly parsed """
        seasons = self.goodseasons
        for season in seasons:
            with self.subTest(season = season):
                self.assertTrue(season['season'],anime.parseanimeseason(season['seasonstring']))

    def test_parseanimeseason_bad(self):
        """ Tests that bad anime seasons raise exceptions """
        seasons = self.badseasons
        for season in seasons:
            with self.subTest(season = season):
                self.assertRaises(ValueError,anime.parseanimeseason,season['seasonstring'])

    def test_stepanimeseasondict(self):
        """ Various test for stepanimeseasondict """
        for case,step,result in [(dict(year=1,season=0),1,dict(year=1,season="Spring")),
                                 (dict(year=1,season=0),-1,dict(year=0,season="Fall")),
                                 (dict(year=1,season=3),1,dict(year=2,season="Winter")),
                                 (dict(year=1,season=0),4,dict(year=2,season="Winter")),
                                 (dict(year=1,season=0),-4,dict(year=0,season="Winter")),
                                 (dict(year=0,season=0),15,dict(year=3,season="Fall")),
                                 (dict(year=0,season=0),-15,dict(year=-4,season="Spring")),
                                 ]:
            with self.subTest(case = case, step = step, result = result):
                self.assertEqual(anime.stepanimeseasondict(case,step),result)

class AnimeSeasonCase(BaseCase):
    
    @property
    def goodseasons(self):
        """ Helper property for returning a reference to the Good Seasons dict and converting to AnimeSeason objects"""
        seasons = copy.deepcopy(self.data['Test Seasons']['Good Seasons'])
        for season in seasons: season['season'] = anime.AnimeSeason(**season['season'])
        return seasons

    def test_season_hash(self):
        """ Tests the accuracy of the AnimeSeason's hash attribute """
        seasons = self.goodseasons
        for season in seasons:
            with self.subTest(season = season):
                self.assertEqual(hash(season['season']),hash(season['hash']))

    def test_season_sort(self):
        """ Tests that seasons can be sorted in the correct order"""
        goodseasons = self.goodseasons
        seasons = [season['season'] for season in goodseasons]
        shuffledseasons = random.sample(seasons,k = len(seasons))
        ## On the 1-in-a-million chance that we don't shuffle well the first time
        if seasons == shuffledseasons:
            shuffledseasons = random.sample(seasons,k = len(seasons))
        self.assertNotEqual(seasons,shuffledseasons)
        for i,season in enumerate(sorted(shuffledseasons)):
            with self.subTest(season = season, i = i):
                self.assertEqual(goodseasons[i]['season'],season)

    def test_sumseasons(self):
        """ Tests that sumseasons flattens lists of anime seasons and orders them """
        
        baseseasons = [season['season'] for season in self.goodseasons]
        ## Duplicate entries
        goodseasons = [baseseasons,baseseasons]
        ## We now have two of all seasons
        self.assertEqual(sum(len(seasons) for seasons in goodseasons), len(baseseasons)*2)
        goodseasons = anime.sumseasons(goodseasons)
        ## Check that it's the correct length
        self.assertEqual(len(goodseasons),len(baseseasons))
        ## Check that all seasons are present
        self.assertTrue(all(season in baseseasons for season in goodseasons))
        self.assertTrue(all(season in goodseasons for season in baseseasons))

    def test_stepanimeseason(self):
        """ This should pass the same tests as test_stepanimeseasondict because they work off the same function """
        for case,step,result in [(anime.AnimeSeason(year=1,season=0),1,anime.AnimeSeason(year=1,season="Spring")),
                                 (anime.AnimeSeason(year=1,season=0),-1,anime.AnimeSeason(year=0,season="Fall")),
                                 (anime.AnimeSeason(year=1,season=3),1,anime.AnimeSeason(year=2,season="Winter")),
                                 (anime.AnimeSeason(year=1,season=0),4,anime.AnimeSeason(year=2,season="Winter")),
                                 (anime.AnimeSeason(year=1,season=0),-4,anime.AnimeSeason(year=0,season="Winter")),
                                 (anime.AnimeSeason(year=0,season=0),15,anime.AnimeSeason(year=3,season="Fall")),
                                 (anime.AnimeSeason(year=0,season=0),-15,anime.AnimeSeason(year=-4,season="Spring")),
                                 ]:
            with self.subTest(case = case, step = step, result = result):
                self.assertEqual(anime.stepanimeseason(case,step),result)

if __name__ == "__main__":
    unittest.main()