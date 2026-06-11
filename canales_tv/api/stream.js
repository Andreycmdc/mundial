// Misma lógica que server.py pero en JavaScript para Vercel
const API_BASE = 'https://www.noveopartidos.xyz';
const HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
};

export default async function handler(req, res) {
    const url = req.url;
    console.log(`📡 ${url}`);
    
    // Configurar CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Referer');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    
    // API Canales
    if (url === '/api/channels' || url === '/api/stream?channels') {
        try {
            const response = await fetch(`${API_BASE}/api/channels`, {
                headers: {
                    ...HEADERS,
                    'Referer': `${API_BASE}/`
                }
            });
            const data = await response.text();
            res.setHeader('Content-Type', 'application/json');
            return res.status(response.status).send(data);
        } catch (error) {
            return res.status(500).json({ error: error.message });
        }
    }
    
    // API Stream
    if (url.includes('/api/stream/')) {
        const match = url.match(/\/api\/stream\/([^?]+)/);
        if (match) {
            const channel = match[1];
            console.log(`🎬 Stream solicitado: ${channel}`);
            try {
                const response = await fetch(`${API_BASE}/api/stream/${channel}?target=1`, {
                    headers: {
                        ...HEADERS,
                        'Referer': `${API_BASE}/ver/${channel}`
                    }
                });
                const data = await response.text();
                res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
                return res.status(response.status).send(data);
            } catch (error) {
                return res.status(500).json({ error: error.message });
            }
        }
    }
    
    // Proxy segmentos
    if (url.includes('/api/segment')) {
        try {
            const fullUrl = `${API_BASE}${url}`;
            console.log(`📥 Proxy segmento: ${fullUrl}`);
            const response = await fetch(fullUrl, {
                headers: {
                    ...HEADERS,
                    'Referer': `${API_BASE}/ver/espn`
                }
            });
            const buffer = await response.arrayBuffer();
            res.setHeader('Content-Type', 'video/mp2t');
            return res.status(response.status).send(Buffer.from(buffer));
        } catch (error) {
            return res.status(500).json({ error: error.message });
        }
    }
    
    res.status(404).json({ error: 'Not found' });
}

export const config = {
    api: {
        bodyParser: false,
        responseLimit: false,
    },
};
