import base64, json, hashlib, os, re, sys, time, zipfile, io
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright

SITE = 'http://localhost:8765/'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out')
FILES = os.path.join(OUT, 'files')
os.makedirs(OUT, exist_ok=True)
repo = {}       # path -> bytes  (simuliertes Repository)
log = []
def sha(b): return hashlib.sha1(b).hexdigest()

def gh_handler(route, request):
    u = urlparse(request.url)
    m = re.match(r'^/repos/[^/]+/[^/]+(/contents/(.*))?$', u.path)
    if not m: return route.fulfill(status=404, body='{}')
    if not m.group(1):
        size = sum(len(v) for v in repo.values()) // 1024
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'permissions': {'push': True}, 'size': size}))
    path = unquote(m.group(2))
    meth = request.method
    if meth == 'GET':
        if path not in repo: return route.fulfill(status=404, content_type='application/json', body='{"message":"Not Found"}')
        b = repo[path]
        if 'raw' in (request.headers.get('accept') or ''):
            return route.fulfill(status=200, body=b)
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'sha': sha(b), 'content': base64.b64encode(b).decode()}))
    body = json.loads(request.post_data or '{}')
    if meth == 'PUT':
        if path in repo and body.get('sha') != sha(repo[path]):
            return route.fulfill(status=409, content_type='application/json', body='{"message":"sha does not match"}')
        repo[path] = base64.b64decode(body['content'])
        log.append(('PUT', path))
        return route.fulfill(status=200, content_type='application/json', body=json.dumps({'content': {'sha': sha(repo[path])}}))
    if meth == 'DELETE':
        repo.pop(path, None); log.append(('DEL', path))
        return route.fulfill(status=200, content_type='application/json', body='{}')
    route.fulfill(status=405, body='{}')

def site_handler(route, request):
    p = unquote(urlparse(request.url).path).lstrip('/') or 'index.html'
    if p in repo: return route.fulfill(status=200, body=repo[p])
    f = os.path.join(ROOT, p)
    if os.path.isfile(f) and not p.startswith(('data/', 'material/')):
        ct = 'text/html' if p.endswith('.html') else ('text/javascript' if p.endswith('.js') else None)
        return route.fulfill(status=200, body=open(f, 'rb').read(), **({'content_type': ct} if ct else {}))
    route.fulfill(status=404, body='nf')

# Hilfsfunktionen im Browser (eigene Krypto, um ALTE Daten einzuspielen)
JS_HELPERS = r'''
window.T = {
  b64: b => { let s=''; for(const x of b) s+=String.fromCharCode(x); return btoa(s); },
  unb64: s => Uint8Array.from(atob(s), c => c.charCodeAt(0)),
  async kek(secret, salt, iter){ const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), 'PBKDF2', false, ['deriveBits']);
    return new Uint8Array(await crypto.subtle.deriveBits({name:'PBKDF2', hash:'SHA-256', salt:T.unb64(salt), iterations:iter}, base, 256)); },
  async key(raw){ return crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt','decrypt']); },
  async seal(k, bytes){ const iv = crypto.getRandomValues(new Uint8Array(12)); const ct = new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM', iv}, k, bytes));
    const o = new Uint8Array(16+ct.length); o.set([85,77,67,49],0); o.set(iv,4); o.set(ct,16); return o; },
  async unseal(k, b){ return new Uint8Array(await crypto.subtle.decrypt({name:'AES-GCM', iv:b.subarray(4,16)}, k, b.subarray(16))); },
  async keys(code, pw){
    const z = await (await fetch('data/zugang.json?t='+Date.now())).json();
    const kb = await T.key(await T.kek(code, z.basis.salt, z.iter)); const dekB = await T.unseal(kb, T.unb64(z.basis.dek));
    const kp = await T.key(await T.kek(pw, z.pruefung.salt, z.iter)); const dekP = await T.unseal(kp, T.unb64(z.pruefung.dek));
    return { B: await T.key(dekB), P: await T.key(dekP) };
  },
  async put(path, bytes){ let sha=null; const g = await fetch('https://api.github.com/repos/o/r/contents/'+path);
    if(g.ok) sha = (await g.json()).sha;
    const r = await fetch('https://api.github.com/repos/o/r/contents/'+path, {method:'PUT', body:JSON.stringify({message:'t', content:T.b64(bytes), sha})}); return r.ok; },
  async getData(K){ const b = new Uint8Array(await (await fetch('data/inhalt.enc?t='+Date.now())).arrayBuffer()); return JSON.parse(new TextDecoder().decode(await T.unseal(K.B, b))); },
  async putData(K, d){ return T.put('data/inhalt.enc', await T.seal(K.B, new TextEncoder().encode(JSON.stringify(d)))); },
  async file(K, path, text, schutz){ const enc = await T.seal(schutz==='pruefung'?K.P:K.B, new TextEncoder().encode(text)); await T.put(path, enc); return {pfad:path, name:path.split('/').pop().replace('.enc',''), ext:path.split('.').slice(-2)[0], mb:0.01, schutz}; }
};
'''

# kleine Testdateien
PDF = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'
os.makedirs(FILES + '', exist_ok=True)
open(FILES + '/AB Spiegel-Parcours.pdf', 'wb').write(PDF)
# Ersatz für eine Schritt-Seite wie „Camera obscura“ (echtes Material gehört nicht unverschlüsselt ins Repository)
open(FILES + '/camera-obscura.html', 'w', encoding='utf-8').write("""<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Camera obscura</title>
<style>.app-only{display:none}.in-app .bar .app-only{display:inline-flex}</style></head><body>
<header><div class="bar"><a class="home app-only" href="#zurueck">‹ Übersicht</a><b>Physik 8</b></div>
<nav><a class="step" href="#auftrag" data-page="auftrag">1</a> <a class="step" href="#bauen" data-page="bauen">2</a></nav></header>
<article id="auftrag"><h1>Auftrag</h1></article><article id="bauen" hidden><h1>Bauen</h1></article>
<script>if(window.Plattform)document.documentElement.classList.add('in-app');
function show(n){if(n==='zurueck'||n==='weiter')return;if(['auftrag','bauen'].indexOf(n)<0)n='auftrag';
['auftrag','bauen'].forEach(function(p){document.getElementById(p).hidden=p!==n;});}
addEventListener('hashchange',function(){show(location.hash.slice(1));});show(location.hash.slice(1));</script></body></html>""")

open(FILES + '/AB Spiegel-Parcours.docx', 'wb').write(b'PK fake docx')
open(FILES + '/Klausur Optik.pdf', 'wb').write(PDF)
open(FILES + '/Film.mp4', 'wb').write(b'0' * 100)
# großes PNG für Verkleinerung
import struct, zlib
def png(w, h):
    raw = b''.join(b'\x00' + os.urandom(w * 3) for _ in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 1)) + chunk(b'IEND', b'')
open(FILES + '/Conceptmap.png', 'wb').write(png(2600, 1400))

