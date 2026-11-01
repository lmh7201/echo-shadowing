from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from podcasts import load_podcast,download_episode,DownloadCancelled,http_url
from podcast_history import PodcastHistory
from theme import wrap


class PodcastDialog:
    def __init__(self,parent,folder,on_download,theme):
        self.folder=Path(folder);self.on_download=on_download;self.events=queue.Queue();self.cancel=threading.Event();self.busy=False;self.closed=False;self.episodes=[];self.visible=[]
        self.window=tk.Toplevel(parent);self.window.title('Echo · 팟캐스트에서 음성 받기');self.window.geometry('840x700');self.window.minsize(660,560);theme.window(self.window)
        body=ttk.Frame(self.window,padding=(26,22,26,20));body.pack(fill='both',expand=True)
        ttk.Label(body,text='링크 한 번으로, 다음부터는 에피소드만 선택',style='Title.TLabel').pack(anchor='w')
        wrap(ttk.Label(body,text='애플 팟캐스트 공유 링크 또는 공개 RSS를 넣어주세요. 한 번 불러온 방송은 ▾ 목록에 남고, ★ 즐겨찾기는 맨 위에 보입니다.',style='Muted.TLabel')).pack(fill='x',pady=(6,16))
        source=ttk.Frame(body,style='Card.TFrame',padding=(18,14,18,12));source.pack(fill='x')
        ttk.Label(source,text='방송 링크',style='Field.TLabel').pack(anchor='w',pady=(0,4))
        self.history=PodcastHistory(self.folder/'podcast-source.json');self.choices=[]
        self.url=tk.StringVar(value=self.history.last);row=ttk.Frame(source,style='Inner.TFrame');row.pack(fill='x')
        self.picker=theme.combo(ttk.Combobox(row,textvariable=self.url,postcommand=self.refresh_choices));self.picker.pack(side='left',fill='x',expand=True)
        self.picker.bind('<<ComboboxSelected>>',self.pick)
        self.load=ttk.Button(row,text='에피소드 불러오기',style='Accent.TButton',command=self.fetch);self.load.pack(side='left',padx=(8,0))
        saved=ttk.Frame(source,style='Inner.TFrame');saved.pack(fill='x',pady=(8,0))
        self.star=ttk.Button(saved,text='☆ 즐겨찾기',style='CardGhost.TButton',command=self.toggle_favorite);self.star.pack(side='left')
        self.forget=ttk.Button(saved,text='목록에서 빼기',style='CardGhost.TButton',command=self.remove);self.forget.pack(side='left',padx=4)
        self.saved_note=tk.StringVar();ttk.Label(saved,textvariable=self.saved_note,style='Card.Muted.TLabel').pack(side='right')
        self.url.trace_add('write',lambda *_:self.refresh_saved());self.refresh_choices();self.refresh_saved()
        episodes=ttk.Frame(body,style='Card.TFrame',padding=(18,14,18,14));episodes.pack(fill='both',expand=True,pady=12)
        self.heading=tk.StringVar(value='링크를 넣고 에피소드 불러오기를 누르세요.')
        wrap(ttk.Label(episodes,textvariable=self.heading,style='Card.Heading.TLabel')).pack(fill='x',pady=(0,10))
        searchrow=ttk.Frame(episodes,style='Inner.TFrame');searchrow.pack(fill='x');ttk.Label(searchrow,text='제목 검색',style='Field.TLabel').pack(side='left',padx=(0,8))
        self.search=tk.StringVar();ttk.Entry(searchrow,textvariable=self.search).pack(side='left',fill='x',expand=True);self.search.trace_add('write',lambda *_:self.filter())
        listframe=ttk.Frame(episodes,style='Card.TFrame',padding=1);listframe.pack(fill='both',expand=True,pady=(10,0))
        self.list=theme.listbox(tk.Listbox(listframe,height=6,exportselection=False,selectmode='browse'));self.list.pack(side='left',fill='both',expand=True,padx=(6,0),pady=4)
        scroll=ttk.Scrollbar(listframe,command=self.list.yview);scroll.pack(side='right',fill='y');self.list.configure(yscrollcommand=scroll.set)
        self.progress=ttk.Progressbar(body,maximum=100);self.progress.pack(fill='x')
        self.status=tk.StringVar(value='에피소드를 불러온 뒤 원하는 회차를 선택하세요.')
        wrap(ttk.Label(body,textvariable=self.status)).pack(fill='x',pady=10)
        actions=ttk.Frame(body);actions.pack(fill='x')
        self.download=ttk.Button(actions,text='선택한 음성 받기 → 자막 생성에 사용',style='Accent.TButton',state='disabled',command=self.get);self.download.pack(side='left')
        self.stop=ttk.Button(actions,text='중지',state='disabled',command=self.cancel.set);self.stop.pack(side='left',padx=8)
        ttk.Button(actions,text='닫기',command=self.close).pack(side='right')
        ttk.Label(body,text='원본 파일을 변환 없이 저장합니다. 공개 RSS로 배포되는 에피소드만 지원합니다.',style='Muted.TLabel').pack(anchor='w',pady=(12,0))
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.window.after(100,self.poll)

    @staticmethod
    def label(entry):
        text=('★ ' if entry['favorite'] else '')+(f"{entry['title']}  ·  {entry['url']}" if entry['title'] else entry['url'])
        return text if len(text)<=110 else text[:107]+'…'

    def refresh_choices(self):
        self.choices=self.history.ordered();self.picker['values']=[self.label(e) for e in self.choices]

    def refresh_saved(self):
        entry=self.history.find(self.url.get())
        self.star['text']='★ 즐겨찾기 해제' if entry and entry['favorite'] else '☆ 즐겨찾기'
        self.forget['state']='normal' if entry else 'disabled'
        favorites=sum(e['favorite'] for e in self.history.entries)
        self.saved_note.set(f'저장된 방송 {len(self.history.entries)}개 · 즐겨찾기 {favorites}개' if self.history.entries else '불러온 방송은 여기에 저장됩니다.')

    def pick(self,_event=None):
        index=self.picker.current()
        if 0<=index<len(self.choices):self.url.set(self.choices[index]['url']);self.picker.selection_clear();self.fetch()

    def toggle_favorite(self):
        url=self.url.get().strip()
        if not url:self.status.set('즐겨찾기할 링크를 먼저 넣어주세요.');return
        try:url=http_url(url)
        except ValueError as e:self.status.set(str(e));return
        favorite=self.history.toggle_favorite(url);self.url.set(url);self.refresh_choices();self.refresh_saved()
        self.status.set('즐겨찾기에 추가했어요. ▾ 목록 맨 위에 보입니다.' if favorite else '즐겨찾기에서 뺐어요. 목록에는 그대로 남아 있습니다.')

    def remove(self):
        if self.history.remove(self.url.get()):
            self.url.set('');self.refresh_choices();self.refresh_saved();self.status.set('목록에서 뺐어요. 다시 불러오면 또 저장됩니다.')

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
                self.history.record(url,title);self.refresh_choices();self.refresh_saved()
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
