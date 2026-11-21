"""從來源筆記、Wiki 條目與教學大綱，產生可離線閱讀的 HTML。只使用標準函式庫。"""
import json
from pathlib import Path
from html import escape as e
from datetime import datetime, timezone, timedelta
import shutil

ROOT = Path(__file__).resolve().parent
OUT = ROOT if (ROOT/'source-notes.json').exists() else ROOT / 'dist'
OUT.mkdir(exist_ok=True)
sources = json.loads((ROOT/'source-notes.json').read_text()) if (ROOT/'source-notes.json').exists() else [json.loads(p.read_text()) for p in sorted((ROOT/'sources').glob('s*.json'))]
wiki = json.loads((ROOT/'wiki.json').read_text())
lesson = json.loads((ROOT/'lesson.json').read_text())
plan = json.loads((ROOT/'project-plan.json').read_text())
source_by_id = {s['id']: s for s in sources}
wiki_by_id = {w['id']: w for w in wiki}
claims = {c['id']: (w, c) for w in wiki for c in w['claims']}

def wiki_url(w):
    return 'wiki-' + w['slug'] + '.html'

def nav(active=''):
    return '<header class="site-header"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">M</span>捷運新手學堂</a><nav aria-label="主要導覽">'+''.join(f'<a {"aria-current=page" if key==active else ""} href="{url}">{name}</a>' for key,url,name in [('wiki','index.html','Wiki'),('slides','slides.html','教學簡報'),('workflow','workflow.html','製作流程')])+'</nav></header>'

def page(title, body, active='', script=''):
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="以五篇臺北捷運官方資料整理的乘車知識庫與教學簡報。"><title>{e(title)}｜捷運新手學堂</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">跳到內容</a>{nav(active)}{body}<footer class="site-footer">非官方學習專案 · 資料查核 2026-11-21 · 不提供即時班次<br>AI 協助整理與製作；實際規定及公告請以臺北捷運官方資訊為準。</footer>{script}</body></html>'''

def source_links(ids):
    return ' · '.join(f'<a href="sources.html#{sid}">{sid} {e(source_by_id[sid]["title"])}</a>' for sid in ids)

def phrase(w):
    p = w['phrase']
    return f'<aside class="phrase"><span class="eyebrow">一句英文，開口求助</span><p lang="en">{e(p["en"])}</p><p>{e(p["zh"])}</p><small>{e(p["label"])}</small></aside>'

def claim_html(c, tag='article'):
    return f'<{tag} class="claim" id="{c["id"]}"><h3>{e(c["title"])}</h3><p>{e(c["text"])}</p><div class="source-line">{source_links(c["sources"])}</div></{tag}>'

cards = ''.join(f'<a class="wiki-card" href="{wiki_url(w)}"><span class="eyebrow">{w["id"]}</span><h2>{e(w["title"])}</h2><p>{e(w["question"])}</p><span class="text-link">閱讀這一頁</span></a>' for w in wiki)
body = f'''<main id="main"><section class="hero"><div><span class="eyebrow">LLM WIKI / 臺北捷運新手乘車</span><h1>第一次搭捷運，<br>從這裡開始。</h1><p class="lead">把官方規定整理成看得懂、找得到的知識。<br>先讀 Wiki，再用一份簡報，走過一趟旅程。</p><div class="actions"><a class="button" href="slides.html">開始教學簡報</a><a class="button secondary" href="#topics">瀏覽 Wiki</a></div></div><div class="journey-art" aria-label="本課學習順序：車票、候車、站內安全、求助"><span class="art-caption">YOUR FIRST METRO RIDE</span><ol><li>車票<span>TICKET</span></li><li>候車<span>BOARDING</span></li><li>安全<span>SAFETY</span></li><li>求助<span>ASK FOR HELP</span></li></ol><p>一趟旅程，四個學習重點。</p></div></section><section class="section" id="topics"><div class="section-heading"><div><span class="eyebrow">KNOWLEDGE BASE</span><h2>從你的問題開始</h2></div><a href="sources.html">查看 5 篇來源與匯入摘要</a></div><div class="wiki-grid">{cards}</div></section><section class="note-band"><h2>這份 Wiki 怎麼來的？</h2><p>先討論主題，再由 AI 閱讀 5 篇官方資料、保存來源摘要，整理為 4 個互相連結的主題頁。簡報從這些 Wiki 條目選取內容，每個重點都保留來源。</p><p>這是由 AI 協助建立的檔案式知識庫；網頁閱讀時不會重新呼叫模型，也不是即時交通查詢服務。</p><a href="workflow.html">查看完整流程與真實檢查紀錄</a></section></main>'''
(OUT/'index.html').write_text(page('第一次搭捷運，從這裡開始', body, 'wiki'))

