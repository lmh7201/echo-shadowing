# PyInstaller spec for the single-file Windows exe; run it through scripts/build_win_exe.py.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files,collect_dynamic_libs,copy_metadata

PC=str(Path(SPECPATH).parent/'pc')

a=Analysis([PC+'/desktop.py'],pathex=[PC],hiddenimports=['transcribe','hf_xet'],
           datas=collect_data_files('faster_whisper')+copy_metadata('hf_xet'),binaries=collect_dynamic_libs('ctranslate2'))
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='echo-pc',console=False,upx=False)
