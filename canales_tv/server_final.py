#!/usr/bin/env python3
"""
Servidor de Canales Deportivos
Con todos los canales desde la API real
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import urllib.parse
import os 

# Configuración
API_BASE = "https://www.noveopartidos.xyz"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

class ProxyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(f"📡 {self.path[:80]}")
        
        # Servir el HTML
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
            return
        
        # API: Lista de canales (desde la API real)
        if self.path == '/api/channels':
            try:
                headers = HEADERS.copy()
                headers['Referer'] = f'{API_BASE}/'
                resp = requests.get(f'{API_BASE}/api/channels', headers=headers, timeout=10)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp.content)
                print(f"   ✅ Canales: {len(resp.content)} bytes")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.send_response(500)
                self.end_headers()
            return
        
        # API: Stream (devuelve .m3u8)
        if self.path.startswith('/api/stream/'):
            channel = self.path.split('/')[-1].split('?')[0]
            print(f"🎬 Stream solicitado: {channel}")
            
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
                resp = requests.get(full_url, headers=headers, timeout=15)
                
                self.send_response(resp.status_code)
                self.send_header('Content-Type', 'video/mp2t')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp.content)
                print(f"   ✅ Segmento: {len(resp.content)} bytes")
            except Exception as e:
                print(f"   ❌ Error segmento: {e}")
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>Canales Deportivos EN VIVO - Mundial 2026</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #0a0a0a;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #fff;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #e50914;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 1.8rem;
        }
        
        .header h1 span {
            color: #e50914;
        }
        
        .header p {
            color: #888;
            font-size: 12px;
            margin-top: 5px;
        }
        
        /* Buscador */
        .search-box {
            max-width: 400px;
            margin: 15px auto 0;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 20px;
            border: none;
            border-radius: 30px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 16px;
            outline: none;
            text-align: center;
        }
        
        .search-box input::placeholder {
            color: #aaa;
        }
        
        /* Filtros */
        .filters {
            display: flex;
            gap: 8px;
            padding: 12px 20px;
            overflow-x: auto;
            background: #0f0f0f;
            border-bottom: 1px solid #222;
            position: sticky;
            top: 120px;
            z-index: 99;
        }
        
        .filter-btn {
            padding: 8px 18px;
            border-radius: 30px;
            border: none;
            background: #1f1f1f;
            color: #ccc;
            cursor: pointer;
            font-size: 13px;
            white-space: nowrap;
            transition: 0.3s;
        }
        
        .filter-btn:hover {
            background: #333;
        }
        
        .filter-btn.active {
            background: #e50914;
            color: #fff;
        }
        
        /* Grid de canales */
        .channel-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 16px;
            padding: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .channel-card {
            background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
            border-radius: 12px;
            padding: 20px 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid #2a2a2a;
        }
        
        .channel-card:hover {
            transform: translateY(-5px);
            border-color: #e50914;
            box-shadow: 0 10px 25px rgba(229, 9, 20, 0.2);
        }
        
        .channel-logo {
            width: 80px;
            height: 80px;
            margin: 0 auto 12px;
        }
        
        .channel-icon {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: bold;
            margin: 0 auto;
        }
        
        .channel-name {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .channel-country {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
        }
        
        .live-badge {
            background: #e50914;
            color: #fff;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            display: inline-block;
            margin-top: 8px;
        }
        
        /* Reproductor flotante */
        .player-overlay {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 450px;
            max-width: calc(100vw - 40px);
            background: #111;
            border-radius: 16px;
            border: 1px solid #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 1000;
            display: none;
            flex-direction: column;
            backdrop-filter: blur(10px);
        }
        
        .player-overlay.active {
            display: flex;
        }
        
        .player-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #1a1a1a;
            border-radius: 16px 16px 0 0;
            border-bottom: 1px solid #333;
        }
        
        .player-header h4 {
            font-size: 14px;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .close-player {
            background: none;
            border: none;
            color: #fff;
            font-size: 20px;
            cursor: pointer;
            padding: 0 8px;
        }
        
        .close-player:hover {
            color: #e50914;
        }
        
        .video-wrapper {
            background: #000;
            border-radius: 0 0 16px 16px;
            overflow: hidden;
        }
        
        video {
            width: 100%;
            display: block;
            max-height: 280px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #888;
        }
        
        .status {
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: #0f0;
            font-size: 11px;
            padding: 5px 10px;
            border-radius: 5px;
            font-family: monospace;
            z-index: 1001;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .channel-grid {
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 12px;
                padding: 16px;
            }
            .channel-icon {
                width: 60px;
                height: 60px;
                font-size: 22px;
            }
            .channel-name {
                font-size: 12px;
            }
            .player-overlay {
                width: 100%;
                bottom: 0;
                right: 0;
                border-radius: 16px 16px 0 0;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><span>🎥</span> Canales Deportivos <span>EN VIVO</span></h1>
        <p>ESPN | Fox Sports | TNT Sports | TyC Sports | Mundial 2026</p>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Buscar canal...">
        </div>
    </div>
    
    <div class="filters" id="filters">
        <button class="filter-btn active" data-filter="all">📺 Todos</button>
        <button class="filter-btn" data-filter="us">🇺🇸 USA</button>
        <button class="filter-btn" data-filter="mx">🇲🇽 México</button>
        <button class="filter-btn" data-filter="ar">🇦🇷 Argentina</button>
        <button class="filter-btn" data-filter="cl">🇨🇱 Chile</button>
        <button class="filter-btn" data-filter="pe">🇵🇪 Perú</button>
        <button class="filter-btn" data-filter="es">🇪🇸 España</button>
        <button class="filter-btn" data-filter="worldcup">🏆 Mundial 2026</button>
    </div>
    
    <div class="channel-grid" id="channelGrid">
        <div class="loading">📡 Cargando canales...</div>
    </div>
    
    <div class="player-overlay" id="playerOverlay">
        <div class="player-header">
            <h4 id="playerTitle">Cargando stream...</h4>
            <button class="close-player" id="closePlayer">✕</button>
        </div>
        <div class="video-wrapper">
            <video id="videoPlayer" controls autoplay></video>
        </div>
    </div>
    
    <div class="status" id="status">🟢 Iniciado</div>

    <script>
        let channels = [];
        let currentFilter = 'all';
        let currentSearch = '';
        let currentHls = null;
        
        const colors = ['#e50914', '#00a650', '#004A98', '#ff8c00', '#9b59b6', '#3498db', '#1abc9c', '#e67e22', '#2c3e50', '#f39c12'];
        
        function setStatus(msg) {
            const statusEl = document.getElementById('status');
            statusEl.innerHTML = msg;
            console.log(msg);
        }
        
        // Cargar canales desde la API
        async function loadChannels() {
            setStatus('📡 Cargando canales...');
            try {
                const response = await fetch('/api/channels');
                channels = await response.json();
                setStatus(`✅ ${channels.length} canales cargados`);
                renderChannels();
            } catch (error) {
                setStatus(`❌ Error: ${error.message}`);
                document.getElementById('channelGrid').innerHTML = `<div class="loading">❌ Error al cargar canales</div>`;
            }
        }
        
        // Renderizar canales
        function renderChannels() {
            let filtered = channels.filter(channel => {
                if (currentFilter === 'worldcup') return channel.worldcup === true;
                if (currentFilter !== 'all') return channel.country === currentFilter;
                return true;
            });
            
            if (currentSearch) {
                filtered = filtered.filter(channel => 
                    channel.name.toLowerCase().includes(currentSearch.toLowerCase())
                );
            }
            
            const grid = document.getElementById('channelGrid');
            
            if (filtered.length === 0) {
                grid.innerHTML = '<div class="loading">📺 No se encontraron canales</div>';
                return;
            }
            
            const countryFlags = {
                'us': '🇺🇸', 'mx': '🇲🇽', 'ar': '🇦🇷', 'cl': '🇨🇱',
                'pe': '🇵🇪', 'es': '🇪🇸', 'gb': '🇬🇧', 'ca': '🇨🇦'
            };
            
            grid.innerHTML = filtered.map((channel, index) => {
                const color = colors[Math.abs(channel.id.length % colors.length)];
                return `
                    <div class="channel-card" data-id="${channel.id}" data-name="${channel.name}">
                        <div class="channel-logo">
                            <div class="channel-icon" style="background:${color}">${channel.name.substring(0,2).toUpperCase()}</div>
                        </div>
                        <div class="channel-name">${channel.name} ${channel.worldcup ? '🏆' : ''}</div>
                        <div class="channel-country">${countryFlags[channel.country] || '🌎'} ${channel.country?.toUpperCase() || ''}</div>
                        <div class="live-badge">🔴 EN VIVO</div>
                    </div>
                `;
            }).join('');
            
            // Agregar eventos
            document.querySelectorAll('.channel-card').forEach(card => {
                card.addEventListener('click', () => {
                    playChannel(card.dataset.id, card.dataset.name);
                });
            });
        }
        
        // Reproducir canal
        async function playChannel(channelId, channelName) {
            const overlay = document.getElementById('playerOverlay');
            const title = document.getElementById('playerTitle');
            const video = document.getElementById('videoPlayer');
            
            if (currentHls) {
                currentHls.destroy();
                currentHls = null;
            }
            
            title.textContent = `${channelName} - Cargando...`;
            overlay.classList.add('active');
            video.pause();
            video.src = '';
            
            setStatus(`🎬 ${channelName} - Solicitando stream...`);
            
            const streamUrl = `/api/stream/${channelId}?target=1`;
            
            if (Hls.isSupported()) {
                currentHls = new Hls({
                    manifestLoadingTimeOut: 30000,
                    levelLoadingTimeOut: 30000,
                    fragLoadingTimeOut: 30000,
                });
                currentHls.loadSource(streamUrl);
                currentHls.attachMedia(video);
                currentHls.on(Hls.Events.MANIFEST_PARSED, () => {
                    title.textContent = `${channelName} - EN VIVO`;
                    setStatus(`✅ ${channelName} - Reproduciendo`);
                    video.play().catch(e => console.log('Autoplay:', e));
                });
                currentHls.on(Hls.Events.ERROR, (event, data) => {
                    if (data.fatal) {
                        setStatus(`❌ ${channelName} - Error, reintentando...`);
                        setTimeout(() => playChannel(channelId, channelName), 3000);
                    }
                });
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                video.src = streamUrl;
                video.addEventListener('loadedmetadata', () => {
                    title.textContent = `${channelName} - EN VIVO`;
                    setStatus(`✅ ${channelName} - Reproduciendo`);
                    video.play();
                });
            } else {
                setStatus(`❌ ${channelName} - HLS no soportado`);
                title.textContent = `${channelName} - Error`;
            }
        }
        
        // Cerrar reproductor
        document.getElementById('closePlayer').addEventListener('click', () => {
            const overlay = document.getElementById('playerOverlay');
            const video = document.getElementById('videoPlayer');
            if (currentHls) {
                currentHls.destroy();
                currentHls = null;
            }
            video.pause();
            video.src = '';
            overlay.classList.remove('active');
            setStatus('🟢 Reproductor cerrado');
        });
        
        // Búsqueda en vivo
        document.getElementById('searchInput').addEventListener('input', (e) => {
            currentSearch = e.target.value.toLowerCase();
            renderChannels();
        });
        
        // Filtros
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.filter;
                renderChannels();
            });
        });
        
        // Iniciar
        loadChannels();
    </script>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def log_message(self, *args):
        pass

port = int(os.environ.get('PORT', 8888))
print(f"🎥 Servidor iniciado en puerto {port}")
HTTPServer(('0.0.0.0', port), ProxyHandler).serve_forever()
