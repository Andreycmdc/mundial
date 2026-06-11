#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import urllib.parse

# Configuración
API_BASE = "https://www.noveopartidos.xyz"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Lista de canales (precargada)
CHANNELS = [
    {"id":"espn","name":"ESPN","country":"us","worldcup":True},
    {"id":"espn2","name":"ESPN 2","country":"us","worldcup":True},
    {"id":"espn3","name":"ESPN 3","country":"us","worldcup":True},
    {"id":"foxsports","name":"Fox Sports","country":"us","worldcup":True},
    {"id":"foxsports2","name":"Fox Sports 2","country":"us","worldcup":True},
    {"id":"tntsportsar","name":"TNT Sports Argentina","country":"ar","worldcup":True},
    {"id":"tycsports","name":"TyC Sports","country":"ar","worldcup":True},
    {"id":"espnmexico","name":"ESPN Mexico","country":"mx","worldcup":True},
]

class ProxyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(f"📡 {self.path[:80]}")
        
        # Servir el HTML
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
            return
        
        # API: Lista de canales
        if self.path == '/api/channels':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(CHANNELS).encode())
            return
        
        # API: Stream (devuelve .m3u8)
        if self.path.startswith('/api/stream/'):
            channel = self.path.split('/')[-1].split('?')[0]
            print(f"🎬 Solicitando stream: {channel}")
            
            try:
                headers = HEADERS.copy()
                headers['Referer'] = f'{API_BASE}/ver/{channel}'
                
                resp = requests.get(f'{API_BASE}/api/stream/{channel}?target=1', 
                                   headers=headers, timeout=10)
                
                self.send_response(resp.status_code)
                self.send_header('Content-Type', 'application/vnd.apple.mpegurl')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp.content)
                print(f"   ✅ .m3u8 enviado")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.send_response(500)
                self.end_headers()
            return
        
        # Proxy para segmentos de video
        if self.path.startswith('/api/segment'):
            try:
                headers = HEADERS.copy()
                headers['Referer'] = f'{API_BASE}/ver/espn'
                
                full_url = f'{API_BASE}{self.path}'
                print(f"   📥 Proxy segmento")
                
                resp = requests.get(full_url, headers=headers, timeout=15)
                
                self.send_response(resp.status_code)
                self.send_header('Content-Type', 'video/mp2t')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp.content)
                print(f"   ✅ Enviado: {len(resp.content)} bytes")
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
        body{background:#0a0a0a;font-family:Arial,sans-serif;color:#fff;}
        .header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px;text-align:center;border-bottom:3px solid #e50914;position:sticky;top:0;z-index:100;}
        .header h1{font-size:1.5rem;}
        .header h1 span{color:#e50914;}
        .search{padding:10px;background:#0f0f0f;}
        .search input{width:100%;padding:12px;border-radius:30px;background:#1f1f1f;color:#fff;border:none;text-align:center;font-size:14px;}
        .filters{display:flex;gap:8px;padding:10px;overflow-x:auto;background:#0a0a0a;}
        .filter{padding:6px 15px;border-radius:20px;background:#1f1f1f;color:#aaa;border:none;cursor:pointer;white-space:nowrap;}
        .filter.active{background:#e50914;color:#fff;}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;padding:16px;}
        .card{background:#1a1a1a;border-radius:12px;padding:15px;text-align:center;cursor:pointer;border:1px solid #333;transition:0.2s;}
        .card:hover{transform:translateY(-3px);border-color:#e50914;}
        .logo{width:70px;height:70px;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;}
        .name{font-size:13px;font-weight:600;}
        .country{font-size:10px;color:#888;margin-top:4px;}
        .player{position:fixed;bottom:0;left:0;right:0;background:#000;z-index:200;display:none;flex-direction:column;border-top:2px solid #e50914;}
        .player.active{display:flex;}
        .player-bar{display:flex;justify-content:space-between;align-items:center;padding:10px 15px;background:#111;}
        .player-bar h4{font-size:14px;}
        .player-bar button{background:#e50914;border:none;color:#fff;padding:5px 15px;border-radius:20px;cursor:pointer;}
        video{width:100%;max-height:40vh;background:#000;}
        .loading{text-align:center;padding:40px;color:#666;}
        .status{position:fixed;bottom:60px;right:10px;background:#000;color:#0f0;font-size:10px;padding:5px 8px;border-radius:5px;z-index:210;font-family:monospace;}
    </style>
</head>
<body>
<div class="header"><h1><span>🎥</span> Canales Deportivos <span>EN VIVO</span></h1></div>
<div class="search"><input type="text" id="search" placeholder="🔍 Buscar canal..." id="searchInput"></div>
<div class="filters" id="filters">
    <button class="filter active" data-filter="all">📺 Todos</button>
    <button class="filter" data-filter="us">🇺🇸 USA</button>
    <button class="filter" data-filter="mx">🇲🇽 México</button>
    <button class="filter" data-filter="ar">🇦🇷 Argentina</button>
</div>
<div class="grid" id="grid"><div class="loading">📡 Cargando canales...</div></div>
<div class="player" id="player">
    <div class="player-bar"><h4 id="playerTitle">Cargando...</h4><button id="closePlayer">CERRAR ✕</button></div>
    <video id="video" controls autoplay></video>
</div>
<div class="status" id="status">⚡ Listo</div>

<script>
let hls = null;
let currentChannel = null;

const canales = ''' + json.dumps(CHANNELS) + ''';
let filtro = 'all';
let busqueda = '';

function setStatus(msg) {
    document.getElementById('status').innerHTML = msg;
    console.log(msg);
}

function renderCanales() {
    let filtrados = canales.filter(c => {
        if (filtro !== 'all' && c.country !== filtro) return false;
        if (busqueda && !c.name.toLowerCase().includes(busqueda.toLowerCase())) return false;
        return true;
    });
    const grid = document.getElementById('grid');
    if (filtrados.length === 0) {
        grid.innerHTML = '<div class="loading">📺 No hay canales</div>';
        return;
    }
    const colores = ['#e50914','#00a650','#004A98','#ff8c00','#9b59b6','#3498db'];
    const flags = {us:'🇺🇸',mx:'🇲🇽',ar:'🇦🇷',cl:'🇨🇱',pe:'🇵🇪',es:'🇪🇸'};
    grid.innerHTML = filtrados.map((c,i) => `
        <div class="card" onclick="reproducir('${c.id}','${c.name}')">
            <div class="logo" style="background:${colores[i%colores.length]}">${c.name.slice(0,2)}</div>
            <div class="name">${c.name}</div>
            <div class="country">${flags[c.country] || '🌎'} ${c.country?.toUpperCase() || ''}</div>
        </div>
    `).join('');
}

function reproducir(id, nombre) {
    const player = document.getElementById('player');
    const video = document.getElementById('video');
    const title = document.getElementById('playerTitle');
    
    if (hls) hls.destroy();
    video.pause();
    video.src = '';
    
    player.classList.add('active');
    title.innerText = `${nombre} - Conectando...`;
    setStatus(`🎬 ${nombre} - Solicitando...`);
    currentChannel = id;
    
    const streamUrl = `/api/stream/${id}?target=1`;
    
    if (Hls.isSupported()) {
        hls = new Hls({
            manifestLoadingTimeOut: 30000,
            levelLoadingTimeOut: 30000,
            fragLoadingTimeOut: 30000,
        });
        hls.loadSource(streamUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            title.innerText = `${nombre} - EN VIVO`;
            setStatus(`✅ ${nombre} - Reproduciendo`);
            video.play();
        });
        hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                setStatus(`❌ ${nombre} - Error, reintentando...`);
                setTimeout(() => reproducir(id, nombre), 3000);
            }
        });
    } else {
        setStatus(`❌ ${nombre} - HLS no soportado`);
    }
}

document.getElementById('closePlayer').onclick = () => {
    const player = document.getElementById('player');
    const video = document.getElementById('video');
    if (hls) hls.destroy();
    video.pause();
    video.src = '';
    player.classList.remove('active');
    setStatus('⚡ Listo');
};

document.getElementById('search').addEventListener('input', (e) => {
    busqueda = e.target.value;
    renderCanales();
});

document.querySelectorAll('.filter').forEach(btn => {
    btn.onclick = () => {
        document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filtro = btn.dataset.filter;
        renderCanales();
    };
});

renderCanales();
setStatus(`✅ ${canales.length} canales listos`);
</script>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, *args):
        pass

print("="*60)
print("🎥 SERVIDOR COMPLETO - http://localhost:8888")
print("="*60)
print("📺 Canales cargados:", len(CHANNELS))
print("🚀 Proxy activo - sin CORS")
print("="*60)
HTTPServer(('0.0.0.0', 8888), ProxyHandler).serve_forever()
