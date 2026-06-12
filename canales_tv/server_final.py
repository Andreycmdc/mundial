#!/usr/bin/env python3
"""
Servidor de Canales Deportivos - CON BYPASS DE CLOUDFLARE
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import os
import time
import random

# Configuración
API_BASE = "https://www.noveopartidos.xyz"

# Múltiples User-Agents para rotar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
]

# Datos de respaldo (canales principales)
BACKUP_CHANNELS = [
    {"id":"espn","name":"ESPN","country":"us","worldcup":True},
    {"id":"espn2","name":"ESPN 2","country":"us","worldcup":True},
    {"id":"espn3","name":"ESPN 3","country":"us","worldcup":True},
    {"id":"foxsports","name":"Fox Sports","country":"us","worldcup":True},
    {"id":"foxsports2","name":"Fox Sports 2","country":"us","worldcup":True},
    {"id":"tntsportsar","name":"TNT Sports Argentina","country":"ar","worldcup":True},
    {"id":"tycsports","name":"TyC Sports","country":"ar","worldcup":True},
    {"id":"espnmexico","name":"ESPN Mexico","country":"mx","worldcup":True},
    {"id":"foxsportsmexico","name":"Fox Sports Mexico","country":"mx","worldcup":True},
]

def get_headers(referer=None):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    if referer:
        headers['Referer'] = referer
    return headers

def fetch_with_retry(url, headers, max_retries=3):
    for i in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                # Verificar que no sea página de Cloudflare
                if 'Just a moment' in resp.text or 'cf-challenge' in resp.text:
                    print(f"   ⚠️ Cloudflare detectado, reintento {i+1}/{max_retries}")
                    time.sleep(2)
                    continue
                return resp
            elif resp.status_code == 403:
                print(f"   ⚠️ 403 detectado, reintento {i+1}/{max_retries}")
                time.sleep(2)
                continue
        except Exception as e:
            print(f"   ❌ Error: {e}, reintento {i+1}/{max_retries}")
            time.sleep(2)
    return None

class ProxyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(f"📡 {self.path[:80]}")
        
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
            return
        
        # API Canales con bypass
        if self.path == '/api/channels':
            try:
                headers = get_headers(f'{API_BASE}/')
                resp = fetch_with_retry(f'{API_BASE}/api/channels', headers)
                
                if resp and resp.status_code == 200:
                    # Verificar que es JSON válido
                    try:
                        json.loads(resp.text)
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(resp.content)
                        print(f"   ✅ Canales: {len(resp.content)} bytes")
                        return
                    except:
                        print(f"   ⚠️ JSON inválido, usando backup")
                else:
                    print(f"   ⚠️ Fallo en API, usando backup")
                    
                # Fallback a datos locales
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(BACKUP_CHANNELS).encode())
                print(f"   ✅ Usando backup: {len(BACKUP_CHANNELS)} canales")
                
            except Exception as e:
                print(f"   ❌ Error: {e}, usando backup")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(BACKUP_CHANNELS).encode())
            return
        
        # API Stream
        if self.path.startswith('/api/stream/'):
            channel = self.path.split('/')[-1].split('?')[0]
            print(f"🎬 Stream: {channel}")
            
            try:
                headers = get_headers(f'{API_BASE}/ver/{channel}')
                resp = fetch_with_retry(f'{API_BASE}/api/stream/{channel}?target=1', headers)
                
                if resp and resp.status_code == 200:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(resp.content)
                    print(f"   ✅ .m3u8 enviado")
                else:
                    self.send_response(503)
                    self.end_headers()
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.send_response(500)
                self.end_headers()
            return
        
        # Proxy segmentos
        if self.path.startswith('/api/segment'):
            try:
                headers = get_headers(f'{API_BASE}/ver/espn')
                full_url = f'{API_BASE}{self.path}'
                resp = fetch_with_retry(full_url, headers)
                
                if resp and resp.status_code == 200:
                    self.send_response(200)
                    self.send_header('Content-Type', 'video/mp2t')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(resp.content)
                    print(f"   ✅ Segmento: {len(resp.content)} bytes")
                else:
                    self.send_response(503)
                    self.end_headers()
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.send_response(500)
                self.end_headers()
            return
        
        self.send_response(404)
        self.end_headers()
    
    def serve_html(self):
        html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canales Deportivos EN VIVO</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{background:#0a0a0a;font-family:Arial;color:#fff;}
        .header{background:#1a1a2e;padding:20px;text-align:center;border-bottom:3px solid #e50914;}
        h1{font-size:1.5rem;}
        span{color:#e50914;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:12px;padding:20px;}
        .card{background:#1a1a1a;border-radius:12px;padding:15px;text-align:center;cursor:pointer;border:1px solid #333;}
        .card:hover{transform:scale(1.02);border-color:#e50914;}
        .logo{width:65px;height:65px;border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;}
        .player{position:fixed;bottom:0;left:0;right:0;background:#000;z-index:20;display:none;flex-direction:column;border-top:2px solid #e50914;}
        .player.active{display:flex;}
        .player-bar{display:flex;justify-content:space-between;padding:10px;background:#111;}
        .player-bar button{background:#e50914;border:none;color:#fff;padding:5px 15px;border-radius:20px;cursor:pointer;}
        video{width:100%;max-height:50vh;}
        .status{position:fixed;bottom:10px;right:10px;background:#000;color:#0f0;font-size:10px;padding:5px;border-radius:5px;}
        .live{color:#e50914;font-size:10px;margin-top:5px;display:inline-block;}
    </style>
</head>
<body>
<div class="header"><h1><span>🎥</span> Canales Deportivos <span>EN VIVO</span></h1></div>
<div class="grid" id="grid"><div class="loading" style="text-align:center;padding:40px">📡 Cargando canales...</div></div>
<div class="player" id="player">
    <div class="player-bar"><span id="playerTitle">Cargando...</span><button id="closeBtn">CERRAR</button></div>
    <video id="video" controls autoplay></video>
</div>
<div class="status" id="status">⚡ Listo</div>
<script>
let canales=[],hls=null;
async function cargarCanales(){
    try{
        const r=await fetch('/api/channels');
        canales=await r.json();
        const grid=document.getElementById('grid');
        const colores=['#e50914','#00a650','#004A98','#ff8c00','#9b59b6','#3498db'];
        grid.innerHTML=canales.map((c,i)=>`
            <div class="card" onclick="reproducir('${c.id}')">
                <div class="logo" style="background:${colores[i%colores.length]}">${c.name.slice(0,2)}</div>
                <div class="name">${c.name}</div>
                <div class="live">🔴 EN VIVO</div>
            </div>
        `).join('');
        document.getElementById('status').innerHTML='✅ '+canales.length+' canales';
    }catch(e){grid.innerHTML='<div style="text-align:center;padding:40px">❌ Error al cargar</div>';}
}
function reproducir(id){
    const player=document.getElementById('player');
    const video=document.getElementById('video');
    if(hls)hls.destroy();
    player.classList.add('active');
    video.pause();
    const url=`/api/stream/${id}?target=1`;
    if(Hls.isSupported()){
        hls=new Hls();
        hls.loadSource(url);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED,()=>video.play());
    }
}
document.getElementById('closeBtn').onclick=()=>{
    document.getElementById('player').classList.remove('active');
    if(hls)hls.destroy();
    document.getElementById('video').pause();
};
cargarCanales();
</script>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    print("="*60)
    print("🎥 SERVIDOR CON BYPASS DE CLOUDFLARE")
    print("="*60)
    print(f"📺 Puerto: {port}")
    print(f"📡 User-Agents: {len(USER_AGENTS)} rotativos")
    print(f"💾 Backup: {len(BACKUP_CHANNELS)} canales")
    print("="*60)
    HTTPServer(('0.0.0.0', port), ProxyHandler).serve_forever()
