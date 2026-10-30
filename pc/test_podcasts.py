import io
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from podcasts import parse_feed,resolve_feed,download_episode,Episode,DownloadCancelled


RSS=b'''<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel><title>Sample</title><item><title>Episode &amp; One</title><pubDate>Tue, 27 Oct 2026 03:45:28 GMT</pubDate><itunes:duration>00:21:14</itunes:duration><enclosure url="https://example.com/file.mp3" type="audio/mpeg"/></item><item><title>Skip website</title></item></channel></rss>'''


class Response(io.BytesIO):
    def __init__(self,data,headers):super().__init__(data);self.headers=headers


class PodcastTests(unittest.TestCase):
    def test_feed(self):
        title,episodes=parse_feed(RSS)
        self.assertEqual(title,'Sample');self.assertEqual(len(episodes),1)
        self.assertEqual(episodes[0].title,'Episode & One');self.assertEqual(episodes[0].duration,'00:21:14')
        self.assertEqual(episodes[0].date,'2026-10-27')

    @patch('podcasts.read_small',return_value=b'{"results":[{"feedUrl":"https://example.com/rss"}]}')
    def test_apple_lookup(self,read):
        self.assertEqual(resolve_feed('https://podcasts.apple.com/kr/podcast/name/id1480155677?i=123'),'https://example.com/rss')
        self.assertIn('1480155677',read.call_args.args[0])

    def test_non_http_and_entities(self):
        with self.assertRaises(ValueError):resolve_feed('file:///C:/secret')
        with self.assertRaises(ValueError):parse_feed(b'<!DOCTYPE rss [<!ENTITY a "x">]><rss/>')

    def test_download_and_reuse(self):
        e=Episode('../unsafe:name','https://example.com/a.mp3',mime='audio/mpeg')
        with tempfile.TemporaryDirectory() as temp:
            with patch('podcasts.request',return_value=Response(b'abc',{'Content-Length':'3','Content-Type':'audio/mpeg'})) as req:
                path=download_episode(e,temp);self.assertEqual(path.read_bytes(),b'abc')
                self.assertEqual(path.parent,Path(temp));self.assertNotIn(':',path.name)
                self.assertEqual(download_episode(e,temp),path);self.assertEqual(req.call_count,1)

    def test_partial_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('podcasts.request',return_value=Response(b'abc',{'Content-Length':'99'})):
                with self.assertRaises(ValueError):download_episode(Episode('x','https://example.com/a.mp3'),temp)
            self.assertEqual(list(Path(temp).iterdir()),[])
            cancel=threading.Event();cancel.set()
            with self.assertRaises(DownloadCancelled):download_episode(Episode('x','https://example.com/a.mp3'),temp,cancel=cancel)
            self.assertEqual(list(Path(temp).iterdir()),[])


if __name__=='__main__':unittest.main()
