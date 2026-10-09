#!/usr/bin/env python3
"""Build Max's pages with the reference layout and verified, locally bundled assets."""
from pathlib import Path
from copy import deepcopy
from lxml import html, etree
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo
import json,re

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
DATA=json.loads((ROOT/'content/max-data.json').read_text())
MEDIA=json.loads((ROOT/'content/max-assets.json').read_text())
FIX=MEDIA['fixed'];HELMETS=MEDIA['helmets'];PHOTOS=MEDIA['photos']
TRACK=[p for p in PHOTOS if not p['offTrack']]
OFF=[p for p in PHOTOS if p['offTrack']]
def cls(node,name):return node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," '+name+' ")]')
def txt(n,t):
    for c in list(n):n.remove(c)
    n.text=str(t)
def inner(n,s):
    for c in list(n):n.remove(c)
    n.text=None
    for c in html.fragments_fromstring(s):
        if isinstance(c,str):n.text=(n.text or '')+c
        else:n.append(c)
def el(s):return html.fragment_fromstring(s)
def remove(n):
    if n.getparent() is not None:n.getparent().remove(n)
def text(n):return ' '.join(n.itertext()).strip()
def section(n):
    while n is not None and n.tag!='section':n=n.getparent()
    return n
def nice(name):
    s=re.sub(r'(?i)max verstappen|verstappen|special|helmet|20\d\d','',name).strip(' -')
    s=re.sub(r'\s+',' ',s).strip()
    return s or 'Season'
