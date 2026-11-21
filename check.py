"""檢查可公開網站的本機連結、頁面結構與 Wiki 引用。"""
import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent
SITE = ROOT if (ROOT/'index.html').exists() else ROOT/'dist'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.ids=[]; self.refs=[]; self.h1=0; self.lang=None
        self.feed(text)
    def handle_starttag(self, tag, attributes):
        a=dict(attributes)
        if a.get('id'): self.ids.append(a['id'])
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if tag in ('a','link') and 'href' in a: self.refs.append(a['href'])
        if tag=='script' and 'src' in a: self.refs.append(a['src'])
pages={p.name:Page(p.read_text()) for p in SITE.glob('*.html')}
errors=[]
count=0
for name,p in pages.items():
    if p.h1!=1 or p.lang!='zh-Hant': errors.append(name+': 語言或 h1 不正確')
    if len(p.ids)!=len(set(p.ids)): errors.append(name+': 重複 id')
    for ref in p.refs:
        u=urlsplit(ref)
        if u.scheme or u.netloc: continue
        target=unquote(u.path) or name
        if not (SITE/target).is_file(): errors.append(name+': 找不到 '+ref)
        elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
            errors.append(name+': 錨點不存在 '+ref)
        count+=1
sources=json.loads((SITE/'source-notes.json').read_text())
wiki=json.loads((SITE/'wiki.json').read_text())
slides=json.loads((SITE/'lesson.json').read_text())
source_ids={s['id'] for s in sources}
claims={c['id']:c for w in wiki for c in w['claims']}
assert len({s['url'] for s in sources})>=5
assert all(set(c['sources'])<=source_ids and c['sources'] for c in claims.values())
assert all(set(s['claims'])<=set(claims) for s in slides)
assert not errors, '\n'.join(errors)
report={'html_pages':len(pages),'local_links_checked':count,'sources':len(sources),'wiki_pages':len(wiki),'slides':len(slides),'status':'PASS','checks':['每頁一個 h1 及繁體中文語言標記','沒有重複 HTML id','本機頁面、資源及錨點存在','來源至少 5 篇且不重複','Wiki 與簡報引用 ID 有效']}
(SITE/'structure-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
