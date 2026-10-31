"""Local Whisper transcription -> portable Echo bundle, word JSON and SRT."""
import argparse
from datetime import datetime
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import unicodedata
import zipfile


def stamp(seconds):
    ms=max(0,round(seconds*1000))
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def bundle_name(title, when=None):
    """Short and distinct per run so files moved to the phone never collide: <title>_<MMDD_HHMM>.echo.zip."""
    safe=re.sub(r'[\x00-\x1f<>:"/\\|?*]+','_',title).strip(' ._')[:10].rstrip(' ._') or 'echo'
    return f'{safe}_{(when or datetime.now()):%m%d_%H%M}.echo.zip'


def save_outputs(audio, output, segments, model, language, preview=False):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    suffix=audio.suffix.lower()
    if not suffix[1:].isalnum() or len(suffix)>9:
        suffix='.bin'
    session={'format':'echo-session','version':1,'title':unicodedata.normalize('NFC',audio.stem),'audioFile':'audio'+suffix,
             'audioMime':mimetypes.guess_type(str(audio))[0] or 'application/octet-stream',
             'model':model,'language':language,'preview':preview,'segments':segments}
    serialized=json.dumps(session,ensure_ascii=False,allow_nan=False)
    (output/'transcript.echo.json').write_text(serialized,encoding='utf-8')
    srt='\n'.join(f'{i+1}\n{stamp(s["start"])} --> {stamp(s["end"])}\n{s["text"].strip()}\n' for i,s in enumerate(segments))
    (output/'transcript.srt').write_text(srt,encoding='utf-8-sig')
    if audio.stat().st_size<=180*1024*1024:
        bundle=output/bundle_name(session['title'])
        tmp=bundle.with_name(bundle.name+'.tmp')
        with zipfile.ZipFile(tmp,'w') as z:
            z.writestr('session.json',serialized,compress_type=zipfile.ZIP_DEFLATED)
            z.write(audio,session['audioFile'],compress_type=zipfile.ZIP_STORED)
        tmp.replace(bundle)
    return session


def run(args):
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio
    audio=Path(args.audio).resolve()
    if not audio.is_file():
        raise ValueError('음성 파일을 찾을 수 없습니다.')
    print(f'모델 준비: {args.model}. 첫 실행은 수 GB를 다운로드할 수 있습니다.',flush=True)
    model=WhisperModel(args.model,device=args.device,compute_type='float16' if args.device=='cuda' else 'int8',
                       cpu_threads=max(1,min(8,(os.cpu_count() or 4)-1)),download_root=args.models)
    print('음성을 읽는 중…',flush=True)
    pcm=decode_audio(str(audio),sampling_rate=16000)
    if args.seconds:
        pcm=pcm[:round(args.seconds*16000)]
    total=len(pcm)/16000
    if total<=0:
        raise ValueError('음성이 비어 있습니다.')
    iterator,info=model.transcribe(pcm,language=None if args.language=='auto' else args.language,
                task='transcribe',beam_size=5,word_timestamps=True,vad_filter=True,
                condition_on_previous_text=False)
    results=[]
    for s in iterator:
        start=max(0,float(s.start));end=min(total,float(s.end))
        if end<=start or not s.text.strip():
            continue
        words=[];last=start
        for w in s.words or []:
            ws=max(start,last,float(w.start));we=min(end,max(ws,float(w.end)))
            if ws>end:
                continue
            words.append({'start':ws,'end':we,'text':w.word});last=ws
        results.append({'start':start,'end':end,'text':s.text,'words':words})
        print(f'PROGRESS|{min(99,round(end/total*100))}|{stamp(end)} / {stamp(total)} · {s.text}',flush=True)
    if not results:
        raise ValueError('話し声が見つかりませんでした。音声と言語を確認してください。 / 말소리를 찾지 못했습니다.')
    save_outputs(audio,Path(args.output),results,args.model,info.language,bool(args.seconds))
    print(f'DONE|{Path(args.output).resolve()}',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio');p.add_argument('--output',required=True)
    p.add_argument('--model',choices=['large-v3','turbo','medium','small','tiny'],default='large-v3')
    p.add_argument('--language',default='ja');p.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    p.add_argument('--seconds',type=float,default=0);p.add_argument('--models',default=str(Path(__file__).parent/'models'))
    args=p.parse_args()
    if args.seconds<0:
        p.error('--seconds must be nonnegative')
    try:
        run(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f'ERROR|{type(e).__name__}: {e}',flush=True)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main())