def ordinal(v):
    if not str(v).isdigit():return str(v)
    n=int(v);return str(n)+('th' if 10<n%100<14 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th'))
def stats_note():return '<p class="mv-data-note">Career snapshot · 7 October 2026 · <a href="https://www.formula1.com/en/drivers/max-verstappen" target="_blank" rel="noopener">Formula 1</a> / <a href="https://news.verstappen.com/en/about" target="_blank" rel="noopener">Verstappen.com</a></p>'

LOGO='<span class="mv-brand-top">MAX</span><span class="mv-brand-bottom">VERSTAPPEN</span>'
SOCIAL={'tiktok':('Facebook','https://www.facebook.com/MaxVerstappen'),'instagram':('Instagram','https://www.instagram.com/maxverstappen1/'),'youtube':('YouTube','https://www.youtube.com/@MaxVerstappen1'),'twitch':('X / Twitter','https://twitter.com/Max33Verstappen')}
PARTNERS=['partner-red-bull-racing','partner-red-bull','partner-alphatauri','partner-viaplay','partner-heineken']

def all_common(doc,page):
    for title in doc.xpath('//title'):txt(title,{'index.html':'Max Verstappen — Born to Race','on-track/index.html':'On Track — Max Verstappen','off-track/index.html':'Off Track — Max Verstappen','calendar/index.html':'Calendar & Every F1 Result — Max Verstappen'}.get(page,'Max Verstappen — '+('Privacy' if 'privacy' in page else 'Terms')))
    for m in doc.xpath('//meta[@name="description"]|//meta[@property="og:description"]|//meta[@name="twitter:description"]'):
        m.set('content','Max Verstappen. Four world championships. Every Grand Prix result, 72 wins, helmets, racing history and life beyond Formula 1. A private fan project, updated 7 October 2026.')
    for m in doc.xpath('//meta[@property="og:title"]|//meta[@name="twitter:title"]'):m.set('content','Max Verstappen — Born to Race')
    for m in doc.xpath('//meta[@property="og:image"]|//meta[@name="twitter:image"]'):m.set('content',FIX.get('red-bull-hero') or TRACK[0]['src'])
    for n in doc.xpath('//link[@rel="canonical"]|//meta[@property="og:url"]'):remove(n)
    for n in doc.xpath('//link[@rel="icon"]|//link[@rel="apple-touch-icon"]'):n.set('href',FIX['mv-logo'])
    for n in cls(doc,'nav-brand'):
        inner(n,LOGO);n.set('aria-label','Max Verstappen');n.set('class',n.get('class')+' mv-brand')
    for n in cls(doc,'page-ln4-svg'):inner(n,f'<img class="mv-nav-monogram" src="{FIX["mv-logo"]}" alt="Max Verstappen monogram">')
    for n in doc.xpath('//a[@href]'):
        href=n.get('href','');low=href.lower()
        if any(k in low for k in ['instagram.com/','youtube.com/','tiktok.com/','twitch.tv/','landonorris','lando.jpg','mailto:business','maxnorris']):
            if 'mailto:' in low: n.set('href','https://news.verstappen.com/en/contact')
            elif any(k in low for k in SOCIAL):
                key=next(k for k in SOCIAL if k in low);label,url=SOCIAL[key];n.set('href',url)
                leaves=n.xpath('.//*[not(*) and normalize-space(text())]')
                for leaf in leaves:
                    if any(s in text(leaf).lower() for s in ['tiktok','twitch','youtube','instagram']):txt(leaf,label)
                if not leaves:n.text=label
                n.set('title',label)
            else:n.set('href','https://store.verstappen.com/en/')
        if href=='#' and any(k in n.attrib for k in ['data-signup-trigger','data-klaviyo']):n.set('href','https://www.verstappen.com/');n.set('data-taxi-ignore','')
        n.attrib.pop('data-klaviyo',None);n.attrib.pop('data-signup-trigger',None)
        if n.get('href','').startswith('https:'):n.set('target','_blank');n.set('rel','noopener noreferrer')
    # Every old personal logo and Rive wordmark gets real MV artwork or Max typography.
    for canvas in doc.xpath('//canvas[@data-rive-file="signature"]'):
        if cls(canvas.getparent(),'marquee-gl-rive-w') or 'marquee-gl-rive-w' in canvas.getparent().get('class',''):
            remove(canvas);continue
        canvas.getparent().append(el(f'<img class="mv-mark-rive" src="{FIX["mv-logo"]}" alt="Max Verstappen monogram" loading="lazy">'));remove(canvas)
    for canvas in doc.xpath('//canvas[@data-rive-file="phrases"]'):
        board=canvas.get('data-rive-artboard','');label='BORN TO RACE' if 'p1' not in board else 'P1'
        canvas.getparent().append(el(f'<div class="mv-rive-phrase">{label}</div>'));remove(canvas)
    for n in doc.xpath('//*[@data-rive-file="logo"]'):remove(n)
    for n in doc.xpath('//*[@data-rive-placeholder]'):
        if n.tag=='img':n.attrib.pop('data-rive-placeholder',None)
    for n in doc.xpath('//*[contains(@data-wf--c-home-hero-icon--variant,"ln4")]'):n.attrib.pop('data-wf--c-home-hero-icon--variant',None)
    for n in cls(doc,'transition-w'):
        n.append(el('<div class="mv-transition-brand">'+LOGO+'<span class="mv-transition-caption">4× WORLD CHAMPION</span></div>'))
    partner_i=0;photo_i=0;off_i=0
    for img in doc.xpath('//img[@src]'):
        src=img.get('src','');base=src.rsplit('/',1)[-1].lower();c=img.get('class','')
        if not src:continue
        if '/assets/max/' in src:continue
        if any(s in base for s in ['signature','ln-logo','footer-rive','collabs-rive','ln1','blobs_footer']):
            img.set('src',FIX['mv-logo']);img.set('alt','Max Verstappen monogram');img.set('class',c+' mv-monogram')
        elif 'lando-norris-text-mobile' in base:
            img.getparent().append(el('<div class="mv-mobile-wordmark">'+LOGO+'</div>'));remove(img)
        elif 'collab' in base or 'footer-logo' in base:
            key=PARTNERS[partner_i%len(PARTNERS)];partner_i+=1;img.set('src',FIX[key]);img.set('alt',key.replace('partner-','').replace('-',' ').title());img.set('class',c+' mv-partner-logo')
        elif any(s in base for s in ['-flag-','-track-vis','-frame-segment','crossed-flags','icon-crossed']):
            if base.endswith('flag-uk.svg') and 'on-track' in page and '67d847cd' in base:
                flag=next(iter((DIST/'assets/site').glob('*flag-Netherlands*')),None)
                if flag:img.set('src','/assets/site/'+flag.name);img.set('alt','Netherlands flag')
            continue
        elif 'trophy' in c or '-trophy' in base:continue
        elif any(s in base for s in ['helm','helmet']) or 'footer-bg-img' in c:
            img.set('src',HELMETS[0]['frames'][0]);img.set('alt','Max Verstappen '+HELMETS[0]['name'])
        elif 'hp-lando-head' in base:
            img.set('src',FIX.get('portrait-full') or FIX.get('portrait') or TRACK[0]['src']);img.set('alt','Max Verstappen in Oracle Red Bull Racing racewear')
        elif src.endswith(('.svg','.png','.webp','.jpg','.jpeg')):
            choices=OFF if ('off-track' in page and OFF) else TRACK
            photo=choices[(off_i if choices==OFF else photo_i)%len(choices)]
            if choices==OFF:off_i+=1
            else:photo_i+=1
            img.set('src',photo['src']);img.set('alt',photo['caption']+' · Max Verstappen')
    # Replace images in background/data attributes, including hidden video thumbnails.
    for n in doc.xpath('//*[@style or @data-poster-url or @data-video-urls]'):
        if n.get('data-video-urls'):n.attrib.pop('data-video-urls',None)
        if n.get('data-poster-url'):n.set('data-poster-url',TRACK[0]['src'])
        style=n.get('style','')
        if 'url(' in style and '/assets/site/' in style:n.set('style',re.sub(r'url\([^)]*\)','url('+TRACK[0]['src']+')',style))
    for n in doc.xpath('//video|//iframe[contains(@src,"vimeo")]'):remove(n)
    for n in doc.xpath('//script[@type="application/ld+json"]'):remove(n)
    for n in doc.xpath('//*[not(*) and not(self::style or self::script)]'):
        if not n.text:continue
        t=n.text
        if 'Lego' in t or 'Nathan Sawaya' in t:t='GT3 racing brings Max’s competitive instinct to endurance racing and the Nürburgring Nordschleife.'
        if 'Load Norris' in t:t=t.replace('Load Norris','Load Max')
        if t.strip()=='lando at':t='Max at'
        if t.strip().startswith('©'):t='© 2026 · Max Verstappen fan project'
        if page=='on-track/index.html':t=re.sub(r'(?i)Rnd\.\s*18','Rnd.17',t)
        replacements={'last lap lando':'MAX ATTACK','26 y.o':'29 y.o','Bristol, UK':'Hasselt, Belgium','Message from lando':'Born to race','LANDO STORE':'VERSTAPPEN STORE','bringing the fight':'born to race','Always  bringing  the  fight .':'BORN TO RACE. BUILT TO WIN.','Since I was 7 years old and had my first experience with kart racing, I’ve worked tirelessly to make that dream come true.':'From a kart at the age of four to four Formula 1 world championships. Racing has always been part of Max’s life.'}
        replacements.update({'follow lando.jpg':'Explore Verstappen Racing','Max’s schedule':'Max’s schedule','1:2 and 1:5':'1:2 and 1:4','Max\'s upcoming racing schedule, as he takes on the 2025 Formula 1 season.':'Max’s upcoming race weekends in the 2026 Formula 1 season.'})
        for a,b in replacements.items():t=t.replace(a,b)
        n.text=t
    # Fresh styles and delegated interactions survive Taxi's page transitions.
    head=doc.xpath('//head')[0]
    head.append(el('<link rel="stylesheet" href="/assets/runtime/max-theme.css">'))
    head.append(el('<script defer src="/assets/runtime/max-app.js"></script>'))
    head.append(el('<link rel="stylesheet" href="/assets/runtime/max-experience.css">'))
    head.append(el('<script defer src="/assets/runtime/max-experience.js"></script>'))
    head.append(el('<link rel="preload" as="image" href="/assets/max/red-bull-rb22.webp">'))
    doc.xpath('//body')[0].insert(0,el('''<div class="mv-race-loader" data-max-loader role="status" aria-label="Loading Max Verstappen’s website">
      <div class="mv-loader-name" data-loader-name aria-hidden="true"><span>MAX</span><span>VERSTAPPEN</span></div>
      <div class="mv-loader-car" data-loader-car aria-hidden="true"><img src="/assets/max/red-bull-rb22.webp" alt="" fetchpriority="high" width="1800" height="396"></div>
      <div class="mv-loader-footer"><span>ORACLE RED BULL RACING</span><span data-loader-caption>LIGHTS OUT.</span></div>
    </div>'''))
    head.append(el('<meta name="theme-color" content="#07152f">'))
    schema={'@context':'https://schema.org','@type':'Person','name':'Max Verstappen','birthDate':'1997-09-30','birthPlace':'Hasselt, Belgium','nationality':'Dutch','description':'Four-time Formula 1 World Champion','sameAs':[v[1] for v in SOCIAL.values()]}
    script=etree.Element('script',type='application/ld+json');script.text=json.dumps(schema);head.append(script)

def build_helmets(doc):
    for grid in doc.xpath('//*[@data-helmet-grid]'):
        template=deepcopy(grid[0]);inner(grid,'')
        for index,h in enumerate(HELMETS):
            card=deepcopy(template)
            for n in card.xpath('.//*[@id]'):n.attrib.pop('id',None)
            hit=card.xpath('.//*[@data-helmet-item]')[0];hit.set('data-max-helmet',str(index));hit.set('role','button');hit.set('tabindex','0');hit.set('aria-label','View '+h['name']+' · '+str(h['year']))
            for i,n in enumerate(hit.xpath('.//img')):n.set('src',h['frames'][min(i,len(h['frames'])-1)]);n.set('alt','Max Verstappen '+h['name'])
            for n in card.xpath('.//h3'):txt(n,nice(h['name']))
            for n in card.xpath('.//*[contains(@class,"text-title-small-label") and contains(@class,"date")]'):txt(n,h['year'])
            grid.append(card)
        section(grid).set('id','helmets')
        paragraphs=section(grid).xpath('.//p')
        if paragraphs:txt(paragraphs[0],'From Toro Rosso to four world titles: season designs, home-race tributes and special editions. Select a helmet to explore Max’s published photo angles.')
        grid.addprevious(el('<div class="mv-helmet-controls"><label for="helmet-year">Explore the collection</label><select id="helmet-year" data-helmet-filter><option value="all">All years</option>'+''.join(f'<option value="{y}">{y}</option>' for y in sorted({h['year'] for h in HELMETS},reverse=True))+'</select><span>'+str(len(HELMETS))+' designs</span></div>'))

def career(doc):
    for n in cls(doc,'on-t-hero-stats-ui-box1-item'):
        if 'Rnd.' in text(n):
            for leaf in n.xpath('.//*[not(*) and normalize-space(text())="18"]'):txt(leaf,17)
    for canvas in doc.xpath('//canvas[@data-rive-file="circuits" and @data-rive-input-track="baku"]'):
        canvas.getparent().append(el('<img class="mv-previous-circuit" src="/assets/max/sepang-track.png" alt="Sepang International Circuit">'));remove(canvas)
    for n in cls(doc,'on-t-hero-stats-para-w'):
        headings=n.xpath('.//h2|.//p')
        if headings:txt(headings[0],'Dutch racer. Four-time world champion. Max made his Formula 1 debut with Toro Rosso in 2015, won on his Red Bull Racing debut in 2016, and has kept rewriting the record book ever since.')
    for n in cls(doc,'on-t-hero-stats-ui-sec1-row'):
        if 'Azerbaijan' in text(n):
            for leaf in n.xpath('.//*[not(*) and normalize-space(text())]'):
                if 'Azerbaijan' in text(leaf):txt(leaf,'Bahrain / Malaysia')
    for n in doc.xpath('//*[@data-text-format="round"]'):
        if text(n)=='18' and not n.xpath('ancestor::*[@data-cal-item]'):txt(n,17)
    for n in cls(doc,'text-on-t-stat-label-gigantic'):txt(n,135)
    stats=cls(doc,'f1-car-stats-item')
    for n,label,value in zip(stats,['formula 1 wins','pole positions','world titles','fastest laps'],[72,49,4,38]):
        txt(n.xpath('.//h3')[0],label)
        box=cls(n,'f1-car-stats-large-num-w')[0]
        inner(box,f'<div data-car-counter="digit" class="text-on-t-large-number">{value}</div>')
    for n in doc.xpath('//h2[contains(translate(.,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"f1") and not(contains(.,"pre-"))]'):
        if 'career' in text(n).lower():
            spans=n.xpath('.//span')
            if spans:txt(spans[-1],'since 2015')
    for n in cls(doc,'f1-car-stat-past-v2-grid-w'):
        inner(n,'')
        for s in reversed(DATA['seasons']):
            n.append(el('<div class="f1-car-stat-past-v2-grid-item"><div class="f1-car-stat-past-v2-grid-inner"><h3 class="text-on-t-stat-label-reg">'+str(s['year'])+(' *' if s['inProgress'] else '')+'</h3></div><div class="f1-car-stat-past-v2-grid-inner"><div class="text-on-t-stat-label-reg">'+ordinal(s['rank'])+'</div></div><div class="f1-car-stat-past-v2-grid-inner"><div class="text-on-t-stat-label-reg">'+str(s['podiums'])+'</div></div></div>'))
    for n in cls(doc,'f1-car-stats-grid'):n.getparent().append(el(stats_note()))
    # Championship seasons and records extend the existing career section.
    for box in cls(doc,'f1-car-stats-grid'):
        block='<div class="mv-title-cards">'
        for s in DATA['seasons']:
            if s['year'] in [2021,2022,2023,2024]:block+=f'<article class="mv-title-card"><h3>{s["year"]}</h3><p>WORLD CHAMPION<br>{s["wins"]} wins · {s["podiums"]} podiums<br>{s["points"]:g} points</p></article>'
        block+='</div><div class="mv-records">'
        for value,label in [('19','Most Grand Prix wins in a season · 2023'),('10','Consecutive Grand Prix wins · 2023'),('575','Points in one season · 2023'),('18','Youngest winner · 18 years, 228 days')]:block+=f'<div class="mv-record"><strong>{value}</strong><span>{label}</span></div>'
        block+='</div><div class="mv-profile-facts">'
        for value,label in [('249','Grand Prix entered'),('3,632.5','Career points'),('33 → 1 → 3','Race numbers'),('RB22','2026 race car')]:block+=f'<div><span class="text-eyebrow">{label}</span><strong>{value}</strong></div>'
        block+='</div>'
        box.getparent().append(el('<div style="grid-column:1/-1">'+block+'</div>'))
    # The reference's highlights become a complete race-win archive.
    for h in doc.xpath('//h2'):
        if 'result' in text(h).lower() and 'highlight' in text(h).lower():
            sec=section(h);txt(h,'Every Formula 1 win');sec.set('id','wins')
            paras=sec.xpath('.//p')
            if paras:txt(paras[0],'All 72 Grand Prix victories. From Barcelona in 2016 to Bahrain in Malaysia in 2026, explore every win by season.')
            lists=sec.xpath('.//*[@data-stat-list]')
            if lists:
                target=lists[0];inner(target,'');target.set('data-wins-list','')
                for w in reversed(DATA['wins']):
                    target.append(el(f'<div class="f1-highlight-grid is-highlights mv-win-row" data-win-year="{w["year"]}"><div class="f1-highlight-grid-item"><div class="text-on-t-stat-label-major">{w["number"]:02}</div></div><div class="f1-highlight-grid-item"><div class="text-on-t-stat-label-major">{escape(w["grandPrix"])}</div></div><div class="f1-highlight-grid-item"><div class="text-on-t-stat-label-major">{w["date"][:-5]}</div><div class="text-eyebrow">{w["year"]}</div></div><div class="f1-highlight-grid-item"><div class="text-on-t-stat-label-major c-lime-off">1st</div></div><div class="f1-highlight-grid-item"><div class="text-on-t-stat-label-reg">{w["points"]:g} pts</div></div><div class="f1-highlight-grid-line"></div></div>'))
                target.addprevious(el('<div class="mv-archive-controls"><label for="wins-year">Wins by season</label><select id="wins-year" data-wins-filter><option value="all">All 72 wins</option>'+''.join(f'<option value="{s["year"]}">{s["year"]} · {s["wins"]} wins</option>' for s in reversed(DATA['seasons']) if s['wins'])+'</select><span data-wins-count>72 wins</span></div>'))
            for n in sec.xpath('.//*[contains(@class,"f1-highlight-grid") and contains(@class,"top")]'):
                labs=n.xpath('.//*[not(*) and normalize-space(text())]')
                for q,t in zip(labs,['Win','Grand Prix','When','Finish','Points']):txt(q,t)
            for n in cls(sec,'f1-highlight-mouse-over-w'):remove(n)
    for h in doc.xpath('//h2'):
        if 'pre-f1' in text(h).lower():
            sec=section(h);spans=h.xpath('.//span');txt(spans[-1],'2005–2014')
            items=cls(sec,'pre-f1-car-stats-item')
            entries=[('European Formula 3 · 3rd place / 10 wins',2014),('CIK-FIA KZ World Champion',2013),('European KZ Champion',2013),('European KF Champion',2013),('WSK Euro Series KZ1 Champion',2013),('WSK Master Series KZ2 Champion',2013),('WSK Euro Series KF3 Champion',2010),('Belgian Minimax Champion',2005)]
            for n,(label,year) in zip(items,entries):
                for q in cls(n,'text-on-t-stat-label-sm'):txt(q,label)
                for q in cls(n,'text-descriptor'):txt(q,year)
            paras=sec.xpath('.//p')
            if paras:txt(paras[0],'Max began karting at four and first raced competitively in 2005. World and European karting titles followed in 2013. In 2014 he won ten European Formula 3 races, then stepped directly into Formula 1 in 2015.')
    for n in doc.xpath('//*[@data-gl="helmet-scroll"]'):
        n.attrib.pop('data-gl',None);n.set('class',n.get('class','')+' mv-floating-helmet')
        inner(n,f'<img src="{HELMETS[0]["frames"][0]}" alt="Max Verstappen 2026 season helmet">')

def calendar(doc,page):
    # Keep the original circuit viewer and schedule row structure, with fresh data.
    for item in cls(doc,'calendar-track-info-item'):
        label=item.xpath('.//*[contains(@class,"text-descriptor")]')
        if label and text(label[0]) in ['Standing','Round']:
            for value in cls(item,'text-on-t-stat-label-major'):txt(value,6 if text(label[0])=='Standing' else 17)
    rows=doc.xpath('//*[@data-cal-item]')
    originals={}
    source=html.document_fromstring((ROOT/'reference/adapt-base/calendar/index.html').read_text())
    for row in source.xpath('//*[@data-cal-item]'):
        ids=row.xpath('.//*[@data-cal-list="circuit-id"]');rid=text(ids[0]) if ids else ''
        if rid:originals[rid]=row
    lookup=['melbourne','shanghai','suzuka','miami','montreal','monaco','barcelona','speilberg','silverstone','spa-francorchamps','mogyorod','zandvoort','monza','madrid','baku','sepang','singapore','austin','mexico-city','sao-paulo','las-vegas','lusail','yas-marina']
    first_competed={'baku':2016,'zandvoort':2021,'miami':2022,'las-vegas':2023,'lusail':2021,'madrid':2026}
    # On Track shows upcoming races; Calendar shows the whole season.
    chosen=DATA['calendar'] if page=='calendar/index.html' else DATA['calendar'][16:]
    parents=list(dict.fromkeys(row.getparent() for row in rows))
    if not parents:return
    template=deepcopy(rows[-1])
    for row in rows:remove(row)
    for event in chosen:
        rid=lookup[event['round']-1];old=originals.get(rid,originals.get('sakhir',template))
        row=deepcopy(old);row.set('data-max-round',str(event['round']));row.set('tabindex','0');row.set('role','button');row.set('aria-label','View '+event['name'])
        for n in row.xpath('.//*[@id]'):n.attrib.pop('id',None)
        name=re.sub(r' Grand Prix(?: in Malaysia)? 2026$','',event['name'])
        if event['round']==16:name='Bahrain / Malaysia'
        dates=[datetime.strptime(s['date'],'%d %b %Y') for s in event['sessions']]
        first,last=min(dates),max(dates)
        dateRange=f'{first.day:02}–{last.day:02}'
        race=next(s for s in event['sessions'] if s['name']=='Race')
        dt=datetime.strptime(race['date']+' '+race['time'],'%d %b %Y %H:%M').replace(tzinfo=ZoneInfo('Europe/Amsterdam')).astimezone(ZoneInfo('UTC'))
        previous=event['round']<=16
        target=parents[0] if previous or len(parents)==1 else parents[1]
        result=DATA['seasons'][-1]['races'][event['round']-1] if previous else None
        row.set('data-max-status','completed' if previous else 'upcoming')
        row.set('class','f1-highlight-grid '+('is-previous' if previous else 'is-schedule')+' w-dyn-item')
        # Preserve track geometry and flags; remove every inherited personal result.
        for n in row.xpath('.//*[@data-cal-list]'):
            key=n.get('data-cal-list','')
            if key.endswith(('-result','-pos')):remove(n)
            elif key.endswith(('-date','-time')) and key!='first-competed-date':txt(n,'—')
        for n in row.xpath('.//*[contains(@class,"text-body-sm-mona") and not(@data-cal-list) and not(*)]'):
            if 'Grand Prix' in text(n):txt(n,event['name'])
        for n in row.xpath('.//*[@data-text-format="round"]'):txt(n,event['round'])
        cells=[n for n in row if 'f1-highlight-grid-item' in n.get('class','')]
        if len(cells)>1:
            q=cells[1].xpath('.//*[contains(@class,"text-on-t-stat-label-major")]')
            if q:txt(q[0],name)
        if len(cells)>2:inner(cells[2],f'<div class="text-on-t-stat-label-major">{dateRange}</div><div class="text-eyebrow">{last.strftime("%b")}</div>')
        if result:
            if len(cells)>3:inner(cells[3],f'<div class="text-on-t-stat-label-major">{ordinal(result["position"])}</div>')
            if len(cells)>4:inner(cells[4],f'<div class="text-on-t-stat-label-reg">{result["points"]:g} pts</div>')
        vals={'circuit-id':rid,'circuit-name':name,'date-actual':dt.strftime('%d/%m/%Y %H:%M'),'date-from-to-num':dateRange,'date-from-to-month':last.strftime('%b'),'first-competed-date':first_competed.get(rid,2015),'circuit-about':f'<p>{name} · Round {event["round"]} of the 2026 Formula 1 season. '+('Max finished '+ordinal(result['position'])+'.' if result else 'Race '+dt.strftime('%d %B at %H:%M UTC')+'.')+'</p>'}
        if rid=='sepang':
            vals.update({'circuit-lap-amount':56,'circuit-lap-length':5.543,'circuit-distance':310.408})
            flag=row.xpath('.//*[@data-cal-list="circuit-flag"]')[0];flag.set('src','/assets/max/flag-malaysia.svg');flag.set('alt','Malaysia')
            row.set('data-max-track-map','/assets/max/sepang-track.png')
        for key,val in vals.items():
            for n in row.xpath('.//*[@data-cal-list="'+key+'"]'):
                if key=='circuit-about':inner(n,val)
                else:txt(n,val)
        sessions={'Practice 1':'prac1','Practice 2':'prac2','Practice 3':'prac3','Qualifying':'qual','Race':'race','Sprintrace':'prac3','Sprint Qualifying':'prac2'}
        for s in event['sessions']:
            when=datetime.strptime(s['date']+' '+s['time'],'%d %b %Y %H:%M').replace(tzinfo=ZoneInfo('Europe/Amsterdam')).astimezone(ZoneInfo('UTC'))
            key=sessions[s['name']]
            for attr,val in [(key+'-date',when.strftime('%-d %b')),(key+'-time',when.strftime('%H:%M'))]:
                for n in row.xpath('.//*[@data-cal-list="'+attr+'"]'):txt(n,val)
        sprint=any('Sprint' in s['name'] or 'Sprintrace'==s['name'] for s in event['sessions'])
        for n in row.xpath('.//*[@data-cal-sprint]'):remove(n)
        marker=etree.Element('span',{'data-cal-sprint':'true','hidden':''});marker.set('class','' if sprint else 'w-condition-invisible');row.append(marker)
        # Store a complete, accessible session schedule on each row.
        row.set('data-max-sessions',json.dumps(event['sessions'],ensure_ascii=False));row.set('data-max-event-name',event['name'])
        for n in row.xpath('.//*[@data-stat-hover-img]'):n.set('src',TRACK[0]['src'])
        target.append(row)
    for n in doc.xpath('//*[@data-countdown-date-target]'):txt(n,'11/10/2026 12:00')
    singapore=doc.xpath('//*[@data-max-round="17"]')[0]
    for n in doc.xpath('//*[@data-cal-target]'):
        key=n.get('data-cal-target');matches=singapore.xpath('.//*[@data-cal-list="'+key+'"]')
        if key=='past-reveal':remove(n)
        elif key=='past-hide':txt(n,'* UTC · weekend points include sprints')
        elif key=='circuit-about':inner(n,matches[0].text_content())
        elif key=='circuit-flag' and matches:n.set('src',matches[0].get('src'));n.set('alt','Singapore')
        elif key!='transition-item' and matches:txt(n,text(matches[0]))
    for n in doc.xpath('//*[contains(@class,"f1-highlight-grid") and contains(@class,"top")]'):
        for leaf in n.xpath('.//*[not(*) and normalize-space(text())]'):
            if text(leaf)=='fastest lap':txt(leaf,'Points')
    # Entire old history panels are replaced: every season and every race is Max's.
    for h in doc.xpath('//h2'):
        if 'All Results' in text(h):
            sec=section(h);sec.set('id','results');container=sec[0]
            for extra in list(sec)[1:]:remove(extra)
            inner(container,'<div class="spacer _10rem"></div><div class="title-layout grid-main"><div class="title-headline-w"><h2 class="text-title-lg-mona split-flex">Formula 1 <span class="text-title-lg-brier c-grey-on-track">Every result</span></h2></div><div class="title-para-w"><p class="text-body-reg-mona">Twelve seasons. Every Grand Prix. Explore Max’s complete Formula 1 career from 2015 to today.</p></div></div>')
            for s in reversed(DATA['seasons']):
                detail=el(f'<details class="mv-season" {"open" if s["year"]==2026 else ""}><summary><span class="mv-season-year">{s["year"]}</span><span>{ordinal(s["rank"])} '+('in progress' if s['inProgress'] else ('· WORLD CHAMPION' if s['rank']==1 else 'in championship'))+f'</span><span>{s["points"]:g} points</span><span>{s["wins"]} wins · {s["podiums"]} podiums</span><span class="mv-season-toggle">+</span></summary><div class="mv-season-body"><div class="f1-highlight-grid mv-results-head"><span>Round</span><span>Grand Prix</span><span>When</span><span>Finish</span><span>Points</span></div></div></details>')
                body=cls(detail,'mv-season-body')[0]
                for r in s['races']:
                    body.append(el(f'<div class="f1-highlight-grid mv-result-row {"mv-winner" if r["position"]=="1" else ""}"><div class="f1-highlight-grid-item">{r["round"]:02}</div><div class="f1-highlight-grid-item"><span class="text-on-t-stat-label-major">{escape(r["grandPrix"])}</span><span class="mv-result-team">{escape(r["team"])}</span></div><div class="f1-highlight-grid-item">{r["date"][:-5]}</div><div class="f1-highlight-grid-item">{ordinal(r["position"])}</div><div class="f1-highlight-grid-item">{r["points"]:g}</div></div>'))
                link=f'https://www.formula1.com/en/results/{s["year"]}/drivers/MAXVER01/max-verstappen'
                body.append(el(f'<p class="mv-data-note">Weekend points include sprint points where applicable. <a href="{link}" target="_blank" rel="noopener">Official {s["year"]} results ↗</a></p>'))
                container.append(detail)
            container.append(el(stats_note()));container.append(el('<div class="spacer _10rem"></div>'))

def home(doc):
    for n in doc.xpath('//*[@data-gl="head"]'):
        n.attrib.pop('data-gl',None);n.set('class',n.get('class','')+' mv-hero-portrait')
        portrait=FIX.get('portrait') or FIX.get('portrait-full') or TRACK[0]['src']
        inner(n,f'<div class="mv-hero-name"><span>MAX</span><span>VERSTAPPEN</span></div><div class="mv-hero-photo-w"><img class="mv-hero-photo" src="{portrait}" alt="Max Verstappen · four-time Formula 1 world champion" fetchpriority="high"></div><span class="mv-hero-champions">2021 · 2022 · 2023 · 2024</span><span class="mv-hero-number">03</span><span class="mv-hero-tag">FOUR WORLD TITLES. ONE RACING INSTINCT.</span>')
    for n in cls(doc,'home-hero-touch-controls-w'):n.set('class',n.get('class')+' mv-portrait-controls')
    for n in cls(doc,'impact-on-home'):
        inner(n,'Born to <strong>race</strong>.<br>Built to <strong>win</strong>.<br>Four world titles.<br>Still chasing <strong>more</strong>.')
    for n in cls(doc,'is-home'):
        if 'impact-content-w' in n.get('class',''):
            for p in cls(n,'text-impact-lg-mona'):inner(p,'Born to <span class="font-brier">race</span>.<br>Built to <span class="font-brier">win</span>.<br>Four world titles.<br>Still chasing <span class="font-brier">more</span>.')
    for h in doc.xpath('//h2'):
        if 'World Drivers' in text(h):txt(h,'Four-time World Champion')
    for p in cls(doc,'exe-cta-para'):
        txt(p,'Explore Max’s official collection: racewear, championship memorabilia and detailed helmet replicas.')
    for n in cls(doc,'is-lando-exe'):
        for p in n.xpath('.//p'):txt(p,'The official Verstappen collection. Teamwear, personal apparel, scale models and the helmets behind the victories.')
    for n in cls(doc,'home-hero-next-race-row'):
        if 'is-2' in n.get('class',''):n.set('data-max-helmet','0');n.set('role','button');n.set('tabindex','0');n.set('aria-label','View Max’s 2026 helmet')

TIMELINE=[('1997','Born into racing','Born on 30 September in Hasselt, Belgium, to racers Jos Verstappen and Sophie Kumpen. Max competes under the Dutch flag.'),('2001–2005','The first kart','He began karting at four and entered his first competitive season in 2005. Karting became his racing education.'),('2013','World and European karting titles','Max won the CIK-FIA KZ World Championship and both European KZ and KF titles, alongside WSK titles.'),('2014','Ten Formula 3 wins','His first season in single-seaters brought ten wins and third place in the FIA European Formula 3 Championship.'),('2015','Formula 1 at seventeen','Max debuted with Scuderia Toro Rosso in Australia. At 17 years and 166 days, he became the youngest Formula 1 driver.'),('2016','The youngest Grand Prix winner','Promoted to Red Bull Racing for the Spanish Grand Prix, Max won immediately at 18 years and 228 days.'),('2017–2020','Building the challenge','Nine more Grand Prix wins over four seasons. Third in the championship in 2019 and 2020.'),('2021','World champion','Ten Grand Prix victories and 395.5 points delivered Max’s first World Drivers’ Championship.'),('2022','Back-to-back','Fifteen wins and 454 points secured a second world title. Max raced with the champion’s number 1.'),('2023','A record season','Nineteen victories in 22 races, ten consecutive wins, 21 podiums and 575 points. A third straight world title.'),('2024','Four in a row','Nine wins and 437 points. A fourth title secured in Las Vegas, with a remarkable wet-weather victory from 17th in São Paulo.'),('2025','Fighting to the final race','Eight wins, 15 podiums and 421 points. Second in the championship, two points from the title.'),('2026','A new era, number 3','Oracle Red Bull Racing’s RB22 and a new race number. 72 career Grand Prix wins as of 7 October, with Bahrain in Malaysia the latest.')]

def biography():
    content='<section class="s mv-biography" id="story"><div class="c"><div class="spacer _10rem"></div><div class="title-layout grid-main"><div class="title-headline-w"><h2 class="text-title-lg-mona">Born to race.<br><span class="text-title-lg-brier c-grey-on-track">The complete story.</span></h2></div><div class="title-para-w"><p class="text-body-reg-mona">Max Emilian Verstappen. Dutch. Born 30 September 1997. Four-time Formula 1 World Champion with Oracle Red Bull Racing.</p></div></div><div class="mv-profile-facts">'
    facts=[('Born','30.09.1997'),('Birthplace','Hasselt, Belgium'),('Nationality','Dutch'),('Height / weight','181 cm / 74 kg'),('Race number','3'),('Formula 1 debut','Australia · 2015'),('Red Bull Racing','Since 2016'),('World titles','2021 / 22 / 23 / 24')]
    content+=''.join(f'<div><span class="text-eyebrow">{a}</span><strong>{b}</strong></div>' for a,b in facts)+'</div><div class="mv-timeline">'
    content+=''.join(f'<article class="mv-timeline-row"><span class="mv-timeline-year">{y}</span><div><h3>{a}</h3><p>{b}</p></div></article>' for y,a,b in TIMELINE)
    content+='</div>'+stats_note()+'<div class="spacer _10rem"></div></div></section>'
    return el(content)

def offtrack(doc):
    for n in cls(doc,'on-t-hero-stats-para-w'):
        headings=n.xpath('.//h2|.//p')
        if headings:txt(headings[0],'The racer beyond Formula 1. From endurance sim racing to Verstappen Racing, Max’s life away from the Grand Prix paddock still revolves around the love of competition.')
    for p in doc.xpath('//p'):
        if 'Hilton' in text(p):txt(p,'Discover Max’s official projects, sim racing, personal collection and life beyond Formula 1.')
    titles=doc.xpath('//h2|//h3')
    replace=[('padel tennis','Verstappen Sim Racing'),('photography & film','Verstappen Racing'),('lego: art oF the brick','GT3 & endurance racing'),('Mastering the Green','Beyond the paddock')]
    for h in titles:
        for old,new in replace:
            if old.lower() in text(h).lower():txt(h,new)
    for p in doc.xpath('//p'):
        t=text(p)
        if 'padel' in t:inner(p,'Max races in the virtual world with Verstappen Sim Racing. Formerly Team Redline, the team adopted its new name in March 2026. <a href="https://news.verstappen.com/en/article/6112/" target="_blank" rel="noopener">Explore the team ↗</a>')
        if 'Nathan' in t or 'Lego' in t:inner(p,'On 27 September 2025, Max won his GT3 race debut at the Nürburgring Nordschleife alongside Chris Lulham, in an Emil Frey Racing Ferrari 296 GT3. <a href="https://news.verstappen.com/en/article/5958/" target="_blank" rel="noopener">Discover the race ↗</a>')
    for n in doc.xpath('//a[contains(.,"Explore Verstappen Racing")]'):n.set('href','https://racing.verstappen.com/')
    for n in doc.xpath('//*[not(*) and contains(text(),"nathan sawaya")]'):txt(n,'The next racing challenge')
    for n in doc.xpath('//*[not(*) and contains(text(),"2006–current")]'):txt(n,'Racing, always')
    for n in doc.xpath('//*[not(*) and not(self::script or self::style)]'):
        if 'padel' in text(n).lower():inner(n,'Max competes in virtual endurance racing with Verstappen Sim Racing, the team previously known as Team Redline. It adopted its new name in March 2026. <a href="https://news.verstappen.com/en/article/6112/" target="_blank" rel="noopener">Explore the team ↗</a>')
    footer=cls(doc,'is-callout-socials')[0];footer.addprevious(biography())

def captions(doc,page):
    for n in cls(doc,'horizontal-item-text'):
        if 'It doesn’t matter' in text(n):inner(n,'A racer’s <span class="span-green-off-white-1">instinct</span>.<br>Every lap. Every <span class="span-green-off-white-1">challenge</span>.')
    for sec in cls(doc,'is-horizontal-track'):
        imgs=cls(sec,'is-horizontal-scroll');choices=OFF if page=='off-track/index.html' else TRACK
        for i,img in enumerate(imgs):
            p=choices[i%len(choices)];img.set('src',p['src']);img.set('alt',p['caption']+' · Max Verstappen')
            par=img.getparent()
            for _ in range(4):
                caption=par.xpath('.//*[contains(@class,"text-eyebrow") and not(contains(@class,"line"))]')
                if caption:
                    for n in caption[:2]:
                        if re.search(r'20\d\d|qatar|battersea|miami|monaco|gala|barcelona|austria|singapore|london|australia|US',text(n),re.I):txt(n,'Max vs 100 · 2026' if p['offTrack'] else p['caption'].replace('Formula 1 GP ','').replace('Formula 1 ','')+' · 2026')
                    break
                if par.getparent() is None:break
                par=par.getparent()
    for n in doc.xpath('//*[not(*) and not(self::style or self::script)]'):
        if n.text and 'It doesn’t matter' in n.text:n.text='A racer’s instinct. Every lap. Every challenge.'
    for n in doc.xpath('//*[contains(@class,"text-impact")]'):
        if 'It doesn’t matter' in text(n):inner(n,'A racer’s <strong>instinct</strong>.<br>Every lap. Every <strong>challenge</strong>.')

def legal(doc,page):
    node=doc.xpath('//*[@data-page]')[0]
    footer=deepcopy(next(n for n in cls(node,'is-footer') if n.tag=='section'));inner(node,'')
    privacy='privacy' in page
    copy='<h1 class="text-title-lg-mona">'+('Privacy Policy' if privacy else 'Terms of Use')+'</h1>'
    if privacy:copy+='<p>This is a private fan project. It does not collect newsletter submissions, process purchases, or add advertising analytics.</p><p>Access and ordinary hosting logs are managed by the hosting platform. Official store and social links open external websites, which apply their own privacy policies.</p>'
    else:copy+='<p>This independent fan project recreates the reference website’s visual layout for a Max Verstappen theme. It is not an official website of Max Verstappen, Red Bull Racing or Formula 1.</p><p>Statistics reflect the cited official sources as of 7 October 2026. Photography and logos belong to their respective owners. Store links lead to the official external store; this website does not sell products.</p>'
    node.append(el('<section class="s mv-legal"><div class="c">'+copy+'<a class="mv-plain-link" href="/">Back to home ↗</a></div></section>'));node.append(footer)

for path in sorted((ROOT/'reference/adapt-base').rglob('*.html')):
    page=str(path.relative_to(ROOT/'reference/adapt-base'));doc=html.document_fromstring(path.read_text())
    all_common(doc,page)
    if 'legal/' in page:legal(doc,page)
    else:
        build_helmets(doc);captions(doc,page)
        if page=='index.html':home(doc)
        if page=='on-track/index.html':career(doc);calendar(doc,page)
        if page=='calendar/index.html':calendar(doc,page)
        if page=='off-track/index.html':offtrack(doc)
    # Footer data provenance stays subtle; every route is independently understandable.
    for footer in [n for n in cls(doc,'is-footer') if n.tag=='section']:
        for h in footer.xpath('.//h2'):txt(h,'Born to race. Built to win.')
        for n in footer.xpath('.//*[not(*) and contains(text(),"All rights reserved")]'):txt(n,'© 2026 · Max Verstappen fan project')
        for n in footer.xpath('.//*[contains(@class,"copyright")]'):
            if '©' in text(n):txt(n,'© 2026 · Max Verstappen fan project')
        for n in footer.xpath('.//*[contains(@class,"text-eyebrow")]'):
            if text(n).startswith('©'):txt(n,'© 2026 · Max Verstappen fan project')
        footer[0].append(el('<div class="mv-footer-note">Independent fan project · Stats updated 7 October 2026</div>'))
    # Embedded data is inert JSON. The same gallery data works after client navigation.
    data=etree.Element('script',id='max-gallery-data',type='application/json');data.text=json.dumps(HELMETS,ensure_ascii=False).replace('</','<\\/');doc.xpath('//body')[0].append(data)
    output='<!DOCTYPE html>\n'+html.tostring(doc,encoding='unicode',method='html')
    output=re.sub(r'landonorris\.com','verstappen.com',output,flags=re.I)
    target=DIST/page;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(output)
print('Built 6 Max Verstappen pages,',len(HELMETS),'helmet designs, 249 race results and 72 wins.')
