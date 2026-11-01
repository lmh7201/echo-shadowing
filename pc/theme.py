"""Light and dark looks for the Echo PC windows, built on ttk's 'clam' so every platform draws the same colors."""
import json
from pathlib import Path
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

MAC=sys.platform=='darwin';WIN=sys.platform=='win32'
# The light palette follows the web app (web/style.css); the dark one keeps the same green on a deep forest ground.
PALETTES={
    'light':dict(bg='#f6f5f0',card='#ffffff',soft='#f1f3ed',line='#e4e6de',strong='#cfd5c8',ink='#263c32',muted='#7e857e',
                 accent='#376c4c',accent_hover='#2f5e42',accent_ink='#ffffff',accent_soft='#edf3e9',field='#ffffff',
                 log='#fafaf7',select='#376c4c',select_ink='#ffffff',disabled='#b4bab1'),
    'dark':dict(bg='#121815',card='#1a221e',soft='#242e29',line='#2b3631',strong='#3a4740',ink='#e4ebe5',muted='#8f9c93',
                accent='#6fae84',accent_hover='#84c198',accent_ink='#0e1611',accent_soft='#20322a',field='#141b17',
                log='#151c18',select='#2f5a42',select_ink='#ffffff',disabled='#56625b'),
}
FAMILY='Apple SD Gothic Neo' if MAC else 'Malgun Gothic' if WIN else None


def system_mode():
    """Read the OS light/dark preference; anything unreadable counts as light."""
    try:
        if WIN:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
                return 'light' if winreg.QueryValueEx(key,'AppsUseLightTheme')[0] else 'dark'
        if MAC:
            out=subprocess.run(['defaults','read','-g','AppleInterfaceStyle'],capture_output=True,text=True,timeout=2).stdout
            return 'dark' if 'Dark' in out else 'light'
    except Exception:pass
    return 'light'


