"""Remembers every podcast link that loaded, and which ones the user starred."""
from datetime import datetime,timezone
import json
from pathlib import Path

MAX_RECENT=50  # unstarred links beyond this are dropped, oldest first; favorites are never pruned


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class PodcastHistory:
    """podcast-source.json: {"url": last opened, "history": [{"url","title","favorite","used"}, ...]}.

    The top-level "url" is kept so older builds that only read it keep working."""

    def __init__(self,path):
        self.path=Path(path);self.entries=[];self.last=''
        try:data=json.loads(self.path.read_text('utf8'))
        except (OSError,ValueError):data={}
        if not isinstance(data,dict):data={}
        self.last=data.get('url','') if isinstance(data.get('url'),str) else ''
        for item in data.get('history',[]) if isinstance(data.get('history'),list) else []:
            if not isinstance(item,dict) or not isinstance(item.get('url'),str) or not item['url'].strip():continue
            self.entries.append({'url':item['url'].strip(),'title':str(item.get('title','') or ''),'favorite':bool(item.get('favorite')),'used':str(item.get('used','') or '')})
        if self.last and not self.find(self.last):self.entries.append({'url':self.last.strip(),'title':'','favorite':False,'used':''})  # migrate the single remembered link

    def find(self,url):
        url=url.strip();return next((e for e in self.entries if e['url']==url),None)

    def ordered(self):
        """Favorites first, then the rest; each group most recently used first."""
        return sorted(self.entries,key=lambda e:(e['favorite'],e['used']),reverse=True)

    def record(self,url,title=''):
        url=url.strip()
        if not url:return None
        entry=self.find(url)
        if entry is None:entry={'url':url,'title':'','favorite':False,'used':''};self.entries.append(entry)
        if title:entry['title']=title
        entry['used']=now();self.last=url;self.prune();self.save();return entry

    def toggle_favorite(self,url):
        url=url.strip()
        if not url:return None
        entry=self.find(url)
        if entry is None:entry={'url':url,'title':'','favorite':False,'used':now()};self.entries.append(entry)
        entry['favorite']=not entry['favorite'];self.prune();self.save();return entry['favorite']

    def remove(self,url):
        entry=self.find(url)
        if entry is None:return False
        self.entries.remove(entry)
        if self.last==entry['url']:self.last=''
        self.save();return True

    def prune(self):
        recent=sorted((e for e in self.entries if not e['favorite']),key=lambda e:e['used'],reverse=True)
        for entry in recent[MAX_RECENT:]:self.entries.remove(entry)

    def save(self):
        try:self.path.write_text(json.dumps({'url':self.last,'history':self.entries},ensure_ascii=False,indent=1),encoding='utf8')
        except OSError:pass
