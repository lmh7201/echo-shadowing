"""Echo PC: a local desktop front end; recognition runs in a cancellable process."""
from datetime import datetime
import multiprocessing
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
import unicodedata
from tkinter import ttk,filedialog,messagebox
from podcast_dialog import PodcastDialog
from theme import Theme,wrap
import updater

ROOT=Path(__file__).resolve().parent
MAC=sys.platform=='darwin'
FROZEN=getattr(sys,'frozen',False)
RESOURCES=Path(getattr(sys,'_MEIPASS',ROOT))  # bundled files such as icons/icon.png
# Frozen builds unpack to a read-only bundle (Mac) or a temp folder (Windows exe), so data lives in the user profile.
if not FROZEN:DATA=ROOT
elif MAC:DATA=Path.home()/'Library'/'Application Support'/'Echo PC'
else:DATA=Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData'/'Local')/'Echo PC'


class App:
    def __init__(self,root):
        self.root=root;self.process=None;self.events=queue.Queue();self.output=None;self.podcast_dialog=None;self.release=None;self.updating=False
        root.title(f'Echo PC {updater.VERSION} · 고정밀 자막 생성');root.geometry('780x760');root.minsize(660,640)
        try:self.icon=tk.PhotoImage(file=str(RESOURCES/'icons'/'icon.png'));root.iconphoto(True,self.icon);self.logo=self.icon.subsample(8)
        except tk.TclError:self.logo=None
        self.theme=theme=Theme(root,DATA/'settings.json')
        body=ttk.Frame(root,padding=(28,18,28,24));body.pack(fill='both',expand=True)
        header=ttk.Frame(body);header.pack(fill='x')
        if self.logo:ttk.Label(header,image=self.logo).pack(side='left',padx=(0,10))
        ttk.Label(header,text='Echo PC',style='Brand.TLabel').pack(side='left')
        ttk.Label(header,text=updater.VERSION,style='Chip.TLabel').pack(side='left',padx=10)
        self.theme_button=ttk.Button(header,style='Ghost.TButton',command=theme.toggle);self.theme_button.pack(side='right')
        self.update_button=ttk.Button(header,text='업데이트 확인',style='Ghost.TButton',command=self.update_click)
        if updater.ENABLED:self.update_button.pack(side='right',padx=(0,4))
        ttk.Label(body,text='한 번 만들고, 어디서나 연습',style='Title.TLabel').pack(anchor='w',pady=(20,6))
        wrap(ttk.Label(body,text='PC에서 음성·단어별 시간·자막을 하나의 연습 파일로 만듭니다. 완성된 ‘음성 제목_날짜시각.echo.zip’을 모바일 웹페이지의 ‘연습 파일 열기’로 불러오세요.',style='Muted.TLabel')).pack(fill='x',pady=(0,18))
        source=self.card(body,'1','음성 파일')
        self.audio=tk.StringVar();row=ttk.Frame(source,style='Inner.TFrame');row.pack(fill='x')
        ttk.Entry(row,textvariable=self.audio).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='음성 선택',command=self.choose).pack(side='left',padx=(8,0))
        ttk.Button(source,text='↧ 팟캐스트에서 음성 받기 · Apple Podcasts / RSS',style='CardGhost.TButton',command=self.podcasts).pack(anchor='w',pady=(8,0))
        options=self.card(body,'2','인식 설정')
        grid=ttk.Frame(options,style='Inner.TFrame');grid.pack(fill='x')
        self.model=tk.StringVar(value='large-v3');self.lang=tk.StringVar(value='ja');self.scope=tk.StringVar(value='전체 음성');self.device=tk.StringVar(value='cpu')
        for i,(label,var,values) in enumerate([('모델',self.model,['large-v3','turbo','medium']),('언어',self.lang,['ja','en','ko','zh','es','fr','de','auto']),('범위',self.scope,['앞 30초 시험','전체 음성']),('실행 장치',self.device,['cpu'] if MAC else ['cpu','cuda'])]):
            ttk.Label(grid,text=label,style='Field.TLabel').grid(row=0,column=i,sticky='w',padx=(0 if i==0 else 10,0))
            theme.combo(ttk.Combobox(grid,textvariable=var,values=values,state='readonly',width=12)).grid(row=1,column=i,padx=(0 if i==0 else 10,0),pady=(4,0),sticky='ew')
            grid.columnconfigure(i,weight=1,uniform='options')
        device_note='Mac에서는 CPU로 실행됩니다. Apple Silicon의 GPU(Metal) 가속은 지원하지 않습니다.' if MAC else 'CPU는 별도 그래픽카드 없이 실행됩니다. CUDA는 NVIDIA GPU와 호환 CUDA·cuDNN이 설치된 PC용입니다.'
        wrap(ttk.Label(options,text=f'large-v3: 정확도 우선 / turbo: 처리 속도 우선\n{device_note}\n첫 실행은 수 GB를 다운로드합니다. CPU에서는 긴 음성 처리에 오래 걸릴 수 있어요.',style='Card.Muted.TLabel')).pack(fill='x',pady=(12,0))
        actions=ttk.Frame(body);actions.pack(fill='x',pady=(4,14))
        self.start=ttk.Button(actions,text='자막 · 연습 파일 만들기',style='Accent.TButton',command=self.begin);self.start.pack(side='left')
        self.cancel=ttk.Button(actions,text='중지',command=self.stop,state='disabled');self.cancel.pack(side='left',padx=8)
        ttk.Button(actions,text='결과 폴더 열기',command=self.open_output).pack(side='right')
        self.progress=ttk.Progressbar(body,maximum=100);self.progress.pack(fill='x')
        logcard=ttk.Frame(body,style='Card.TFrame');logcard.pack(fill='both',expand=True,pady=(12,0))
        self.log=theme.text(tk.Text(logcard,wrap='word',height=8));self.log.pack(side='left',fill='both',expand=True,padx=1,pady=1)
        scroll=ttk.Scrollbar(logcard,command=self.log.yview);scroll.pack(side='right',fill='y',padx=(0,1),pady=1);self.log.configure(yscrollcommand=scroll.set)
        theme.on_change(self.theme_label);theme.apply()
        self.append('준비됐어요. 원본 음성은 외부로 전송하지 않습니다.\n'+(f'결과는 {DATA/"results"} 안에 저장됩니다.' if FROZEN else 'Python 3.10~3.12 64비트 권장. 결과는 프로그램 폴더의 results 안에 저장됩니다.'))
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(150,self.poll)
        if MAC:root.createcommand('tk::mac::Quit',self.close)  # Cmd-Q bypasses WM_DELETE_WINDOW
        if updater.ENABLED:updater.cleanup(DATA/'updates');self.check_updates(auto=True)

    def card(self,parent,step,title):
        """A bordered section with a numbered heading; returns the frame to fill."""
        frame=ttk.Frame(parent,style='Card.TFrame',padding=(18,14,18,16));frame.pack(fill='x',pady=(0,12))
        head=ttk.Frame(frame,style='Inner.TFrame');head.pack(fill='x',pady=(0,10))
        ttk.Label(head,text=step,style='Step.TLabel').pack(side='left',padx=(0,8))
        ttk.Label(head,text=title,style='Card.Heading.TLabel').pack(side='left')
        return frame

    def theme_label(self):
        self.theme_button['text']='☀ 라이트 모드' if self.theme.mode=='dark' else '☾ 다크 모드'

    def append(self,text):
        self.log.insert('end',text+'\n');self.log.see('end')

    def choose(self):
        path=filedialog.askopenfilename(title='음성 파일 선택',filetypes=[('음성 파일','*.mp3 *.m4a *.wav *.ogg *.flac *.aac *.mp4'),('모든 파일','*.*')])
        if path:self.audio.set(path)

    def podcasts(self):
        if self.podcast_dialog and not self.podcast_dialog.closed:
            self.podcast_dialog.window.lift();return
        def downloaded(path):
            self.audio.set(str(path));self.append(f'다운로드 완료: {path}\n모델과 범위를 선택하고 자막 만들기를 누르세요.')
        self.podcast_dialog=PodcastDialog(self.root,DATA,downloaded,self.theme)

    def begin(self):
        if self.process:return
        source=Path(self.audio.get())
        if not source.is_file():messagebox.showerror('음성 선택','음성 파일을 먼저 선택해 주세요.');return
        self.output=DATA/'results'/f'{unicodedata.normalize("NFC",source.stem)[:50]}_{datetime.now():%Y%m%d_%H%M%S_%f}'
        command=([sys.executable,'--transcribe'] if FROZEN else [sys.executable,'-u',str(ROOT/'transcribe.py')])+[str(source),'--output',str(self.output),'--models',str(DATA/'models'),'--model',self.model.get(),'--language',self.lang.get(),'--device',self.device.get()]
        if self.scope.get()=='앞 30초 시험':command+=['--seconds','30']
        self.log.delete('1.0','end');self.progress['value']=0;self.start['state']='disabled';self.cancel['state']='normal'
        env=os.environ.copy();env['PYTHONUTF8']='1';env['PYTHONIOENCODING']='utf-8'
        try:
            self.process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except OSError as e:
            self.append(str(e));self.start['state']='normal';self.cancel['state']='disabled';return
        process=self.process
        def read():
            for line in process.stdout:self.events.put(('log',line.rstrip()))
            self.events.put(('exit',process.wait()))
        threading.Thread(target=read,daemon=True).start()

    def poll(self):
        while not self.events.empty():
            kind,value=self.events.get()
            if kind=='log':
                if value.startswith('PROGRESS|'):
                    _,pct,text=value.split('|',2);self.progress['value']=int(pct);self.append(text)
                elif value.startswith('DONE|'):
                    self.progress['value']=100;bundle=next(self.output.glob('*.echo.zip'),None)
                    self.append(f'완료! {bundle.name}을 휴대폰으로 옮겨주세요.' if bundle else '완료! 음성이 180MB를 넘어 ZIP을 만들지 않았어요.\n원본 음성과 transcript.echo.json을 따로 옮겨주세요.')
                else:self.append(value)
            elif kind=='exit':
                self.process=None;self.start['state']='normal';self.cancel['state']='disabled'
                if value!=0:self.append(f'종료 코드: {value}. 위 오류를 확인하거나 설정을 바꿔 다시 실행하세요.')
            elif kind=='update':
                release,auto=value
                if release:
                    self.release=release;self.update_button['text']=f'{release.tag} 업데이트'
                    self.append(f'새 버전 {release.tag}이 나왔어요. 다운로드 후 자동으로 다시 시작합니다.')
                    if messagebox.askyesno('업데이트',f'새 버전 {release.tag}이 나왔어요. 지금 업데이트할까요?\n다운로드가 끝나면 자동으로 다시 시작합니다.'):self.update_begin()
                elif not auto:self.append(f'최신 버전({updater.VERSION})을 사용 중입니다.')
            elif kind=='update-progress':
                n,total=value;self.progress['value']=n/total*100 if total else 0
            elif kind=='update-ready':
                self.append('설치하고 다시 시작합니다…')
                try:updater.install(value)
                except Exception as e:self.update_failed(f'{e}\n받은 파일: {value}');continue
                self.close();return
            elif kind=='update-error':
                message,auto=value
                if not auto:self.update_failed(message)
        self.root.after(150,self.poll)

    def check_updates(self,auto=False):
        """Ask GitHub Releases in the background; a failed automatic check stays silent."""
        def job():
            try:self.events.put(('update',(updater.latest(),auto)))
            except Exception as e:self.events.put(('update-error',(str(e),auto)))
        threading.Thread(target=job,daemon=True).start()

    def update_click(self):
        if self.updating:return
        if self.release:self.update_begin()
        else:self.append('업데이트를 확인하는 중…');self.check_updates()

    def update_begin(self):
        if self.updating or not self.release:return
        if self.process:messagebox.showinfo('업데이트','자막 생성이 끝난 뒤 업데이트해 주세요.');return
        self.updating=True;self.start['state']='disabled';self.update_button['state']='disabled';self.progress['value']=0
        self.append(f'{self.release.tag} 다운로드 중…');release=self.release
        def job():
            try:self.events.put(('update-ready',updater.download(release,DATA/'updates',lambda n,total:self.events.put(('update-progress',(n,total))))))
            except Exception as e:self.events.put(('update-error',(str(e),False)))
        threading.Thread(target=job,daemon=True).start()

    def update_failed(self,message):
        self.updating=False;self.start['state']='normal';self.update_button['state']='normal';self.progress['value']=0
        self.append('업데이트 실패: '+message)

    def stop(self):
        if self.process and self.process.poll() is None:self.process.terminate();self.append('중지 중…')

    def open_output(self):
        target=self.output if self.output and self.output.exists() else DATA/'results'
        target.mkdir(parents=True,exist_ok=True)
        if sys.platform=='win32':os.startfile(target)
        elif sys.platform=='darwin':subprocess.Popen(['open',str(target)])
        else:subprocess.Popen(['xdg-open',str(target)])

    def close(self):
        if self.podcast_dialog:self.podcast_dialog.close()
        self.stop();self.root.destroy()


if __name__=='__main__':
    multiprocessing.freeze_support()  # frozen app: helpers such as the resource tracker re-run this executable
    if sys.argv[1:2]==['--transcribe']:
        import transcribe;sys.argv.pop(1);sys.exit(transcribe.main())
    DATA.mkdir(parents=True,exist_ok=True)
    root=tk.Tk();App(root);root.mainloop()
