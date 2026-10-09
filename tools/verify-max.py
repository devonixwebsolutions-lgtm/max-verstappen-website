"""Check driver identity, complete archives and calendar/helmet data bindings."""
from pathlib import Path
from lxml import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
data = json.loads((ROOT / 'content/max-data.json').read_text())
media = json.loads((ROOT / 'content/max-assets.json').read_text())

assert sum(len(s['races']) for s in data['seasons']) == data['driver']['entries'] == 249
assert sum(s['wins'] for s in data['seasons']) == len(data['wins']) == 72
assert sum(s['podiums'] for s in data['seasons']) == 135
assert sum(s['rank'] == 1 for s in data['seasons']) == 4
assert len(data['calendar']) == 23
assert all(media['fixed'].values())

for page in DIST.rglob('*.html'):
    doc = html.parse(str(page))
    text = ' '.join(doc.xpath('//body//text()[not(ancestor::style or ancestor::script)]'))
    assert not re.search(r'\b(?:lando|norris|mclaren|sawaya|padel)\b', text, re.I), page
    assert not doc.xpath('//canvas[@data-rive-file="signature"]|//canvas[@data-rive-ln4]'), page
    assert not doc.xpath('//*[@data-gl="head" or @data-gl="helmet-scroll"]'), page
    for anchor in doc.xpath('//a[@href]'):
        assert not re.search(r'lando|norris|lnfour', anchor.get('href'), re.I), (page, anchor.get('href'))
    for grid in doc.xpath('//*[@data-helmet-grid]'):
        cards = grid.xpath('./*')
        assert len(cards) == len(media['helmets']), page
        for card, helmet in zip(cards, media['helmets']):
            year = card.xpath('.//*[contains(@class,"text-title-small-label") and contains(@class,"date")]')[0].text_content()
            assert year == str(helmet['year']), (page, helmet['name'], year)
            for image in card.xpath('.//img'):
                assert image.get('src').startswith('/assets/max/'), image.get('src')
    for row in doc.xpath('//*[@data-max-round]'):
        event = data['calendar'][int(row.get('data-max-round')) - 1]
        assert json.loads(row.get('data-max-sessions')) == event['sessions']
        assert row.xpath('.//*[@data-cal-list="qual-time"]')[0].text_content() != '—'
        assert not row.xpath('.//*[@data-cal-list[contains(.,"-result") or contains(.,"-pos")]]')

track = html.parse(str(DIST / 'on-track/index.html'))
assert len(track.xpath('//*[@data-win-year]')) == 72
assert len(track.xpath('//*[@data-max-round]')) == 7
assert [n.text_content() for n in track.xpath('//*[@data-car-counter="digit"]')] == ['72', '49', '4', '38']
calendar = html.parse(str(DIST / 'calendar/index.html'))
assert len(calendar.xpath('//*[@data-max-round]')) == 23
assert len(calendar.xpath('//*[contains(concat(" ",@class," ")," mv-result-row ")]')) == 249
assert len(calendar.xpath('//details[@class="mv-season"]')) == 12
assert not calendar.xpath('//*[contains(@class,"calendar-dropdown-item")]')
rounds = calendar.xpath('//*[@data-max-round]')
assert [r.get('data-max-round') for r in rounds] == [str(i) for i in range(1, 24)]
assert sum(r.get('data-max-status') == 'completed' for r in rounds) == 16
for item in calendar.xpath('//*[contains(@class,"calendar-track-info-item")]'):
    label=item.xpath('.//*[contains(@class,"text-descriptor")]')
    if label and label[0].text_content() in ['Standing','Round']:
        value=item.xpath('.//*[contains(@class,"text-on-t-stat-label-major")]')[0].text_content()
        assert value == ('6' if label[0].text_content()=='Standing' else '17')

for resource in media['assets']:
    assert (DIST / resource.lstrip('/')).is_file(), resource
for helmet in media['helmets']:
    assert all((DIST / frame.lstrip('/')).is_file() for frame in helmet['frames'])

print(json.dumps({'driver': 'Max Verstappen', 'seasons': 12, 'grandPrix': 249,
                  'wins': 72, 'podiums': 135, 'helmets': len(media['helmets']),
                  'calendarRounds': 23, 'status': 'passed'}, indent=2))