results = []
def check(name, cond, info=''):
    results.append((name, bool(cond), info)); print(('OK   ' if cond else 'FAIL ') + name + ('  ' + str(info) if info and not cond else ''))

with sync_playwright() as p:
    chrome = os.environ.get('CHROME') or ('/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None)
    br = p.chromium.launch(executable_path=chrome, args=['--no-sandbox']) if chrome else p.chromium.launch(args=['--no-sandbox'])
    ctx = br.new_context(service_workers='block', viewport={'width': 1024, 'height': 1300}, accept_downloads=True)
    ctx.route('https://api.github.com/**', gh_handler)
    ctx.route(SITE + '**', site_handler)
    page = ctx.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    dialogs = []
    def on_dialog(d):
        dialogs.append(d.message)
        # „auch aus dem Speicher löschen?“ -> ja; sonst bestätigen
        d.accept()
    page.on('dialog', on_dialog)
    def wait_saved():
        page.wait_for_selector('#toast.on', timeout=20000); page.wait_for_selector('#busy:not(.on)', state='attached', timeout=60000); time.sleep(0.3)
        page.evaluate("document.querySelector('#toast').classList.remove('on')")
    def shot(n): page.screenshot(path=f'{OUT}/{n}.png', full_page=True)

    # ---- Ersteinrichtung ----
    page.goto(SITE)
    page.evaluate("localStorage.setItem('um-github', JSON.stringify({owner:'o', repo:'r', branch:'main', token:'x'}))")
    page.goto(SITE + '#/einrichtung'); page.reload()
    page.wait_for_selector('#setup-form')
    page.fill('input[name=code]', '1234'); page.fill('input[name=pw]', 'pruefung123'); page.fill('input[name=jgPhysik]', '8')
    page.click('#setup-form button[type=submit]')
    page.wait_for_selector('.fach', timeout=60000)
    check('Ersteinrichtung', 'data/inhalt.enc' in repo and 'data/zugang.json' in repo)

    # ---- ALTE Daten einspielen (Board + nurLK + sus/lk + Prüfung) ----
    page.evaluate(JS_HELPERS); page.add_init_script(JS_HELPERS)
    page.evaluate('''async () => {
      const K = await T.keys('1234', 'pruefung123'); const d = await T.getData(K);
      delete d.version;
      const f = d.faecher.find(x => x.id === 'physik'), j = f.jahrgaenge[0], r = j.reihen.find(x => x.id === 'optische-instrumente');
      const dir = 'material/physik/8/optische-instrumente/';
      r.board = { nodes:[{id:'a', x:50, y:50, t:'Licht', art:'thema'}], edges:[], bild: await T.file(K, dir+'bild.jpg.enc', 'BILD', 'basis') };
      r.vorhaben = [
        { id:'v1', titel:'Camera obscura', notiz:'', materialien:[
          { id:'m1', typ:'ab', titel:'Nachricht an Lena', nurLK:false, sus: await T.file(K, dir+'ab-lena.pdf.enc', 'PDF-LENA', 'basis'), lk: await T.file(K, dir+'ab-lena.docx.enc', 'DOCX-LENA', 'basis'), url:null },
          { id:'m2', typ:'loesung', titel:'Lösung Lena', nurLK:true, sus: await T.file(K, dir+'loes.pdf.enc', 'LOES', 'basis'), lk:null, url:null },
          { id:'m3', typ:'video', titel:'Erklärvideo', nurLK:false, sus:null, lk:null, url:'https://www.youtube.com/watch?v=x' },
          { id:'m4', typ:'pruefung', titel:'Test Optik', nurLK:true, sus: await T.file(K, dir+'test.pdf.enc', 'TEST', 'pruefung'), lk:null, url:null } ]},
        { id:'v2', titel:'Linsen', notiz:'', ausgeblendet:true, materialien:[
          { id:'m5', typ:'ab', titel:'AB Linsen', nurLK:false, sus: await T.file(K, dir+'linsen.pdf.enc', 'LINSEN', 'basis'), lk:null, url:null } ]}
      ];
      await T.putData(K, d);
    }''')

    # ---- Lehrkraft-Ansicht nach Migration ----
    page.goto(SITE + '#/f/physik/8/optische-instrumente'); page.reload()
    page.wait_for_selector('.rows')
    time.sleep(0.8)
    row1 = page.locator('.row').nth(0)
    sus_titles = row1.locator('.row-main > .chips .chip').all_inner_texts()
    check('Migration: SuS-Chips (AB + Video)', any('Nachricht an Lena' in t for t in sus_titles) and any('Erklärvideo' in t for t in sus_titles) and not any('Lösung' in t for t in sus_titles), sus_titles)
    check('Migration: Lehrkraft-Material (DOCX, Lösung, Test)', 'Lehrkraft-Material (3)' in row1.inner_text(), row1.inner_text())
    check('Titelbild sichtbar (aus board.bild)', page.locator('img.titelbild').count() == 1 and page.locator('.board').count() == 0)
    page.wait_for_function("document.querySelector('img.titelbild') && document.querySelector('img.titelbild').src.startsWith('blob:')", timeout=5000)
    shot('01-lehrkraft-migriert')

    # ---- Bearbeiten-Modus: Auge pro Material ----
    page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    shot('02-bearbeiten')
    check('Zwei Knöpfe pro Vorhaben', page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=sus]').count() == 1 and page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=lk]').count() == 1)
    check('Concept-Map-Editor entfernt', page.locator('[data-act=edit-board]').count() == 0 and page.locator('[data-act=edit-bild]').count() >= 1)
    page.locator('.row').nth(0).locator('[data-act=vis-m]').nth(1).click()   # Erklärvideo ausblenden
    wait_saved()
    check('Material ausblenden speichert', page.locator('.row').nth(0).locator('.chip.aus').count() == 1)
    shot('03-material-ausgeblendet')

    # ---- Upload SuS-Material (PDF) ----
    page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=sus]').click()
    page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/AB Spiegel-Parcours.pdf')
    check('Titel aus Dateiname', page.input_value('input[name=titel]') == 'AB Spiegel-Parcours', page.input_value('input[name=titel]'))
    shot('04-dialog-sus')
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    # ---- Upload Lehrkraft-Material (DOCX) ----
    page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=lk]').click()
    page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/AB Spiegel-Parcours.docx')
    check('LK-Dialog: Sichtbarkeit verborgen', page.locator('#sichtbar-row').is_hidden())
    shot('05-dialog-lk')
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    # ---- Klausur im SuS-Feld -> wird automatisch Lehrkraft/Prüfung ----
    page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=sus]').click()
    page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/Klausur Optik.pdf')
    check('Klausur erkannt -> Prüfung + Lehrkraft', page.input_value('select[name=typ]') == 'pruefung' and page.is_checked('input[name=bereich][value=lk]'))
    page.click('dialog#sheet button[value=ok]')
    page.wait_for_selector('dialog#sheet[open] input[name=pw]'); page.fill('input[name=pw]', 'pruefung123'); page.click('dialog#sheet button[value=ok]')
    wait_saved()
    # ---- Video-Datei wird abgelehnt ----
    n_before = len(dialogs)
    page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=sus]').click()
    page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/Film.mp4')
    page.click('dialog#sheet button[value=ok]'); time.sleep(1.5); shot('dbg-video'); print('DBG', dialogs[-3:], page.locator('dialog#sheet[open]').count())
    check('Video-Upload abgelehnt', any('Videos bitte nicht hochladen' in d for d in dialogs[n_before:]), dialogs[n_before:])
    # ---- Titelbild ändern (großes PNG wird verkleinert) ----
    page.click('[data-act=edit-bild]'); page.wait_for_selector('dialog#sheet[open]')
    page.click('input[name=bild__mode][value=file]')
    page.set_input_files('input[name=bild__file]', FILES + '/Conceptmap.png')
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    tb = [k for k in repo if 'conceptmap' in k]
    check('Titelbild hochgeladen + alte Datei gelöscht', len(tb) == 1 and 'material/physik/8/optische-instrumente/bild.jpg.enc' not in repo, tb)
    check('Titelbild verkleinert (JPEG)', tb and tb[0].endswith('.jpg.enc') and len(repo[tb[0]]) < os.path.getsize(FILES + '/Conceptmap.png'), [(k, len(repo[k])) for k in tb])
    page.click('#edit-toggle')
    time.sleep(0.5)
    shot('06-lehrkraft-nach-upload')

    # ---- Datenmodell prüfen ----
    d = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    r = [x for x in d['faecher'][1]['jahrgaenge'][0]['reihen'] if x['id'] == 'optische-instrumente'][0]
    mats = r['vorhaben'][0]['materialien']
    check('Datenmodell v2', d.get('version') == 2 and 'board' not in r and r['titelbild'] and all('bereich' in m and 'sus' not in m and 'nurLK' not in m for m in mats), json.dumps(mats)[:400])
    check('Prüfung mit Prüfungsschlüssel', all(m['datei']['schutz'] == 'pruefung' for m in mats if m['typ'] == 'pruefung'))
    check('Lösung + DOCX im LK-Bereich', [m['bereich'] for m in mats if m['titel'] == 'Lösung Lena'] == ['lk'] and len([m for m in mats if m['titel'] == 'Nachricht an Lena']) == 2)

    # ---- Speicheranzeige ----
    page.goto(SITE + '#/einstellungen'); page.wait_for_selector('.store-list')
    page.wait_for_function("document.querySelector('#repo-size').textContent.indexOf('ca.') >= 0", timeout=5000)
    check('Speicheranzeige', 'Physik' in page.inner_text('.store-list') and 'Jahrgang 8' in page.inner_text('.store-list'))
    shot('07-speicher')

    # ---- Kursansicht ----
    page.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page.wait_for_selector('.rows')
    time.sleep(0.5)
    txt = page.inner_text('main')
    check('Kurs: kein „Ganze Sammlung öffnen“', 'Ganze Sammlung' not in txt)
    check('Kurs: kein LK-Material, keine Lösung/Klausur', 'Lösung Lena' not in txt and 'Klausur' not in txt and 'Lehrkraft' not in txt)
    check('Kurs: ausgeblendetes Material/Vorhaben fehlt', 'Erklärvideo' not in txt and 'Linsen' not in txt and 'Nachricht an Lena' in txt)
    check('Kurs: Titelbild', page.locator('img.titelbild').count() == 1)
    check('Kurs: Lehrkraft-Knopf (Gerät mit Token)', page.locator('#kurs-exit').is_visible())
    shot('08-kurs')
    with page.expect_download() as dl:
        page.click('[data-act=dl-reihe]')
    zpath = OUT + '/sus.zip'; dl.value.save_as(zpath)
    names = zipfile.ZipFile(zpath).namelist()
    check('SuS-ZIP: nur SuS-Inhalte', any('Nachricht an Lena.pdf' in n for n in names) and any('AB Spiegel-Parcours.pdf' in n for n in names)
          and not any(x in ' '.join(names) for x in ['docx', 'Lösung', 'Klausur', 'Test Optik', 'Linsen']), names)
    check('SuS-ZIP: Inhalt entschlüsselt', zipfile.ZipFile(zpath).read([n for n in names if 'Lena' in n][0]) == b'PDF-LENA')
    page.click('#kurs-exit'); page.wait_for_selector('.crumbs')
    check('Lehrkraft-Knopf führt zur Reihe', '#/f/physik/8/optische-instrumente' in page.url)

    # ---- Export -> Reihe löschen -> Import ----
    page.goto(SITE + '#/f/physik/8'); page.wait_for_selector('.reihe-card')
    with page.expect_download() as dl:
        page.click('[data-act=export-j]')
    epath = OUT + '/export.zip'; dl.value.save_as(epath)
    plan = json.loads(zipfile.ZipFile(epath).read('import.json'))
    pr = [x for x in plan['eintraege'][0]['reihen'] if x['titel'] == 'Sehhilfen für nah und fern'][0]
    check('Export v2 mit Titelbild/bereich/ausgeblendet', plan['version'] == 2 and pr.get('titelbild') and any(m.get('ausgeblendet') for m in pr['vorhaben'][0]['materialien']) and all('bereich' in m for m in pr['vorhaben'][0]['materialien']))
    # Reihe löschen
    page.goto(SITE + '#/f/physik/8/optische-instrumente'); page.wait_for_selector('.rows')
    page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    page.evaluate("document.querySelector('#toast').classList.remove('on')"); page.click('.page-head [data-act=del-r]'); wait_saved()
    # Import
    page.goto(SITE + '#/einstellungen'); page.wait_for_selector('[data-act=import]')
    with page.expect_file_chooser() as fc:
        page.click('[data-act=import]')
    fc.value.set_files(epath)
    page.wait_for_selector('dialog#sheet[open]'); page.click('dialog#sheet button[value=ok]')
    wait_saved()
    d2 = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    r2 = [x for x in d2['faecher'][1]['jahrgaenge'][0]['reihen'] if x['titel'] == 'Sehhilfen für nah und fern'][0]
    m2 = r2['vorhaben'][0]['materialien']
    check('Import: Reihen-ID bleibt (Kurs-Link)', r2['id'] == 'optische-instrumente', r2['id'])
    check('Import: Titelbild wieder da', bool(r2.get('titelbild')))
    check('Import: Bereiche + Ausblenden erhalten', sorted((m['titel'], m['bereich'], m['ausgeblendet']) for m in m2) == sorted((m['titel'], m['bereich'], m['ausgeblendet']) for m in mats) , [(m['titel'], m['bereich'], m['ausgeblendet']) for m in m2])

    # ---- Import einer ALTEN import.json (v1, board.bild) ----
    v1 = {'format': 'unterrichtsmaterial-import', 'version': 1, 'fach': 'Physik', 'jahrgang': '9', 'reihen': [{'titel': 'Alt', 'board': {'nodes': [], 'edges': [], 'bild': 'dateien/b.png'},
          'vorhaben': [{'titel': 'V', 'materialien': [{'typ': 'ab', 'titel': 'X', 'sicht': 'alle', 'sus': 'dateien/x.pdf', 'lk': 'dateien/x.docx'}]}]}]}
    zb = io.BytesIO(); z = zipfile.ZipFile(zb, 'w')
    z.writestr('import.json', json.dumps(v1)); z.writestr('dateien/x.pdf', PDF); z.writestr('dateien/x.docx', b'D'); z.writestr('dateien/b.png', open(FILES + '/Conceptmap.png', 'rb').read()); z.close()
    open(OUT + '/v1.zip', 'wb').write(zb.getvalue())
    with page.expect_file_chooser() as fc:
        page.click('[data-act=import]')
    fc.value.set_files(OUT + '/v1.zip')
    page.wait_for_selector('dialog#sheet[open]'); page.click('dialog#sheet button[value=ok]'); wait_saved()
    d3 = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    j9 = [j for j in d3['faecher'][1]['jahrgaenge'] if j['name'] == '9'][0]
    ms = j9['reihen'][0]['vorhaben'][0]['materialien']
    check('Import v1: aufgeteilt in SuS + LK, Titelbild', sorted(m['bereich'] for m in ms) == ['lk', 'sus'] and j9['reihen'][0].get('titelbild'))

    # ---- SuS-Gerät ohne Token: Kursmodus + versteckter Rückweg ----
    page2 = ctx.new_page(); page2.on('dialog', lambda d: d.accept()); page2.on('pageerror', lambda e: errors.append(str(e)))
    page2.goto(SITE); page2.evaluate("localStorage.clear()")
    page2.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page2.reload()
    page2.wait_for_selector('#pad')
    for k in '1234': page2.click(f'#pad [data-k="{k}"]')
    page2.wait_for_selector('.rows', timeout=30000)
    check('SuS: kein Lehrkraft-Knopf', page2.locator('#kurs-exit').is_hidden())
    page2.goto(SITE); page2.wait_for_selector('.rows')
    check('SuS: Start merkt Kursansicht', '#/kurs/' in page2.url)
    for _ in range(5): page2.click('[data-kurs-pill]')
    page2.wait_for_selector('[data-act=leave-kurs]')
    page2.screenshot(path=f'{OUT}/09-sus-einstellungen.png')
    page2.click('[data-act=leave-kurs]'); page2.wait_for_selector('.faecher')
    page2.goto(SITE); page2.wait_for_selector('.faecher')
    check('SuS: Kursmodus beendet', '#/kurs/' not in page2.url)


    # ================= A: Sammel-Upload (Ordnerstruktur wie am Laptop) =================
    import shutil
    base = OUT + '/GSQ/Schuljahr 2526/2526 M 6'
    shutil.rmtree(OUT + '/GSQ', ignore_errors=True)
    rd = base + '/M 6 Brüche'; os.makedirs(rd)
    names = ['M 6 Brüche - 1 Addition ungleichnamiger Brüche.docx', 'M 6 Brüche - 1 Addition ungleichnamiger Brüche.pdf',
             'M 6 Brüche - 2 AB Bruchrechnung Fehler.docx', 'M 6 Brüche - 2 Bruchrechnung Fehler.pdf', 'M 6 Brüche - 2 Fehler und unechte Brüche.docx',
             'M 6 Brüche - 5 AB Bruchrechnung.docx', 'M 6 Brüche - 5 Sachaufgaben Bruchrechnung.docx', 'Klausur Brüche.pdf', '~$temp.docx']
    for n in names: open(rd + '/' + n, 'wb').write((PDF if n.endswith('.pdf') else b'PK docx ') + n.encode())
    page.bring_to_front(); page2.close()
    page.evaluate("localStorage.setItem('um-github', JSON.stringify({owner:'o', repo:'r', branch:'main', token:'x'}))")
    def open_sync_dir(path):
        page.goto(SITE + '#/einstellungen'); page.wait_for_selector('[data-act=sync]')
        page.click('[data-act=sync]'); page.wait_for_selector('dialog#sheet[open] [data-pick=dir]')
        with page.expect_file_chooser() as fc:
            page.click('[data-pick=dir]')
        fc.value.element.set_input_files(path)
        page.wait_for_selector('.sync-body .sync-box', timeout=30000); time.sleep(0.3)
    open_sync_dir(base)
    shot('11-sync-vorschau')
    grp = page.locator('.sync-box').nth(1)
    check('A: Reihe aus Ordner, Fach + Jahrgang erkannt', grp.locator('h3').inner_text() == 'M 6 Brüche' and page.input_value('select[data-k=fach]') == 'mathe'
          and page.input_value('input[data-k=jgnew]') == '6' and page.input_value('input[data-k=rtitel]') == 'Brüche',
          [grp.locator('h3').inner_text(), page.input_value('select[data-k=fach]')])
    vrows = grp.locator('table.sync').nth(0).locator('tbody tr')
    check('A: Vorhaben nach Nummer (1, 2, 5, ohne Nr.)', vrows.count() == 4 and 'Nr. 1' in vrows.nth(0).inner_text() and 'ohne Nr.' in vrows.nth(3).inner_text(), vrows.all_inner_texts())
    vt = [page.input_value('input[data-k=vtitel][data-v="%s"]' % k) for k in ['nr:1', 'nr:2', 'nr:5']]
    check('A: Vorhaben-Titel aus Dateien', vt == ['Addition ungleichnamiger Brüche', 'Bruchrechnung Fehler', 'Bruchrechnung'], vt)
    frows = grp.locator('table.sync').nth(1).locator('tbody tr')
    def rowinfo(i):
        r = frows.nth(i); return (r.locator('.fname').inner_text(), r.locator('select[data-k=typ]').input_value(), r.locator('select[data-k=bereich]').input_value(), r.locator('input[data-k=titel]').input_value())
    info = [rowinfo(i) for i in range(frows.count())]
    check('A: ~$-Datei ignoriert, 8 Dateien', frows.count() == 8, info)
    d_ = {x[0]: x for x in info}
    check('A: PDF+DOCX-Paar: PDF SuS, Word LK', d_['M 6 Brüche - 1 Addition ungleichnamiger Brüche.pdf'][2] == 'sus' and d_['M 6 Brüche - 1 Addition ungleichnamiger Brüche.docx'][2] == 'lk'
          and d_['M 6 Brüche - 1 Addition ungleichnamiger Brüche.docx'][3] == 'Addition ungleichnamiger Brüche', info)
    check('A: Klausur -> Prüfung/LK', d_['Klausur Brüche.pdf'][1] == 'pruefung' and d_['Klausur Brüche.pdf'][2] == 'lk', d_['Klausur Brüche.pdf'])
    check('A: Zähler', page.inner_text('[data-s=go]') == '8 hochladen', page.inner_text('[data-s=go]'))
    page.click('[data-s=go]'); wait_saved()
    d4 = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    mj = [j for j in d4['faecher'][0]['jahrgaenge'] if j['name'] == '6']
    rb = mj[0]['reihen'][0] if mj else None
    check('A: Mathe 6 / Brüche mit 4 Vorhaben, 8 Materialien', rb and rb['titel'] == 'Brüche' and rb.get('ordner') == 'M 6 Brüche' and len(rb['vorhaben']) == 4
          and sum(len(v['materialien']) for v in rb['vorhaben']) == 8 and all(m.get('hash') and m.get('quelle') for v in rb['vorhaben'] for m in v['materialien']),
          json.dumps(rb)[:600] if rb else d4)
    check('A: Seite springt zur neuen Reihe', '#/f/mathe/6/brueche' in page.url, page.url)
    shot('12-nach-sync')
    open_sync_dir(base)
    sts = page.locator('.sync-box').nth(1).locator('.st').all_inner_texts()
    check('A: Abgleich – alles unverändert', all(x == 'unverändert' for x in sts) and page.locator('[data-s=go]').is_disabled(), sts)
    page.click('[data-s=close]'); time.sleep(0.3)
    open(rd + '/M 6 Brüche - 2 Bruchrechnung Fehler.pdf', 'wb').write(PDF + b'% neu')
    alt = [m['datei']['pfad'] for v in rb['vorhaben'] for m in v['materialien'] if m['quelle'].endswith('2 Bruchrechnung Fehler.pdf')][0]
    open_sync_dir(base)
    sts = page.locator('.sync-box').nth(1).locator('.st').all_inner_texts()
    check('A: Abgleich – 1 geändert', sts.count('geändert') == 1 and page.inner_text('[data-s=go]') == '1 hochladen', sts)
    page.click('[data-s=go]'); wait_saved()
    d5 = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    rb5 = [j for j in d5['faecher'][0]['jahrgaenge'] if j['name'] == '6'][0]['reihen'][0]
    neu = [m for v in rb5['vorhaben'] for m in v['materialien'] if m['quelle'].endswith('2 Bruchrechnung Fehler.pdf')]
    check('A: geänderte Datei ersetzt, alte gelöscht', len(neu) == 1 and neu[0]['datei']['pfad'] != alt and alt not in repo and sum(len(v['materialien']) for v in rb5['vorhaben']) == 8, (alt, neu))

    # ================= B =================
    page.goto(SITE + '#/f/mathe/6/brueche'); page.wait_for_selector('.rows')
    if not page.locator('body.editing').count():
        page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    page.evaluate("""() => { const dt = new DataTransfer();
      dt.items.add(new File(['%PDF-1.4 a'], 'Übung A.pdf', {type:'application/pdf'})); dt.items.add(new File(['%PDF-1.4 b'], 'Übung A Lösung.pdf', {type:'application/pdf'}));
      const row = document.querySelectorAll('.row[data-v]')[0];
      row.dispatchEvent(new DragEvent('dragover', {bubbles:true, cancelable:true, dataTransfer:dt}));
      row.dispatchEvent(new DragEvent('drop', {bubbles:true, cancelable:true, dataTransfer:dt})); }""")
    page.wait_for_selector('.sync-body .sync-box', timeout=15000); time.sleep(0.3)
    check('B: Ablegen auf Zeile -> Vorschau ohne Schema, Ziel = Vorhaben 1', page.locator('input[data-schema]').count() == 0
          and page.locator('select[data-k=vt]').first.input_value() == rb5['vorhaben'][0]['id'], page.locator('select[data-k=vt]').first.input_value())
    check('B: Lösung erkannt', page.locator('table.sync').nth(1).locator('tbody tr', has_text='Übung A Lösung.pdf').locator('select[data-k=typ]').input_value() == 'loesung')
    shot('13-drop-vorschau')
    page.click('[data-s=go]'); wait_saved()
    d6 = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    v1 = [j for j in d6['faecher'][0]['jahrgaenge'] if j['name'] == '6'][0]['reihen'][0]['vorhaben'][0]
    check('B: 2 Dateien im Vorhaben 1', sum(1 for m in v1['materialien'] if m['titel'].startswith('Übung A')) == 2, [m['titel'] for m in v1['materialien']])
    page.goto(SITE + '#/f/mathe/6/brueche'); page.wait_for_selector('.rows')
    if not page.locator('body.editing').count():
        page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    page.locator('.row').nth(1).locator('[data-act=add-m][data-bereich=sus]').click(); page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', [FILES + '/AB Spiegel-Parcours.pdf', FILES + '/AB Spiegel-Parcours.docx'])
    page.wait_for_selector('.sync-body .sync-box', timeout=15000)
    b2 = page.locator('table.sync').nth(1).locator('select[data-k=bereich]').all()
    check('B: Mehrfachauswahl im Dialog -> Vorschau mit Paar', len(b2) == 2 and sorted(x.input_value() for x in b2) == ['lk', 'sus'])
    page.click('[data-s=close]'); time.sleep(0.3)
    if page.locator('body.editing').count(): page.click('#edit-toggle'); time.sleep(0.3)


    # ================= HTML-Seiten: Brücke zur Oberfläche =================
    open(FILES + '/Camera Seite.html', 'w').write('''<!DOCTYPE html><html><head><title>Cam</title></head><body>
<p id="v"></p><button id="s" onclick="localStorage.setItem('x', String((+localStorage.getItem('x')||0)+1)); document.getElementById('v').textContent=localStorage.getItem('x')">+</button>
<a id="z" href="#zurueck">Zurück</a> <a id="w" href="#weiter">Weiter</a>
<script>document.getElementById('v').textContent = localStorage.getItem('x')||'0'; var sicher='nein'; try{ parent.localStorage.getItem('um-github'); }catch(e){ sicher='ja'; } document.body.setAttribute('data-sicher', sicher);</script></body></html>''')
    page.goto(SITE + '#/f/mathe/6/brueche'); page.wait_for_selector('.rows')
    if not page.locator('body.editing').count():
        page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    page.locator('.row').nth(0).locator('[data-act=add-m][data-bereich=sus]').click(); page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/Camera Seite.html')
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    page.click('#edit-toggle'); time.sleep(0.4)
    page.locator('.chip', has_text='Camera Seite').click()
    fr = page.frame_locator('.viewer iframe')
    fr.locator('#s').wait_for(timeout=10000)
    check('HTML: läuft abgeschottet (kein Zugriff auf Token/Schlüssel)', fr.locator('body').get_attribute('data-sicher') == 'ja')
    fr.locator('#s').click(); fr.locator('#s').click()
    check('HTML: localStorage funktioniert', fr.locator('#v').inner_text() == '2')
    check('HTML: Weiter-Knopf in der Leiste', page.locator('.viewer [data-v=next]').count() == 1)
    fr.locator('#z').click(); time.sleep(0.6)
    check('HTML: #zurueck schließt die Seite', page.locator('.viewer').count() == 0 and '#/f/mathe/6/brueche' in page.url)
    page.locator('.chip', has_text='Camera Seite').click()
    fr = page.frame_locator('.viewer iframe'); fr.locator('#s').wait_for(timeout=10000); time.sleep(0.3)
    check('HTML: Fortschritt bleibt gespeichert', fr.locator('#v').inner_text() == '2', fr.locator('#v').inner_text())
    fr.locator('#w').click(); time.sleep(1)
    t2 = page.locator('.viewer .viewer-bar b').inner_text() if page.locator('.viewer').count() else ''
    check('HTML: #weiter öffnet nächstes Material', page.locator('.viewer').count() == 1 and t2 and t2 != 'Camera Seite', t2)
    shot('17-weiter')
    page.go_back(); time.sleep(0.5)
    check('HTML: Zurück nach Weiter landet in der Reihe', page.locator('.viewer').count() == 0)


    # ================= Freischalten ab Datum, Hinweis, Checkliste, Suche, Camera, Vorlage =================
    import datetime
    morgen = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    gestern = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    R = '#/f/physik/8/optische-instrumente'
    def edit_on():
        if not page.locator('body.editing').count():
            page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    def edit_off():
        if page.locator('body.editing').count(): page.click('#edit-toggle'); time.sleep(0.3)
    page.goto(SITE + R); page.wait_for_selector('.rows'); edit_on()
    # Vorhaben 1 erst ab morgen
    page.locator('.row').nth(0).locator('[data-act=edit-v]').click(); page.wait_for_selector('dialog#sheet[open] input[name=ab]')
    page.fill('dialog#sheet input[name=ab]', morgen); page.click('dialog#sheet button[value=ok]'); wait_saved()
    check('Datum: Badge „für SuS ab“ in Lehrkraft-Ansicht', 'für SuS ab' in page.locator('.row').nth(0).inner_text())
    # Material in Vorhaben 2 (Linsen ist ausgeblendet) -> nimm die Camera-Zeile? Material „Erklärvideo“-Link ist ausgeblendet; nimm „AB Spiegel-Parcours“ (Vorhaben 1) – stattdessen neues Material in Vorhaben 2:
    page.locator('.row').nth(1).locator('[data-act=add-m][data-bereich=sus]').click(); page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/camera-obscura.html')
    page.fill('dialog#sheet input[name=ab]', gestern)
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    page.locator('.row').nth(1).locator('[data-act=add-m][data-bereich=sus]').click(); page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/AB Spiegel-Parcours.pdf')
    page.fill('dialog#sheet input[name=titel]', 'Lösungsblatt später')
    page.select_option('dialog#sheet select[name=typ]', 'ab')
    page.fill('dialog#sheet input[name=ab]', morgen)
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    check('Datum: Material-Chip zeigt „ab …“', page.locator('.row').nth(1).locator('.chip.aus', has_text='Lösungsblatt später').count() == 1)
    # Vorhaben 2 einblenden (war ausgeblendet), damit Kursansicht es zeigt
    page.locator('.row').nth(1).locator('[data-act=vis-v]').click(); wait_saved()
    # Hinweis
    page.click('[data-act=edit-hinweis]'); page.wait_for_selector('dialog#sheet[open] textarea[name=text]')
    page.fill('dialog#sheet textarea[name=text]', 'Test am Freitag: Spiegel und Schatten'); page.fill('dialog#sheet input[name=bis]', morgen)
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    # Checkliste aus Word-Datei
    import zipfile as _zf
    dx = FILES + '/Checkliste.docx'
    with _zf.ZipFile(dx, 'w', _zf.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', '<w:document><w:body><w:p><w:r><w:t># Licht</w:t></w:r></w:p><w:p><w:r><w:t>Ich kann erklären, </w:t></w:r><w:r><w:t xml:space="preserve">wie wir sehen.</w:t></w:r></w:p><w:p></w:p><w:p><w:r><w:t>• Ich kann den Strahlengang zeichnen &amp; beschriften.</w:t></w:r></w:p></w:body></w:document>')
    page.click('[data-act=edit-check]'); page.wait_for_selector('dialog#sheet[open] textarea[name=liste]')
    with page.expect_file_chooser() as fc:
        page.click('dialog#sheet [data-x=datei]')
    fc.value.set_files(dx); time.sleep(0.8)
    lv = page.input_value('dialog#sheet textarea[name=liste]')
    check('Checkliste: aus Word übernommen', lv.split('\n')[:2] == ['# Licht', 'Ich kann erklären, wie wir sehen.'] and '&' in lv, lv)
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    edit_off()
    shot('18-lehrkraft-hinweis-checkliste')
    # Kursansicht
    page.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page.wait_for_selector('.rows'); time.sleep(0.4)
    txt = page.inner_text('main')
    vt = page.locator('.row-title b').all_inner_texts()
    check('Datum: Vorhaben ab morgen in Kursansicht unsichtbar', 'Camera obscura' not in vt and 'Linsen' in vt, vt)
    check('Datum: Material ab morgen unsichtbar, ab gestern sichtbar', 'Lösungsblatt später' not in txt and 'camera-obscura' in txt, txt[:400])
    check('Hinweis in Kursansicht', page.locator('.hinweis').count() == 1 and 'Test am Freitag' in page.inner_text('.hinweis'))
    check('Checkliste in Kursansicht', page.locator('details.checkbox').count() == 1)
    page.click('details.checkbox > summary'); time.sleep(0.2)
    b = page.locator('.ck').first; b.click(); b.click()
    check('Checkliste: zweimal tippen = sicher, Zähler', 'sicher' in b.get_attribute('class') and page.inner_text('[data-checkcount]') == '1 / 2 sicher', page.inner_text('[data-checkcount]'))
    page.reload(); page.wait_for_selector('details.checkbox')
    check('Checkliste: bleibt gespeichert und offen', page.locator('details.checkbox[open]').count() == 1 and 'sicher' in page.locator('.ck').first.get_attribute('class'))
    shot('19-kurs-hinweis-checkliste')
    # Camera-Seite in der App
    page.locator('.chip', has_text='camera-obscura').first.click()
    fr = page.frame_locator('.viewer iframe'); fr.locator('h1').first.wait_for(timeout=15000)
    fr.locator('a.step[data-page=bauen]').click(); time.sleep(0.4)
    check('Camera: Schritt-Navigation funktioniert in der App', fr.locator('#bauen').is_visible() and not fr.locator('#auftrag').is_visible())
    check('Camera: „‹ Übersicht“ sichtbar', fr.locator('.bar .home').is_visible())
    shot('20-camera-in-app')
    fr.locator('.bar .home').click(); time.sleep(0.5)
    check('Camera: „‹ Übersicht“ führt zurück', page.locator('.viewer').count() == 0)
    # Abgelaufener Hinweis verschwindet
    page.goto(SITE + R); page.wait_for_selector('.rows'); edit_on()
    page.click('.hinweis [data-act=edit-hinweis]'); page.wait_for_selector('dialog#sheet[open] input[name=bis]')
    page.fill('dialog#sheet input[name=bis]', gestern); page.click('dialog#sheet button[value=ok]'); wait_saved()
    edit_off()
    page.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page.wait_for_selector('.rows'); time.sleep(0.3)
    check('Hinweis: nach Ablauf nicht mehr sichtbar', page.locator('.hinweis').count() == 0)
    page.click('#kurs-exit'); page.wait_for_selector('.crumbs')
    # Suche
    page.click('#search-btn'); page.wait_for_selector('#such-feld')
    page.fill('#such-feld', 'lena'); time.sleep(0.3)
    check('Suche: findet Material „Nachricht an Lena“', page.locator('#such-treffer .chip', has_text='Nachricht an Lena').count() >= 1)
    page.fill('#such-feld', 'bruche'); time.sleep(0.3)
    check('Suche: ohne Umlaute („bruche“ → Brüche)', 'Brüche' in page.inner_text('#such-treffer'))
    shot('21-suche')
    page.locator('#such-treffer a.ziel').first.click(); page.wait_for_selector('.rows')
    check('Suche: Treffer führt zur Reihe', '#/f/mathe/6/brueche' in page.url, page.url)
    # Vorlage: herunterladbar und in der App lauffähig
    page.goto(SITE + '#/einstellungen'); page.wait_for_selector('[data-act=vorlage]')
    with page.expect_download() as dl:
        page.click('[data-act=vorlage]')
    vp = OUT + '/vorlage.html'; dl.value.save_as(vp)
    check('Vorlage: Download', 'data-quiz' in open(vp, encoding='utf-8').read())
    import shutil as _sh; _sh.copy(vp, FILES + '/Vorlage Seite.html')
    page.goto(SITE + R); page.wait_for_selector('.rows'); edit_on()
    page.locator('.row').nth(1).locator('[data-act=add-m][data-bereich=sus]').click(); page.wait_for_selector('dialog#sheet[open]')
    page.set_input_files('input[name=datei__file]', FILES + '/Vorlage Seite.html')
    page.click('dialog#sheet button[value=ok]'); wait_saved(); edit_off()
    page.locator('.chip', has_text='Vorlage Seite').click()
    fr = page.frame_locator('.viewer iframe'); fr.locator('h1').first.wait_for(timeout=10000)
    fr.locator('a.step[data-page=aufgaben]').click(); time.sleep(0.3)
    fr.locator('[data-quiz] button').nth(1).click()
    check('Vorlage: Quiz gibt Rückmeldung', 'richtig' in (fr.locator('[data-quiz] button').nth(1).get_attribute('class') or ''))
    fr.locator('a.step[data-page=sichern]').click(); time.sleep(0.3)
    fr.locator('textarea[data-antwort]').fill('Meine Antwort'); time.sleep(0.8)
    fr.locator('.fertig:visible').first.click(); time.sleep(0.6)
    check('Vorlage: Fertig-Knopf verlässt die Seite', page.locator('.viewer').count() == 0 or 'Vorlage Seite' not in page.inner_text('.viewer .viewer-bar b'))
    if page.locator('.viewer').count(): page.go_back(); time.sleep(0.4)
    page.locator('.chip', has_text='Vorlage Seite').click()
    fr = page.frame_locator('.viewer iframe'); fr.locator('h1').first.wait_for(timeout=10000)
    fr.locator('a.step[data-page=sichern]').click(); time.sleep(0.3)
    check('Vorlage: Antwort bleibt gespeichert', fr.locator('textarea[data-antwort]').input_value() == 'Meine Antwort')
    shot('22-vorlage')
    page.go_back(); time.sleep(0.4)

    # ================= D: Notizen pro Vorhaben + Niveau =================
    page.goto(SITE + '#/f/physik/8/optische-instrumente'); page.wait_for_selector('.rows'); time.sleep(0.4)
    if page.locator('body.editing').count() == 0: page.click('#edit-toggle'); page.wait_for_selector('body.editing')
    row0 = page.locator('.row').nth(0)
    row0.locator('[data-act=notiz-v]').click(); page.wait_for_selector('dialog#sheet[open] textarea[name=ziel]')
    page.fill('textarea[name=ziel]', 'SuS erklären die Bildentstehung'); page.fill('textarea[name=verlauf]', 'Einstieg\nErarbeitung\nSicherung')
    page.fill('textarea[name=reflexion]', 'Gruppenphase lief gut')
    page.click('dialog#sheet button[value=ok]'); wait_saved()
    d = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    v0 = [x for x in d['faecher'][1]['jahrgaenge'][0]['reihen'] if x['id'] == 'optische-instrumente'][0]['vorhaben'][0]
    check('D: Notizen gespeichert (Ziel, Verlauf, Reflexion)', v0.get('planung') == {'ziel': 'SuS erklären die Bildentstehung', 'verlauf': 'Einstieg\nErarbeitung\nSicherung', 'reflexion': 'Gruppenphase lief gut'}, v0.get('planung'))
    page.locator('.row').nth(0).locator('.row-main > .chips [data-act=edit-m]', has_text='Nachricht an Lena').click()
    page.wait_for_selector('dialog#sheet[open] select[name=niveau]')
    page.select_option('select[name=niveau]', '2'); page.click('dialog#sheet button[value=ok]'); wait_saved()
    page.locator('.row').nth(0).locator('[data-act=edit-m]', has_text='AB Spiegel-Parcours').first.click()
    page.wait_for_selector('dialog#sheet[open] select[name=niveau]')
    check('D: Niveau-Auswahl im Dialog (ohne/Basis/Standard/Erweiterung)', page.locator('select[name=niveau] option').count() == 4 and page.input_value('select[name=niveau]') == '')
    page.select_option('select[name=niveau]', '3'); page.click('dialog#sheet button[value=ok]'); wait_saved()
    d = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    ms0 = [x for x in d['faecher'][1]['jahrgaenge'][0]['reihen'] if x['id'] == 'optische-instrumente'][0]['vorhaben'][0]['materialien']
    check('D: Niveau gespeichert', sorted((m['titel'], m.get('niveau')) for m in ms0 if m.get('niveau')) == [('AB Spiegel-Parcours', 3), ('Nachricht an Lena', 2)], [(m['titel'], m.get('niveau')) for m in ms0])
    page.locator('.row').nth(1).locator('[data-act=edit-m]', has_text='AB Linsen').first.click()   # Vorhaben 2 ist in der Kursansicht sichtbar
    page.wait_for_selector('dialog#sheet[open] select[name=niveau]'); page.select_option('select[name=niveau]', '1'); page.click('dialog#sheet button[value=ok]'); wait_saved()
    page.click('#edit-toggle'); time.sleep(0.4)
    row0 = page.locator('.row').nth(0)
    check('D: Sterne am Chip', '★★' in row0.locator('.chip', has_text='Nachricht an Lena').first.inner_text() and '★★★' in row0.locator('.chip', has_text='AB Spiegel-Parcours').first.inner_text())
    tg = row0.locator('.lk-toggle')
    check('D: LK-Bereich nennt Notizen', 'Notizen' in tg.inner_text(), tg.inner_text())
    if tg.get_attribute('aria-expanded') != 'true': tg.click(); time.sleep(0.2)
    check('D: Notizen im LK-Bereich sichtbar', 'Gruppenphase lief gut' in row0.locator('.lk-notizen').inner_text() and 'Schwerpunktziel' in row0.locator('.lk-notizen').inner_text())
    shot('23-notizen-niveau')
    page.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page.wait_for_selector('.rows'); time.sleep(0.5)
    txt = page.inner_text('main')
    check('D: Kurs ohne Notizen', 'Gruppenphase' not in txt and 'Bildentstehung' not in txt and 'Notizen' not in txt)
    check('D: Kurs mit Sternen + Legende', '★' in page.locator('.chip', has_text='AB Linsen').inner_text() and 'Basis' in txt and 'Erweiterung' in txt)
    shot('24-kurs-niveau')
    page.click('#kurs-exit'); page.wait_for_selector('.crumbs')
    page.goto(SITE + '#/suche'); page.wait_for_selector('#such-feld'); page.fill('#such-feld', 'Gruppenphase'); time.sleep(0.6)
    check('D: Suche findet Notizen (Lehrkraft)', 'Spiegel' in page.inner_text('#such-treffer') or page.locator('#such-treffer .chip, #such-treffer a').count() > 0, page.inner_text('#such-treffer')[:200])

    # ================= C: Sicherung -> „Alles ersetzen“ =================
    page.evaluate("""async () => { const K = await T.keys('1234','pruefung123'); const d = await T.getData(K);
      const r = d.faecher[1].jahrgaenge[0].reihen.find(x => x.id === 'optische-instrumente');
      r.uebersicht = { sus: await T.file(K, 'material/physik/8/optische-instrumente/lernlandkarte.pdf.enc', 'LLK', 'basis'), lk:null, url:null };
      d.faecher[1].farbe = 'lila'; d.faecher.push({ id:'chemie', name:'Chemie', farbe:'rot', vorlage:null, extern:'https://x.github.io/chemie/', jahrgaenge:[] });
      await T.putData(K, d); }""")
    page.goto(SITE + '#/einstellungen'); page.reload(); page.wait_for_selector('[data-act=unlock-p]')
    page.click('[data-act=unlock-p]'); page.wait_for_selector('dialog#sheet[open] input[name=pw]'); page.fill('input[name=pw]', 'pruefung123'); page.click('dialog#sheet button[value=ok]')
    time.sleep(0.8); page.wait_for_selector('[data-act=export-all]')
    before = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    page.evaluate("document.querySelector('#toast').classList.remove('on')")
    with page.expect_download() as dl:
        page.click('[data-act=export-all]')
    spath = OUT + '/sicherung.zip'; dl.value.save_as(spath)
    page.evaluate("""async () => { const K = await T.keys('1234','pruefung123'); const d = await T.getData(K); d.faecher[0].jahrgaenge = []; d.faecher[1].jahrgaenge[0].reihen.reverse(); await T.putData(K, d); }""")
    page.reload()
    page.wait_for_selector('[data-act=import]')
    page.click('[data-act=unlock-p]'); page.wait_for_selector('dialog#sheet[open] input[name=pw]'); page.fill('input[name=pw]', 'pruefung123'); page.click('dialog#sheet button[value=ok]'); time.sleep(0.8)
    cur = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    def paths(o):
        out = set()
        if isinstance(o, dict):
            if isinstance(o.get('pfad'), str): out.add(o['pfad'])
            for v in o.values(): out |= paths(v)
        elif isinstance(o, list):
            for v in o: out |= paths(v)
        return out
    files_before = paths(cur)
    page.evaluate("document.querySelector('#toast').classList.remove('on')")
    with page.expect_file_chooser() as fc:
        page.click('[data-act=import]')
    fc.value.set_files(spath)
    page.wait_for_selector('dialog#sheet[open] input[name=modus]'); page.click('input[name=modus][value=ersetzen]')
    shot('15-ersetzen-dialog')
    page.click('dialog#sheet button[value=ok]')
    page.wait_for_function("document.querySelector('#toast').textContent.indexOf('Alte Dateien gelöscht') >= 0", timeout=120000); time.sleep(0.5)
    after = page.evaluate("async () => { const K = await T.keys('1234','pruefung123'); return T.getData(K); }")
    def norm(d):
        out = []
        for f in d['faecher']:
            out.append(('F', f['id'], f['name'], f.get('farbe'), f.get('extern')))
            for j in f['jahrgaenge']:
                out.append(('J', j['id'], j['name']))
                for r in j['reihen']:
                    out.append(('R', r['id'], r['titel'], r.get('ordner'), bool(r.get('titelbild')), bool(r.get('uebersicht') and r['uebersicht'].get('sus')), json.dumps(r.get('hinweis')), json.dumps(r.get('checkliste'))))
                    for v in r['vorhaben']:
                        out.append(('V', v['titel'], bool(v.get('ausgeblendet')), v.get('ab'), json.dumps(v.get('planung'))))
                        for m in v['materialien']:
                            out.append(('M', m['titel'], m['typ'], m['bereich'], bool(m.get('ausgeblendet')), bool(m.get('datei')), m.get('url'), (m.get('datei') or {}).get('schutz'), m.get('hash'), m.get('ab'), m.get('niveau')))
        return out
    nb, na = norm(before), norm(after)
    check('C: „Alles ersetzen“ stellt Stand verlustfrei wieder her', nb == na, [x for x in nb if x not in na][:5] + ['---'] + [x for x in na if x not in nb][:5])
    check('C: Datum/Hinweis/Checkliste in Sicherung', any(x[0]=='R' and x[7] != 'null' for x in na) and any(x[0]=='V' and x[3] for x in na) and any(x[0]=='M' and x[9] for x in na))
    check('C: Notizen + Niveau in Sicherung', any(x[0]=='V' and x[4] != 'null' for x in na) and any(x[0]=='M' and x[10] for x in na))
    check('C: Prüfung wiederhergestellt', any(x[0] == 'M' and x[2] == 'pruefung' and x[7] == 'pruefung' for x in na))
    check('C: alte Dateien gelöscht', not (files_before & set(k for k in repo if k.startswith('material/'))), sorted(files_before & set(repo)))
    shot('16-nach-ersetzen')


    # iPad-Größe Screenshot
    page.set_viewport_size({'width': 820, 'height': 1180})
    page.goto(SITE + '#/kurs/physik/8/optische-instrumente'); page.wait_for_selector('.rows'); time.sleep(0.6)
    shot('10-kurs-ipad')
    errors = [x for x in errors if 'serviceWorker' not in x]; check('Keine JS-Fehler', not errors, errors)
    br.close()

print('\n%d/%d bestanden' % (sum(1 for r in results if r[1]), len(results)))
