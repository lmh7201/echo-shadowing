import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import podcast_history
from podcast_history import PodcastHistory


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'podcast-source.json'

    def tearDown(self):self.temp.cleanup()

    def test_record_keeps_every_link_and_last(self):
        h=PodcastHistory(self.path)
        h.record(' https://a.example/rss ','A');h.record('https://b.example/rss','B');h.record('https://a.example/rss')
        self.assertEqual([e['url'] for e in h.ordered()],['https://a.example/rss','https://b.example/rss'])
        self.assertEqual(h.find('https://a.example/rss')['title'],'A')  # a reload without a title keeps the old one
        saved=json.loads(self.path.read_text('utf8'))
        self.assertEqual(saved['url'],'https://a.example/rss');self.assertEqual(len(saved['history']),2)
        self.assertEqual(PodcastHistory(self.path).last,'https://a.example/rss')

    def test_favorites_come_first_and_survive_pruning(self):
        h=PodcastHistory(self.path)
        with patch('podcast_history.now',side_effect=(f'2026-01-01T00:00:{i:02d}Z' for i in range(99))):
            h.record('https://old.example/rss','Old');self.assertTrue(h.toggle_favorite('https://old.example/rss'))
            for i in range(podcast_history.MAX_RECENT+5):h.record(f'https://n{i}.example/rss')
        self.assertEqual(h.ordered()[0]['url'],'https://old.example/rss')
        self.assertEqual(len(h.entries),podcast_history.MAX_RECENT+1)
        self.assertIsNone(h.find('https://n0.example/rss'));self.assertIsNotNone(h.find('https://n5.example/rss'))
        self.assertFalse(h.toggle_favorite('https://old.example/rss'))
        self.assertTrue(PodcastHistory(self.path).toggle_favorite('https://new.example/rss'))  # starring an unloaded link saves it
        self.assertEqual(PodcastHistory(self.path).find('https://new.example/rss')['favorite'],True)

    def test_remove_and_migration(self):
        self.path.write_text('{"url":"https://legacy.example/rss"}','utf8')
        h=PodcastHistory(self.path)
        self.assertEqual(h.last,'https://legacy.example/rss');self.assertEqual(len(h.entries),1)
        self.assertTrue(h.remove('https://legacy.example/rss'));self.assertFalse(h.remove('https://legacy.example/rss'))
        self.assertEqual(h.last,'');self.assertEqual(json.loads(self.path.read_text('utf8'))['history'],[])

    def test_bad_file_is_ignored(self):
        self.path.write_text('[not,"an object"',encoding='utf8')
        self.assertEqual(PodcastHistory(self.path).entries,[])
        self.path.write_text('{"history":[1,{"url":""},{"url":"https://ok.example/rss","favorite":"yes"}]}',encoding='utf8')
        h=PodcastHistory(self.path);self.assertEqual(len(h.entries),1);self.assertTrue(h.entries[0]['favorite'])


if __name__=='__main__':unittest.main()
