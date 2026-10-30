"""Package only the distributable PC source; never include audio, models or settings."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=('desktop.py','transcribe.py','podcasts.py','podcast_dialog.py','start.cmd','start.command','requirements.txt','README.txt')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'web/echo-pc.zip'))
    args=parser.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            info=zipfile.ZipInfo.from_file(ROOT/'pc'/name,'echo-pc/'+name)
            info.create_system=3;info.external_attr=(0o100755 if name.endswith('.command') else 0o100644)<<16
            z.writestr(info,(ROOT/'pc'/name).read_bytes(),zipfile.ZIP_DEFLATED)
    print(output)

if __name__=='__main__':main()
