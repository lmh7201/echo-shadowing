import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import updater
from updater import Release,aside,download,latest,parse_version,swap_mac,swap_windows

SHA_ABC='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'


class Response(io.BytesIO):
    def __init__(self,data,headers):super().__init__(data);self.headers=headers


def api(tag,name=None,host='github.com'):
    asset={'name':name or updater.ASSET,'size':3,'digest':'sha256:'+SHA_ABC,'browser_download_url':f'https://{host}/lmh7201/echo-shadowing/releases/download/{tag}/{updater.ASSET}'}
    return json.dumps({'tag_name':tag,'assets':[asset]}).encode()


class UpdaterTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(parse_version('v1.2.0'),(1,2,0));self.assertEqual(parse_version('1.10'),(1,10,0))
        self.assertIsNone(parse_version('dev'));self.assertIsNone(parse_version('v1.2.0-beta'))

    def test_latest_only_when_newer(self):
        with patch('updater.read_small',return_value=api('v1.3.0')):
            release=latest('v1.2.0')
            self.assertEqual(release.tag,'v1.3.0');self.assertEqual(release.size,3);self.assertEqual(release.sha256,SHA_ABC)
            self.assertIsNone(latest('v1.3.0'));self.assertIsNone(latest('v2.0.0'));self.assertIsNone(latest('dev'))
        with patch('updater.read_small',return_value=api('v1.3.0',name='other.zip')):self.assertIsNone(latest('v1.0.0'))
        with patch('updater.read_small',return_value=api('v1.3.0',host='example.com')):
            with self.assertRaises(ValueError):latest('v1.0.0')

    def test_download_checks_digest(self):
        release=Release('v1.3.0','https://github.com/x',3,SHA_ABC)
        with tempfile.TemporaryDirectory() as temp:
            with patch('updater.request',return_value=Response(b'abc',{'Content-Length':'3'})):
                self.assertEqual(download(release,temp).read_bytes(),b'abc')
            with patch('updater.request',return_value=Response(b'abd',{'Content-Length':'3'})):
                with self.assertRaises(ValueError):download(release,Path(temp)/'bad')
            with patch('updater.request',return_value=Response(b'ab',{'Content-Length':'3'})):
                with self.assertRaises(ValueError):download(release,Path(temp)/'short')
            self.assertEqual([p.name for p in Path(temp).rglob('*') if p.is_file()],[updater.ASSET])

    def test_launch_env_drops_pyinstaller_handoff(self):
        with patch.dict('os.environ',{'_PYI_APPLICATION_HOME_DIR':'x','_PYI_PARENT_PROCESS_LEVEL':'1','_MEIPASS2':'y','PATH':'keep'}):
            env=updater.launch_env()
            self.assertEqual(env['PATH'],'keep');self.assertFalse([k for k in env if k.startswith('_PYI_') or k=='_MEIPASS2'])

    def test_swap_windows(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=Path(temp)/'echo-pc.exe';exe.write_bytes(b'old');new=Path(temp)/'dl'/'echo-pc.exe';new.parent.mkdir();new.write_bytes(b'new')
            old=swap_windows(exe,new)
            self.assertEqual(exe.read_bytes(),b'new');self.assertEqual(old.read_bytes(),b'old');self.assertEqual(old.name,'echo-pc.old.exe')
            self.assertEqual(sorted(p.name for p in Path(temp).iterdir()),['dl','echo-pc.exe','echo-pc.old.exe'])

    def test_swap_mac(self):
        with tempfile.TemporaryDirectory() as temp:
            app=Path(temp)/'Echo PC.app';(app/'Contents').mkdir(parents=True);(app/'Contents'/'v').write_text('old')
            new=Path(temp)/'extract'/'Echo PC.app';(new/'Contents').mkdir(parents=True);(new/'Contents'/'v').write_text('new')
            old=swap_mac(app,new)
            self.assertEqual((app/'Contents'/'v').read_text(),'new');self.assertEqual((old/'Contents'/'v').read_text(),'old')
            self.assertEqual(old.name,'.Echo PC.app.old');self.assertFalse(new.exists())
            self.assertEqual(aside(app)[1].name,'.Echo PC.app.new')


if __name__=='__main__':unittest.main()
