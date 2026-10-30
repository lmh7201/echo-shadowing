"""Echo PC: a local desktop front end; recognition runs in a cancellable process."""
from datetime import datetime
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from podcast_dialog import PodcastDialog

ROOT=Path(__file__).resolve().parent


class App:
    def __init__(self,root):
        self.root=root;self.process=None;self.events=queue.Queue();self.output=None;self.podcast_dialog=None
        root.title('Echo PC · 고정밀 자막 생성');root.geometry('740x650');root.minsize(630,540)
        body=ttk.Frame(root,padding=24);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Echo PC · 한 번 만들고, 어디서나 연습',font=('',17,'bold')).pack(anchor='w')
        ttk.Label(body,text='PC에서 음성·단어별 시간·자막을 하나의 연습 파일로 만듭니다.\n완성된 practice.echo.zip을 모바일 웹페이지의 ‘연습 파일 열기’로 불러오세요.',wraplength=660).pack(anchor='w',pady=(10,18))
        self.audio=tk.StringVar();row=ttk.Frame(body);row.pack(fill='x')
        ttk.Entry(row,textvariable=self.audio).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='음성 선택',command=self.choose).pack(side='left',padx=(8,0))
        ttk.Button(body,text='↧ 팟캐스트에서 음성 받기 · Apple Podcasts / RSS',command=self.podcasts).pack(anchor='w',pady=(10,0))
        options=ttk.Frame(body);options.pack(fill='x',pady=16)
        self.model=tk.StringVar(value='large-v3');self.lang=tk.StringVar(value='ja');self.scope=tk.StringVar(value='앞 30초 시험');self.device=tk.StringVar(value='cpu')
        for i,(label,var,values) in enumerate([('모델',self.model,['large-v3','turbo','medium']),('언어',self.lang,['ja','en','ko','zh','es','fr','de','auto']),('범위',self.scope,['앞 30초 시험','전체 음성']),('실행 장치',self.device,['cpu','cuda'])]):
            ttk.Label(options,text=label).grid(row=0,column=i,sticky='w')
            ttk.Combobox(options,textvariable=var,values=values,state='readonly',width=15).grid(row=1,column=i,padx=(0,10),pady=6,sticky='ew')
            options.columnconfigure(i,weight=1)
        ttk.Label(body,text='large-v3: 정확도 우선 / turbo: 처리 속도 우선\nCPU는 별도 그래픽카드 없이 실행됩니다. CUDA는 NVIDIA GPU와 호환 CUDA·cuDNN이 설치된 PC용입니다.\n첫 실행은 수 GB를 다운로드합니다. CPU에서는 긴 음성 처리에 오래 걸릴 수 있어요.',wraplength=660,foreground='#637061').pack(anchor='w')
        actions=ttk.Frame(body);actions.pack(fill='x',pady=16)
        self.start=ttk.Button(actions,text='자막 · 연습 파일 만들기',command=self.begin);self.start.pack(side='left')
        self.cancel=ttk.Button(actions,text='중지',command=self.stop,state='disabled');self.cancel.pack(side='left',padx=8)
        self.open=ttk.Button(actions,text='결과 폴더 열기',command=self.open_output,state='disabled');self.open.pack(side='right')
        self.progress=ttk.Progressbar(body,maximum=100);self.progress.pack(fill='x')
        self.log=tk.Text(body,wrap='word',height=12,font=('Consolas',10));self.log.pack(fill='both',expand=True,pady=(12,0))
        self.append('준비됐어요. 원본 음성은 외부로 전송하지 않습니다.\nPython 3.10~3.12 64비트 권장. 결과는 프로그램 폴더의 results 안에 저장됩니다.')
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(150,self.poll)

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
        self.podcast_dialog=PodcastDialog(self.root,ROOT,downloaded)

    def begin(self):
        if self.process:return
        source=Path(self.audio.get())
        if not source.is_file():messagebox.showerror('음성 선택','음성 파일을 먼저 선택해 주세요.');return
        self.output=ROOT/'results'/f'{source.stem[:50]}_{datetime.now():%Y%m%d_%H%M%S_%f}'
        command=[sys.executable,'-u',str(ROOT/'transcribe.py'),str(source),'--output',str(self.output),'--model',self.model.get(),'--language',self.lang.get(),'--device',self.device.get()]
        if self.scope.get()=='앞 30초 시험':command+=['--seconds','30']
        self.log.delete('1.0','end');self.progress['value']=0;self.start['state']='disabled';self.cancel['state']='normal';self.open['state']='disabled'
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
                    self.progress['value']=100;self.append('완료! practice.echo.zip을 휴대폰으로 옮겨주세요.\n180MB가 넘는 음성은 원본 음성과 transcript.echo.json을 따로 옮겨주세요.')
                else:self.append(value)
            else:
                self.process=None;self.start['state']='normal';self.cancel['state']='disabled'
                if value==0:self.open['state']='normal'
                else:self.append(f'종료 코드: {value}. 위 오류를 확인하거나 설정을 바꿔 다시 실행하세요.')
        self.root.after(150,self.poll)

    def stop(self):
        if self.process and self.process.poll() is None:self.process.terminate();self.append('중지 중…')

    def open_output(self):
        if self.output and self.output.exists():
            if sys.platform=='win32':os.startfile(self.output)
            elif sys.platform=='darwin':subprocess.Popen(['open',str(self.output)])
            else:subprocess.Popen(['xdg-open',str(self.output)])

    def close(self):
        if self.podcast_dialog:self.podcast_dialog.close()
        self.stop();self.root.destroy()


if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
