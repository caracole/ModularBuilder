#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║  ModularBuilder — Serveur local                        ║
║  « Éviter de faire tout ce que l'ordinateur peut faire » ║
║  Pierre-Henri Giraud × Claude · 2026                   ║
╚══════════════════════════════════════════════════════════╝

Usage :  python3 modular_server.py
         → ouvre automatiquement l'interface dans le navigateur
         → Ctrl+C pour arrêter
"""

import http.server, json, os, subprocess, shutil, re, sys, webbrowser, urllib.parse
from pathlib import Path
from datetime import datetime

PORT = 7777
HOST = '127.0.0.1'

# ── Configuration par défaut (MediFolio) ──
CONFIG_FILE = os.path.expanduser('~/.modular_builder.json')
DEFAULT_CONFIG = {
    'project_name': 'MediFolio',
    'work_dir': os.path.expanduser('~/Escritorio/MediFolio/MediFolio_modular'),
    'skeleton': 'skeleton.html',
    'output': 'MediFolio.html',
    'modules_dir': 'modules',
    'github_dir': os.path.expanduser('~/Escritorio/MediFolio_github'),
    'browser': 'brave-browser',
    'include_pattern': r'<INCLUDE:(.+?)\s*/>',
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

CFG = load_config()

def ok_json(handler, data):
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def err_json(handler, msg, code=400):
    handler.send_response(code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps({'error': msg}, ensure_ascii=False).encode('utf-8'))

# ── BUILD ENGINE ──
def do_build():
    """Assemble skeleton + modules → output HTML"""
    cfg = load_config()
    work = cfg['work_dir']
    skel_path = os.path.join(work, cfg['skeleton'])
    out_path = os.path.join(work, cfg['output'])
    pattern = re.compile(cfg['include_pattern'])

    if not os.path.exists(skel_path):
        return {'ok': False, 'error': f'skeleton introuvable: {skel_path}'}

    with open(skel_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    inc = 0
    warnings = []
    for line in lines:
        m = pattern.search(line)
        if m:
            fp = os.path.join(work, m.group(1).strip())
            if os.path.exists(fp):
                with open(fp, 'r', encoding='utf-8') as f2:
                    result.extend(f2.readlines())
                inc += 1
            else:
                warnings.append(f'Module introuvable: {m.group(1).strip()}')
                result.append(line)
        else:
            result.append(line)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(result)

    return {
        'ok': True,
        'lines': len(result),
        'modules': inc,
        'warnings': warnings,
        'output': out_path
    }

# ── PUBLISH ENGINE ──
def do_publish():
    """Copy output to github dir + git add/commit/push"""
    cfg = load_config()
    work = cfg['work_dir']
    gh = cfg['github_dir']
    out_file = cfg['output']
    out_path = os.path.join(work, out_file)

    if not os.path.exists(out_path):
        return {'ok': False, 'error': f'{out_file} introuvable. Buildez d\'abord.'}
    if not os.path.exists(os.path.join(gh, '.git')):
        return {'ok': False, 'error': f'Repo Git introuvable: {gh}'}

    # Copy output
    shutil.copy2(out_path, os.path.join(gh, out_file))
    copied = [out_file]

    # Copy index.html if exists
    idx = os.path.join(work, 'index.html')
    if os.path.exists(idx):
        shutil.copy2(idx, os.path.join(gh, 'index.html'))
        copied.append('index.html')

    # Git
    os.chdir(gh)
    subprocess.run(['git', 'add'] + copied, capture_output=True)
    diff = subprocess.run(['git', 'diff', '--cached', '--stat'], capture_output=True, text=True)
    if not diff.stdout.strip():
        return {'ok': True, 'message': 'Aucun changement à publier', 'copied': copied}

    dt = datetime.now().strftime('%Y-%m-%d %H:%M')
    subprocess.run(['git', 'commit', '-m', f'{cfg["project_name"]} update {dt}'], capture_output=True)
    push = subprocess.run(['git', 'push'], capture_output=True, text=True)
    if push.returncode != 0:
        return {'ok': False, 'error': f'git push failed: {push.stderr}'}

    return {'ok': True, 'message': 'Publié sur GitHub !', 'copied': copied}

# ── MODULES LIST ──
def list_modules():
    cfg = load_config()
    mdir = os.path.join(cfg['work_dir'], cfg['modules_dir'])
    if not os.path.exists(mdir):
        return {'ok': False, 'error': f'Dossier modules introuvable: {mdir}'}

    modules = []
    for f in sorted(os.listdir(mdir)):
        fp = os.path.join(mdir, f)
        if os.path.isfile(fp):
            stat = os.stat(fp)
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                first_lines = fh.read(500)
            # Detect type
            ext = f.rsplit('.', 1)[-1] if '.' in f else ''
            # Detect version
            ver_m = re.search(r'v[\d.]+', first_lines)
            modules.append({
                'name': f,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                'type': ext,
                'version': ver_m.group(0) if ver_m else '',
                'lines': first_lines.count('\n') + (stat.st_size // 40),  # approx
            })

    return {'ok': True, 'modules': modules, 'count': len(modules)}

# ── READ / WRITE MODULE ──
def read_module(name):
    cfg = load_config()
    fp = os.path.join(cfg['work_dir'], cfg['modules_dir'], name)
    if not os.path.exists(fp):
        return {'ok': False, 'error': f'Module introuvable: {name}'}
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    return {'ok': True, 'name': name, 'content': content}

def write_module(name, content):
    cfg = load_config()
    fp = os.path.join(cfg['work_dir'], cfg['modules_dir'], name)
    # Backup
    if os.path.exists(fp):
        bak = fp + '.bak'
        shutil.copy2(fp, bak)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    return {'ok': True, 'name': name, 'size': len(content)}

def delete_module(name):
    cfg = load_config()
    fp = os.path.join(cfg['work_dir'], cfg['modules_dir'], name)
    if not os.path.exists(fp):
        return {'ok': False, 'error': f'Module introuvable: {name}'}
    os.remove(fp)
    return {'ok': True, 'name': name}

# ── SKELETON ──
def read_skeleton():
    cfg = load_config()
    fp = os.path.join(cfg['work_dir'], cfg['skeleton'])
    if not os.path.exists(fp):
        return {'ok': False, 'error': 'skeleton introuvable'}
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    return {'ok': True, 'content': content}

def write_skeleton(content):
    cfg = load_config()
    fp = os.path.join(cfg['work_dir'], cfg['skeleton'])
    if os.path.exists(fp):
        shutil.copy2(fp, fp + '.bak')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    return {'ok': True}

# ── OPEN IN BROWSER ──
def do_open_browser():
    cfg = load_config()
    out_path = os.path.join(cfg['work_dir'], cfg['output'])
    if not os.path.exists(out_path):
        return {'ok': False, 'error': 'Fichier output introuvable. Buildez d\'abord.'}
    url = 'file://' + os.path.abspath(out_path)
    try:
        subprocess.Popen([cfg['browser'], url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        webbrowser.open(url)
    return {'ok': True, 'url': url}

# ── APPLY PATCH ZIP ──
def do_apply_patch(zip_path):
    cfg = load_config()
    mdir = os.path.join(cfg['work_dir'], cfg['modules_dir'])
    if not os.path.exists(zip_path):
        return {'ok': False, 'error': f'Zip introuvable: {zip_path}'}
    result = subprocess.run(['unzip', '-o', zip_path, '-d', mdir], capture_output=True, text=True)
    if result.returncode != 0:
        return {'ok': False, 'error': result.stderr}
    return {'ok': True, 'message': f'Patch appliqué dans {mdir}'}

# ── RUN SHELL ──
def do_shell(cmd):
    cfg = load_config()
    try:
        r = subprocess.run(cmd, shell=True, cwd=cfg['work_dir'],
                          capture_output=True, text=True, timeout=30)
        return {'ok': True, 'stdout': r.stdout, 'stderr': r.stderr, 'code': r.returncode}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))

        if path == '/':
            # Serve the UI
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_ui.html')
            if os.path.exists(ui_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(ui_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                err_json(self, 'modular_ui.html introuvable', 404)
            return

        if path == '/api/config':
            ok_json(self, load_config())
        elif path == '/api/modules':
            ok_json(self, list_modules())
        elif path == '/api/module':
            ok_json(self, read_module(params.get('name', '')))
        elif path == '/api/skeleton':
            ok_json(self, read_skeleton())
        elif path == '/api/build':
            ok_json(self, do_build())
        elif path == '/api/publish':
            ok_json(self, do_publish())
        elif path == '/api/test':
            ok_json(self, do_open_browser())
        else:
            err_json(self, 'Route inconnue', 404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}
        path = self.path

        if path == '/api/config':
            cfg = load_config()
            cfg.update(body)
            save_config(cfg)
            ok_json(self, cfg)
        elif path == '/api/module':
            ok_json(self, write_module(body.get('name', ''), body.get('content', '')))
        elif path == '/api/module/delete':
            ok_json(self, delete_module(body.get('name', '')))
        elif path == '/api/skeleton':
            ok_json(self, write_skeleton(body.get('content', '')))
        elif path == '/api/shell':
            ok_json(self, do_shell(body.get('cmd', '')))
        elif path == '/api/patch':
            ok_json(self, do_apply_patch(body.get('zip_path', '')))
        elif path == '/api/build-publish':
            r1 = do_build()
            if not r1['ok']:
                ok_json(self, r1)
                return
            r2 = do_publish()
            ok_json(self, {
                'ok': r2['ok'],
                'build': r1,
                'publish': r2
            })
        elif path == '/api/build-test':
            r1 = do_build()
            if not r1['ok']:
                ok_json(self, r1)
                return
            r2 = do_open_browser()
            ok_json(self, {'ok': True, 'build': r1, 'test': r2})
        elif path == '/api/build-publish-test':
            r1 = do_build()
            if not r1['ok']:
                ok_json(self, r1)
                return
            r2 = do_publish()
            r3 = do_open_browser()
            ok_json(self, {'ok': True, 'build': r1, 'publish': r2, 'test': r3})
        else:
            err_json(self, 'Route inconnue', 404)

    def log_message(self, format, *args):
        # Silence les logs HTTP normaux
        pass


if __name__ == '__main__':
    save_config(CFG)  # S'assurer que le fichier config existe
    print()
    print('╔══════════════════════════════════════════════════════════╗')
    print('║  ModularBuilder — Serveur local                        ║')
    print(f'║  http://{HOST}:{PORT}                                   ║')
    print('║  Ctrl+C pour arrêter                                   ║')
    print('╚══════════════════════════════════════════════════════════╝')
    print()
    print(f'  Projet : {CFG["project_name"]}')
    print(f'  Dossier : {CFG["work_dir"]}')
    print()

    # Ouvrir le navigateur
    webbrowser.open(f'http://{HOST}:{PORT}')

    server = http.server.HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Arrêt du serveur.')
        server.server_close()
