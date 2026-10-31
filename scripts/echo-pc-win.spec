# PyInstaller spec for the single-file Windows exe; run it through scripts/build_win_exe.py.
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files,collect_dynamic_libs,copy_metadata

PC=str(Path(SPECPATH).parent/'pc')
# The release tag (ECHO_VERSION=v1.3.0) travels inside the exe so the app can compare itself with GitHub Releases.
VERSION_FILE=Path(workpath)/'echo-version.txt';VERSION_FILE.parent.mkdir(parents=True,exist_ok=True)
VERSION_FILE.write_text(os.environ.get('ECHO_VERSION','v0.0.0'),encoding='utf8')

a=Analysis([PC+'/desktop.py'],pathex=[PC],hiddenimports=['transcribe','hf_xet'],
           datas=[(str(VERSION_FILE),'.'),(PC+'/icons/icon.png','icons')]+collect_data_files('faster_whisper')+copy_metadata('hf_xet'),binaries=collect_dynamic_libs('ctranslate2'))
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='echo-pc',console=False,upx=False,icon=PC+'/icons/icon.ico')
