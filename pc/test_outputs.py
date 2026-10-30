from pathlib import Path
import tempfile
import unicodedata
import unittest
import zipfile
from transcribe import save_outputs,stamp


class OutputTests(unittest.TestCase):
    def test_portable_audio_and_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);audio=root/'日本語.wav';audio.write_bytes(b'audio sample')
            segments=[{'start':0,'end':1.25,'text':'こんにちは。','words':[{'start':0,'end':1.25,'text':'こんにちは。'}]}]
            result=save_outputs(audio,root/'out',segments,'turbo','ja')
            with zipfile.ZipFile(root/'out/practice.echo.zip') as z:
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

    def test_timestamp_rollover(self):
        self.assertEqual(stamp(59.9996),'00:01:00,000')


if __name__=='__main__':
    unittest.main()