for w in wiki:
    related = ' '.join(f'<a class="pill" href="{wiki_url(wiki_by_id[r])}">{e(wiki_by_id[r]["title"])}</a>' for r in w['related'])
    body = f'<main id="main" class="reading"><a href="index.html">Wiki 首頁</a><span class="eyebrow block">{w["id"]} / 知識條目</span><h1>{e(w["title"])}</h1><p class="lead">{e(w["intro"])}</p><p class="meta">查核日期：2026-11-21 · AI 依官方資料摘要整理</p><section aria-label="重點">'+''.join(claim_html(c) for c in w['claims'])+f'</section>{phrase(w)}<section class="related"><h2>接著閱讀</h2>{related}</section><p><a href="slides.html">用教學簡報練習</a></p></main>'
    (OUT/wiki_url(w)).write_text(page(w['title'],body,'wiki'))

source_cards = ''
for s in sources:
    used_by = [w for w in wiki if any(s['id'] in c['sources'] for c in w['claims'])]
    source_cards += f'<article class="source-card" id="{s["id"]}"><span class="eyebrow">{s["id"]} / 已讀取正文並整理</span><h2>{e(s["title"])}</h2><p><a href="{e(s["url"], quote=True)}">臺北捷運官方原文</a></p><p class="meta">來源更新：{s["source_updated_on"]} · 本次查核：{s["reviewed_on"]}</p><ul>'+''.join(f'<li>{e(n)}</li>' for n in s['notes'])+f'</ul><p><strong>使用範圍：</strong>{e(s["scope"])}</p><p class="meta">{e(s["notes_type"])}</p><p>整理至：'+ ' · '.join(f'<a href="{wiki_url(w)}">{w["id"]} {e(w["title"])}</a>' for w in used_by)+'</p></article>'
(OUT/'sources.html').write_text(page('來源與匯入摘要', f'<main id="main" class="reading"><span class="eyebrow">INGEST / 5 SOURCES</span><h1>先讀資料，再整理知識。</h1><p class="lead">五篇獨立的官方文字資料。保留來源、日期、摘要與使用範圍，供 Wiki 和簡報追溯。</p><p>匯入方式：AI 閱讀官方網頁正文後，保存為來源筆記，再綜合為 Wiki。未保存官方全文；下列是摘要，不是逐字引文。查核日期不等於官方更新日期。</p>{source_cards}<p><a href="index.html">返回 Wiki</a></p></main>', 'wiki'))

slide_html = ''
trace = []
for i, s in enumerate(lesson, 1):
    selected = [claims[cid][1] for cid in s['claims']]
    used_sources = sorted({sid for c in selected for sid in c['sources']})
    if s['type'] in ('route','end'):
        used_sources = sorted({sid for wid in s['wiki'] for c in wiki_by_id[wid]['claims'] for sid in c['sources']})
    trace.append({'slide':i, 'question':s['query'], 'wiki':s['wiki'], 'claims':s['claims'], 'sources':used_sources, 'method':'AI 選定教學問題與條目；建置程式依 ID 讀取 Wiki 文字，沒有生成新的交通事實'})
    content = ''
    if s['type']=='cover':
        content = '<p class="lead">'+e(s['subtitle'])+'</p><div class="lesson-tags"><span>中文重點</span><span>英文求助句</span><span>情境小練習</span></div><p class="meta">非官方教學 · 官方資料查核 2026-11-21</p>'
    elif s['type']=='route':
        content = '<p class="lead">'+e(s['subtitle'])+'</p><ol class="learning-route">'+''.join(f'<li><a href="{wiki_url(w)}">{e(w["title"])}</a></li>' for w in wiki)+'</ol>'
    elif s['type']=='content':
        content = '<div class="slide-claims">'+''.join(claim_html(c) for c in selected)+'</div>'
        if s.get('phrase'): content += phrase(wiki_by_id[s['phrase']])
    elif s['type']=='quiz':
        content = '''<p class="lead">先說出你的答案，再展開說明。</p><div class="quiz"><details><summary>今天買的一般單程票，明天可以使用嗎？</summary><p>不可以。單程票發售當日有效。<a href="wiki-tickets.html#ticket-validity">查看 Wiki 依據</a></p></details><details><summary>關門警示音響起，朋友還沒上車，可以擋門嗎？</summary><p>不可以。不要強行進出或阻擋車門，等待下一班。<a href="wiki-boarding.html#closing-doors">查看 Wiki 依據</a></p></details><details><summary>還沒通過閘門，是否就一定可以喝水？</summary><p>不是。要看是否已進入黃色禁止飲食線內；需要服藥等特殊情形可洽站務人員協助。<a href="wiki-food-and-help.html#food-line">查看 Wiki 依據</a></p></details></div>'''
    else:
        content = '<p class="lead">當日用票、先下後上、站穩握好、需要時求助。</p><div class="end-links"><a class="button" href="index.html">回到 Wiki 查重點</a><a class="button secondary" href="sources.html">查看官方資料</a></div><p>英文求助句是 AI 編寫的練習內容，非官方翻譯。這份課程不包含即時班次或個別路線規劃。</p>'
    refs = ' · '.join(f'<a href="{wiki_url(wiki_by_id[wid])}">{wid} {e(wiki_by_id[wid]["title"])}</a>' for wid in s['wiki'])
    slide_html += f'<section class="slide {s["type"]}" id="slide-{i}" aria-labelledby="title-{i}"><div class="slide-topline"><span class="eyebrow">{e(s["kicker"])}</span><span class="slide-number">{i:02d} / {len(lesson):02d}</span></div><h2 id="title-{i}">{e(s["title"]).replace(chr(10),"<br>")}</h2>{content}<div class="slide-references">'+('Wiki 依據：'+refs if refs else '教學設計：適合首次搭乘臺北捷運的人')+'</div></section>'

