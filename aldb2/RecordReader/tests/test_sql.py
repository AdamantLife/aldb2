## Framework
import unittest
## Test Target
from aldb2.RecordReader import sql

## Sister Module
from aldb2 import RecordReader
from aldb2.Anime.tests.test_sql import fullsetup as animesetup
from aldb2.AnimeLife.tests.test_sql import fullsetup as animelifesetup

## Builtin
import pathlib

root = pathlib.Path(__file__).resolve().parent
MASTERSTATSFILE = (root / "test_master_stats.csv").resolve()
if not MASTERSTATSFILE.exists():
    import warnings
    warnings.warn("masterstats file is missing")

MASTEREPISODESFILE = (root / "test_master_episodes.csv").resolve()
if not MASTEREPISODESFILE.exists():
    import warnings
    warnings.warn("masterepisodes file is missing")
    
del root

def basic_setup(testcase):
    animesetup(testcase)

class MasterstatsCase(unittest.TestCase):
    def setUp(self):
        basic_setup(self)
        self.masterstats = RecordReader.master.load_masterstats(MASTERSTATSFILE)
        self.masterepisodes = RecordReader.master.load_masterepisodes(MASTEREPISODESFILE)

    def test_uploadmasterstats(self):
        """ Tests the upload of a masterstats file """
        sql.import_master(self.connection, masterstats = MASTERSTATSFILE, masterepisodes = False)

if __name__ == "__main__":
    unittest.main()