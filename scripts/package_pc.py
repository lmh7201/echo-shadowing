"""Package only the distributable PC source; never include audio, models or settings."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FILES=('desktop.py','transcribe.py','podcasts.py','podcast_dialog.py','start.cmd','requirements.txt','README.txt')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'web/echo-pc.zip'))
    args=parser.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name in FILES:z.write(ROOT/'pc'/name,'echo-pc/'+name)
    print(output)

if __name__=='__main__':main()
