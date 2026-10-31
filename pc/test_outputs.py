from datetime import datetime
from pathlib import Path
import tempfile
import unicodedata
import unittest
import zipfile
from transcribe import bundle_name,save_outputs,stamp


class OutputTests(unittest.TestCase):
    def test_portable_audio_and_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);audio=root/'日本語.wav';audio.write_bytes(b'audio sample')
            segments=[{'start':0,'end':1.25,'text':'こんにちは。','words':[{'start':0,'end':1.25,'text':'こんにちは。'}]}]
            result=save_outputs(audio,root/'out',segments,'turbo','ja')
            bundles=list((root/'out').glob('*.echo.zip'))
            self.assertEqual(len(bundles),1);self.assertTrue(bundles[0].name.startswith('日本語_'))
            with zipfile.ZipFile(bundles[0]) as z:
                self.assertEqual(z.read('audio.wav'),audio.read_bytes())
                self.assertIn('こんにちは',z.read('session.json').decode('utf8'))
            self.assertEqual(result['segments'][0]['words'][0]['end'],1.25)
            self.assertIn('00:00:01,250',(root/'out/transcript.srt').read_text('utf-8-sig'))
            with self.assertRaises(FileExistsError):
                save_outputs(audio,root/'out',segments,'turbo','ja')

    def test_mac_decomposed_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);audio=root/unicodedata.normalize('NFD','한국어 がくせい.wav');audio.write_bytes(b'audio')
            self.assertEqual(save_outputs(audio,root/'out',[],'turbo','ja')['title'],'한국어 がくせい')

    def test_bundle_name_is_safe_and_dated(self):
        when=datetime(2026,11,1,15,30)
        self.assertEqual(bundle_name('第12回: Q&A / 질문?',when),'第12回_ Q&A_1101_1530.echo.zip')
        self.assertEqual(bundle_name(' ..',when),'echo_1101_1530.echo.zip')
        self.assertEqual(bundle_name('あ'*80,when),'あ'*10+'_1101_1530.echo.zip')

    def test_timestamp_rollover(self):
        self.assertEqual(stamp(59.9996),'00:01:00,000')


if __name__=='__main__':
    unittest.main()
