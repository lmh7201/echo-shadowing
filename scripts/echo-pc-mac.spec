# PyInstaller spec for the self-contained macOS app; run it through scripts/build_mac_app.sh.
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files,collect_dynamic_libs,copy_metadata

PC=str(Path(SPECPATH).parent/'pc')
VERSION=os.environ.get('ECHO_VERSION','0.0.0').lstrip('v')

a=Analysis([PC+'/desktop.py'],pathex=[PC],hiddenimports=['transcribe','hf_xet'],
           datas=collect_data_files('faster_whisper')+copy_metadata('hf_xet'),binaries=collect_dynamic_libs('ctranslate2'))
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='Echo PC',console=False)
coll=COLLECT(exe,a.binaries,a.datas,name='Echo PC')
app=BUNDLE(coll,name='Echo PC.app',bundle_identifier='io.github.lmh7201.echo-pc',version=VERSION,
           info_plist={'LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True})