class Theme:
    """Owns the ttk styles plus the classic tk widgets (Text, Listbox, windows) that ttk styles cannot reach."""
    def __init__(self,root,settings):
        self.root=root;self.settings=Path(settings);self.windows=[];self.texts=[];self.lists=[];self.combos=[];self.listeners=[]
        try:saved=json.loads(self.settings.read_text('utf8')).get('theme')
        except (OSError,ValueError,AttributeError):saved=None
        self.mode=saved if saved in PALETTES else system_mode()
        self.style=ttk.Style(root);self.style.theme_use('clam');self.fonts()
        self.window(root)

    @property
    def c(self):return PALETTES[self.mode]

    def fonts(self):
        size=13 if MAC else 10
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkHeadingFont'):
            font=tkfont.nametofont(name);font.configure(size=size,**({'family':FAMILY} if FAMILY else {}))
        base=tkfont.nametofont('TkDefaultFont').actual('family')
        self.font=dict(title=(base,size+10,'bold'),heading=(base,size+2,'bold'),brand=(base,size+5,'bold'),
                       body=(base,size),small=(base,size-1),strong=(base,size,'bold'),button=(base,size,'bold'))

    def toggle(self):
        self.mode='dark' if self.mode=='light' else 'light'
        try:self.settings.parent.mkdir(parents=True,exist_ok=True);self.settings.write_text(json.dumps({'theme':self.mode}),'utf8')
        except OSError:pass
        self.apply()

    # Registration: each call styles the widget now and again on every toggle.
    def window(self,w):self.windows.append(w);self.apply_window(w);return w
    def text(self,w):self.texts.append(w);self.apply_text(w);return w
    def listbox(self,w):self.lists.append(w);self.apply_list(w);return w
    def combo(self,w):self.combos.append(w);self.apply_combo(w);return w
    def on_change(self,fn):self.listeners.append(fn)

    def apply(self):
        self.apply_styles()
        for group,fn in ((self.windows,self.apply_window),(self.texts,self.apply_text),(self.lists,self.apply_list),(self.combos,self.apply_combo)):
            group[:]=[w for w in group if self.alive(w)]
            for w in group:fn(w)
        for fn in self.listeners:fn()

    @staticmethod
    def alive(w):
        try:return bool(w.winfo_exists())
        except tk.TclError:return False

    def apply_styles(self):
        c=self.c;s=self.style;f=self.font
        s.configure('.',background=c['bg'],foreground=c['ink'],bordercolor=c['line'],lightcolor=c['bg'],darkcolor=c['bg'],
                    troughcolor=c['soft'],focuscolor=c['accent'],selectbackground=c['select'],selectforeground=c['select_ink'],
                    fieldbackground=c['field'],insertcolor=c['ink'],arrowcolor=c['muted'],font=f['body'])
        s.map('.',foreground=[('disabled',c['disabled'])])
        s.configure('TFrame',background=c['bg'])
        s.configure('Card.TFrame',background=c['card'],bordercolor=c['line'],lightcolor=c['card'],darkcolor=c['card'],relief='solid',borderwidth=1)
        s.configure('Inner.TFrame',background=c['card'])
        for name,bg in (('',c['bg']),('Card.',c['card'])):
            s.configure(f'{name}TLabel',background=bg,foreground=c['ink'])
            s.configure(f'{name}Muted.TLabel',background=bg,foreground=c['muted'],font=f['small'])
            s.configure(f'{name}Heading.TLabel',background=bg,foreground=c['ink'],font=f['heading'])
        s.configure('Title.TLabel',background=c['bg'],foreground=c['ink'],font=f['title'])
        s.configure('Brand.TLabel',background=c['bg'],foreground=c['ink'],font=f['brand'])
        s.configure('Chip.TLabel',background=c['accent_soft'],foreground=c['accent'],font=f['small'],padding=(8,2))
        s.configure('Step.TLabel',background=c['accent_soft'],foreground=c['accent'],font=f['strong'],padding=(7,1),anchor='center')
        s.configure('Field.TLabel',background=c['card'],foreground=c['muted'],font=f['small'])
        # Buttons: Accent is the one main action, plain TButton is secondary, Ghost reads as a link on any ground.
        button=dict(borderwidth=1,focusthickness=1,padding=(14,7),relief='flat',font=f['body'])
        s.configure('TButton',background=c['soft'],foreground=c['ink'],bordercolor=c['line'],lightcolor=c['soft'],darkcolor=c['soft'],**button)
        s.map('TButton',background=[('disabled',c['soft']),('pressed',c['strong']),('active',c['line'])],
              lightcolor=[('pressed',c['strong']),('active',c['line'])],darkcolor=[('pressed',c['strong']),('active',c['line'])],
              bordercolor=[('focus',c['accent'])],foreground=[('disabled',c['disabled'])])
        s.configure('Accent.TButton',background=c['accent'],foreground=c['accent_ink'],bordercolor=c['accent'],lightcolor=c['accent'],darkcolor=c['accent'],
                    **{**button,'padding':(22,10),'font':f['button']})
        s.map('Accent.TButton',background=[('disabled',c['soft']),('pressed',c['accent_hover']),('active',c['accent_hover'])],
              lightcolor=[('disabled',c['soft']),('active',c['accent_hover'])],darkcolor=[('disabled',c['soft']),('active',c['accent_hover'])],
              bordercolor=[('disabled',c['line']),('focus',c['ink'])],foreground=[('disabled',c['disabled'])])
        for name,bg in (('Ghost',c['bg']),('CardGhost',c['card'])):
            s.configure(f'{name}.TButton',background=bg,foreground=c['accent'],bordercolor=bg,lightcolor=bg,darkcolor=bg,**{**button,'padding':(8,5),'font':f['strong']})
            s.map(f'{name}.TButton',background=[('pressed',c['accent_soft']),('active',c['accent_soft'])],lightcolor=[('active',c['accent_soft'])],
                  darkcolor=[('active',c['accent_soft'])],bordercolor=[('focus',c['accent']),('active',c['accent_soft'])],foreground=[('disabled',c['disabled'])])
        field=dict(fieldbackground=c['field'],foreground=c['ink'],bordercolor=c['strong'],lightcolor=c['field'],darkcolor=c['field'],padding=(8,6),insertcolor=c['ink'])
        s.configure('TEntry',**field)
        s.map('TEntry',bordercolor=[('focus',c['accent'])],lightcolor=[('focus',c['accent'])])
        s.configure('TCombobox',**field,background=c['field'],arrowcolor=c['muted'],arrowsize=13)
        s.map('TCombobox',fieldbackground=[('readonly',c['field'])],foreground=[('readonly',c['ink']),('disabled',c['disabled'])],
              selectbackground=[('readonly',c['field'])],selectforeground=[('readonly',c['ink'])],
              background=[('active',c['soft']),('readonly',c['field'])],bordercolor=[('focus',c['accent']),('active',c['accent'])],
              lightcolor=[('focus',c['accent'])],arrowcolor=[('active',c['accent'])])
        s.configure('Horizontal.TProgressbar',background=c['accent'],troughcolor=c['soft'],bordercolor=c['soft'],lightcolor=c['accent'],darkcolor=c['accent'],arrowsize=7)  # clam sizes the bar by arrowsize
        s.configure('Vertical.TScrollbar',background=c['soft'],troughcolor=c['card'],bordercolor=c['card'],lightcolor=c['soft'],darkcolor=c['soft'],arrowcolor=c['muted'],gripcount=0)
        s.map('Vertical.TScrollbar',background=[('active',c['line'])])
        # The combobox drop-down is a classic Listbox; new pop-downs pick these up, existing ones are fixed in apply_combo.
        for key,value in (('background',c['card']),('foreground',c['ink']),('selectBackground',c['select']),('selectForeground',c['select_ink'])):
            self.root.option_add(f'*TCombobox*Listbox.{key}',value)

    def apply_window(self,w):
        w.configure(background=self.c['bg']);self.titlebar(w)

    def apply_text(self,w):
        c=self.c;w.configure(background=c['log'],foreground=c['ink'],insertbackground=c['ink'],selectbackground=c['select'],selectforeground=c['select_ink'],
                             relief='flat',borderwidth=0,highlightthickness=0,padx=14,pady=12,font=self.font['body'],spacing1=2,spacing3=2)

    def apply_list(self,w):
        c=self.c;w.configure(background=c['card'],foreground=c['ink'],selectbackground=c['select'],selectforeground=c['select_ink'],
                             relief='flat',borderwidth=0,highlightthickness=0,activestyle='none',font=self.font['body'])

    def apply_combo(self,w):
        c=self.c
        try:
            popdown=w.tk.eval(f'ttk::combobox::PopdownWindow {w}')
            w.tk.call(f'{popdown}.f.l','configure','-background',c['card'],'-foreground',c['ink'],'-selectbackground',c['select'],
                      '-selectforeground',c['select_ink'],'-borderwidth',0,'-relief','flat','-font',self.font['body'])
        except tk.TclError:pass

    def titlebar(self,w):
        """Match the native title bar to the theme where the OS lets an app ask for it."""
        dark=self.mode=='dark'
        if MAC:
            try:w.tk.call('::tk::unsupported::MacWindowStyle','appearance',w._w,'darkaqua' if dark else 'aqua')
            except tk.TclError:pass
            return
        if not WIN:return
        def paint():
            try:
                import ctypes
                hwnd=ctypes.windll.user32.GetParent(w.winfo_id());value=ctypes.c_int(1 if dark else 0)
                for attribute in (20,19):  # DWMWA_USE_IMMERSIVE_DARK_MODE on Windows 11/10 20H1+, then older Windows 10
                    if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd,attribute,ctypes.byref(value),ctypes.sizeof(value))==0:break
            except Exception:pass
        w.after_idle(paint)


def wrap(label,margin=0):
    """Let a label's text reflow with its container instead of a fixed wraplength."""
    label.bind('<Configure>',lambda e:label.configure(wraplength=max(e.width-margin,120)),add='+')
    return label