body = f'''<main id="main" class="deck"><h1 class="sr-only">第一次搭臺北捷運：教學簡報</h1><p class="deck-hint">可用上一頁／下一頁，或鍵盤左右方向鍵閱讀。<a href="sources.html">查看教材來源</a></p><div id="slides">{slide_html}</div><div class="deck-controls"><button id="prev" type="button">上一頁</button><label for="slide-select" class="sr-only">選擇投影片</label><select id="slide-select">'''+''.join(f'<option value="{i}">{i+1:02d} · {e(s["kicker"])}</option>' for i,s in enumerate(lesson))+f'''</select><span id="progress" aria-live="polite">1 / {len(lesson)}</span><button id="next" type="button">下一頁</button></div><noscript><p>JavaScript 未開啟，以下已顯示全部投影片，可直接往下閱讀。</p></noscript></main>'''
controls_start = body.index('<div class="deck-controls">')
controls_end = body.index('</div><noscript>', controls_start) + len('</div>')
controls = body[controls_start:controls_end]
body = (body[:controls_start]+body[controls_end:]).replace('<div id="slides">', controls+'<div id="slides">')
(OUT/'slides.html').write_text(page('第一次搭臺北捷運：教學簡報',body,'slides','<script src="slides.js"></script>'))

timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
log = {'built_at':timestamp,'execution_mode':'使用者與 Codex 討論；Codex 讀取網頁並整理來源與 Wiki；Python 依結構化大綱選取 Wiki 條目生成 HTML。不是網站訪客觸發的自動 LLM 工作流。','source_checks':plan['checks'],'slide_queries':trace,'automated_checks':[]}
assert len(sources)>=5 and len({s['url'] for s in sources})>=5
assert all(c['sources'] and set(c['sources'])<=set(source_by_id) for _,c in claims.values())
assert all(set(s['claims']) <= set(claims) for s in lesson)
assert all(set(w['related'])<=set(wiki_by_id) for w in wiki)
assert {sid for t in trace for sid in t['sources']} == set(source_by_id)
log['automated_checks'] = ['5 篇來源網址互不重複','所有 Wiki 事實都有有效來源 ID','簡報引用的條目 ID 均存在於 Wiki','Wiki 相關頁面 ID 均存在','5 篇來源皆用於教學簡報']
(OUT/'run-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
events = ''.join(f'<tr><td>{e(x["node"])}</td><td>{e(x["observed"])}</td><td>{e(x["resolution"])}</td></tr>' for x in plan['checks'])
mapping = ''.join(f'<tr><td>{t["slide"]}</td><td>{e(t["question"])}</td><td>{", ".join(t["wiki"]) or "教學開場"}</td><td>{", ".join(t["sources"]) or "—"}</td></tr>' for t in trace)
flow = '<ol class="flow">'+''.join(f'<li>{e(n)}</li>' for n in plan['workflow_v2'])+'</ol>'
workflow = f'''<main id="main" class="reading wide"><span class="eyebrow">WORKFLOW / 可追溯的製作過程</span><h1>資料怎麼變成一份課？</h1><p class="lead">不直接跳到簡報。先檢查資料，再整理 Wiki，最後把每個教學重點連回依據。</p><section class="note-band"><h2>先討論，後生成</h2><p>延續前幾次作業的通勤與捷運新手主題，將受眾設定為第一次搭臺北捷運的人，採中文重點搭配英文求助句。範圍包括票種、候車、站內安全與求助；不處理即時班次及自動改道。</p><p>主題經對話確認後開始收集資料。語言採建議版本，仍可依使用者回饋調整。</p></section><section><h2>目前的 graph</h2>{flow}<div class="loop-grid"><article><h3>資料讀不到</h3><p>回到「取得資料」，尋找文字版或替換來源。</p></article><article><h3>說法沒有依據</h3><p>回到「查詢 Wiki」，補查原文或刪改敘述，再檢查一次。</p></article><article><h3>畫面操作出錯</h3><p>回到「生成 HTML」，修改後重測受影響的操作。</p></article></div><p>每一篇資料都重複執行正文與來源檢查；每個教學重點都核對 Wiki 依據。只有遇到問題才回到對應節點重做。</p></section><section><h2>一次實際執行的紀錄</h2><p>{e(log['execution_mode'])}</p><p class="meta">HTML 建置時間：{e(timestamp)}</p><div class="table-wrap"><table><thead><tr><th>節點</th><th>實際發現</th><th>處理</th></tr></thead><tbody>{events}</tbody></table></div><h3>建置時已通過</h3><ul>'''+''.join(f'<li>{e(c)}</li>' for c in log['automated_checks'])+'''</ul><p>程式檢查確認結構與引用關係，不能取代對官方原文的事實核對。瀏覽器操作檢查另外保存在驗證紀錄。</p><p><a href="run-log.json">開啟原始執行紀錄 JSON</a> · <a href="validation.html">查看網頁驗證紀錄</a></p></section><section><h2>簡報如何查詢 Wiki？</h2><p>先為每張投影片寫一個教學問題，再指定需要的 Wiki 頁與條目。建置程式依 ID 讀取原有文字，不重新猜測交通規定。</p><div class="table-wrap"><table><thead><tr><th>頁</th><th>教學問題</th><th>Wiki</th><th>來源</th></tr></thead><tbody>'''+mapping+'''</tbody></table></div></section><section class="note-band"><h2>這次實作的反思</h2><p>目前這次執行中，來源正文取得遇到兩次問題：路網圖入口缺少可用文字，禮節頁也要再點入文字版。這是本次有紀錄的主要問題，還不能推論每次執行都一樣。</p><p>原先流程是「取得資料 → 整理 Wiki → 做簡報 → 檢查」。後來把「正文可用性與來源檢查」提前到整理 Wiki 之前，避免把只有連結或圖片的頁面當成已讀完的教材。</p><p>因此調整了 graph：讀不到正文就先回頭找資料，通過後才建立 Wiki。這也讓「至少 5 篇資料」有實際內容可以核對。</p></section><section><h2>AI 協作與理解</h2><p>Codex 協助查找官方資料、整理 Wiki、編寫英文練習句、製作 HTML 與檢查程式。使用者提供主題方向並參與討論。來源摘要不是官方全文，英文句子也不是官方翻譯。</p><p>我需要理解的部分：來源是原始依據；Wiki 是整理後的知識；簡報是按照教學順序選出的重點。loop 是發現問題後回到前一步修正，graph 是把各步驟及返回路徑畫清楚。提交前應親自閱讀並用自己的話說明。</p></section></main>'''
(OUT/'workflow.html').write_text(page('流程與檢查紀錄',workflow,'workflow'))
if not (OUT/'validation.html').exists():
    (OUT/'validation.html').write_text(page('網頁驗證紀錄','<main id="main" class="reading"><h1>網頁驗證紀錄</h1><p>尚未完成瀏覽器檢查，不宣稱已通過。</p><a href="workflow.html">返回製作流程</a></main>','workflow'))
for filename in ['style.css','slides.js','wiki.json','lesson.json','project-plan.json']:
    if ROOT != OUT:
        shutil.copy2(ROOT/filename,OUT/filename)
(OUT/'source-notes.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
print(f'已建立 {len(wiki)} 頁 Wiki、{len(lesson)} 張投影片與來源／流程頁。結構檢查 5 項通過。')
