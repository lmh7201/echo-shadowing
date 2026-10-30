import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from podcasts import DEFAULT_URL,load_podcast,download_episode,DownloadCancelled


class PodcastDialog:
    def __init__(self,parent,folder,on_download):
        self.folder=Path(folder);self.on_download=on_download;self.events=queue.Queue();self.cancel=threading.Event();self.busy=False;self.closed=False;self.episodes=[];self.visible=[]
        self.window=tk.Toplevel(parent);self.window.title('Echo · 팟캐스트에서 음성 받기');self.window.geometry('820x620');self.window.minsize(650,500)
        body=ttk.Frame(self.window,padding=20);body.pack(fill='both',expand=True)
        ttk.Label(body,text='링크 한 번으로, 다음부터는 에피소드만 선택',font=('',15,'bold')).pack(anchor='w')
        ttk.Label(body,text='애플 팟캐스트 공유 링크 또는 공개 RSS를 넣어주세요. 마지막으로 연 방송을 기억합니다.',wraplength=760).pack(anchor='w',pady=10)
        saved=DEFAULT_URL
        try:saved=json.loads((self.folder/'podcast-source.json').read_text('utf8')).get('url',saved)
        except (OSError,ValueError,TypeError):pass
        self.url=tk.StringVar(value=saved);row=ttk.Frame(body);row.pack(fill='x')
        ttk.Entry(row,textvariable=self.url).pack(side='left',fill='x',expand=True)
        self.load=ttk.Button(row,text='에피소드 불러오기',command=self.fetch);self.load.pack(side='left',padx=(8,0))
        self.heading=tk.StringVar(value='처음에는 YUYU 방송 링크가 준비되어 있어요.')
        ttk.Label(body,textvariable=self.heading,wraplength=760).pack(anchor='w',pady=12)
        searchrow=ttk.Frame(body);searchrow.pack(fill='x');ttk.Label(searchrow,text='제목 검색 ').pack(side='left')
        self.search=tk.StringVar();ttk.Entry(searchrow,textvariable=self.search).pack(side='left',fill='x',expand=True);self.search.trace_add('write',lambda *_:self.filter())
        listframe=ttk.Frame(body);listframe.pack(fill='both',expand=True,pady=10)
        self.list=tk.Listbox(listframe,font=('',11),exportselection=False,selectmode='browse');self.list.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(listframe,command=self.list.yview);scroll.pack(side='right',fill='y');self.list.configure(yscrollcommand=scroll.set)
        self.progress=ttk.Progressbar(body,maximum=100);self.progress.pack(fill='x')
        self.status=tk.StringVar(value='에피소드를 불러온 뒤 원하는 회차를 선택하세요.')
        ttk.Label(body,textvariable=self.status,wraplength=760).pack(anchor='w',pady=10)
        actions=ttk.Frame(body);actions.pack(fill='x')
        self.download=ttk.Button(actions,text='선택한 음성 받기 → 자막 생성에 사용',state='disabled',command=self.get);self.download.pack(side='left')
        self.stop=ttk.Button(actions,text='중지',state='disabled',command=self.cancel.set);self.stop.pack(side='left',padx=8)
        ttk.Button(actions,text='닫기',command=self.close).pack(side='right')
        ttk.Label(body,text='원본 파일을 변환 없이 저장합니다. 공개 RSS로 배포되는 에피소드만 지원합니다.',foreground='#637061').pack(anchor='w',pady=(12,0))
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.window.after(100,self.poll)

    def set_busy(self,busy):
        self.busy=busy;self.load['state']='disabled' if busy else 'normal';self.download['state']='disabled' if busy or not self.visible else 'normal';self.stop['state']='normal' if busy else 'disabled'

    def fetch(self):
        if self.busy:return
        url=self.url.get();self.cancel.clear();self.set_busy(True);self.status.set('방송과 공개 RSS를 찾는 중…');self.progress['value']=0
        def job():
            try:self.events.put(('feed',(load_podcast(url),url)))
            except Exception as e:self.events.put(('error',str(e)))
        threading.Thread(target=job,daemon=True).start()

    def filter(self):
        query=self.search.get().casefold();self.visible=[e for e in self.episodes if query in e.title.casefold()];self.list.delete(0,'end')
        for e in self.visible:self.list.insert('end',f'{e.date}  {e.duration}  {e.title}')
        if self.visible:self.list.selection_set(0)
        if not self.busy:self.download['state']='normal' if self.visible else 'disabled'

    def get(self):
        if self.busy:return
        selected=self.list.curselection()
        if not selected:messagebox.showinfo('에피소드 선택','받을 에피소드를 선택해 주세요.',parent=self.window);return
        episode=self.visible[selected[0]];self.cancel.clear();self.set_busy(True);self.status.set('원본 음성 다운로드 중…');self.progress['value']=0
        def job():
            try:
                result=download_episode(episode,self.folder/'downloads',lambda n,total:self.events.put(('progress',(n,total))),self.cancel)
                self.events.put(('done',result))
            except DownloadCancelled:self.events.put(('error','다운로드를 중지했습니다. 다시 시도할 수 있어요.'))
            except Exception as e:self.events.put(('error',str(e)))
        threading.Thread(target=job,daemon=True).start()

    def poll(self):
        if self.closed:return
        while not self.events.empty():
            kind,value=self.events.get()
            if kind=='feed':
                (title,episodes,feed),url=value
                if self.cancel.is_set():self.status.set('불러오기를 중지했습니다.');self.set_busy(False);continue
                self.episodes=episodes;self.heading.set(f'{title} · {len(episodes)}개 에피소드');self.filter();self.status.set('원하는 회차를 선택한 뒤 음성 받기를 누르세요.');self.set_busy(False)
                try:(self.folder/'podcast-source.json').write_text(json.dumps({'url':url},ensure_ascii=False),encoding='utf8')
                except OSError:pass
            elif kind=='progress':
                n,total=value;self.progress['value']=n/total*100 if total else 0
                self.status.set(f'다운로드 중 · {n/1024/1024:.1f} MB'+(f' / {total/1024/1024:.1f} MB' if total else ''))
            elif kind=='done':
                self.on_download(value);self.close();return
            else:self.status.set('다시 시도해 주세요. '+value);self.set_busy(False)
        self.window.after(100,self.poll)

    def close(self):
        if self.closed:return
        self.closed=True;self.cancel.set();self.window.destroy()
