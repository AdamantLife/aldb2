## Framework
import unittest
## Test Target Module
from aldb2 import RecordReader

## Builtin
import csv
import pathlib

root = pathlib.Path(__file__).resolve().parent
TESTDIR1 = (root / "testdir_1").resolve()
if not TESTDIR1.exists():
    import warnings
    warnings.warn("Could not find TESTDIR1")

del root

class MasterStatsCase(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def test_compile_missing_seasonid(self):
        """ Make sure that masterstats compiles shows that have an identifying ID even if they do not have seasonid """
        outputstats = (TESTDIR1 / "temp_master_stats.csv").resolve()
        try:
            RecordReader.master.compile_directory(TESTDIR1,statsfile= outputstats, episodesfile= False)
            self.assertTrue(outputstats.exists())
            with open(outputstats,'r') as f:
                result = list(csv.DictReader(f))

            #self.assertEqual()

        finally:
            if outputstats.exists():
                outputstats.unlink()


class MasterEpisodesCase(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def test_compile_episodesfile_false(self):
        """ Tests that when False is supplied as the episodesfile, the compile function will not export the master_episodes file.
        
            Note that, in theory, the function could choose a complete arbitrary location to save the file and we wouldn't know
            where to check. The best we can do is hope and check in DEFAULTEPISODEFILE
        """
        outputlocation = RecordReader.master.DEFAULTEPISODEFILE
        try:
            RecordReader.master.compile_directory(TESTDIR1,statsfile= False, episodesfile= False)
            self.assertFalse(outputlocation.exists())
        finally:
            if outputlocation.exists():
                outputlocation.unlink()
        
if __name__ == "__main__":
    unittest.main()