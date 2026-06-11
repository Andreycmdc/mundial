const API_BASE = 'https://www.noveopartidos.xyz';

export default async function handler(req, res) {
    const { path } = req.query;
    
    // Configurar CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Referer');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    
    let url;
    let refererChannel = 'espn';
    
    // Si es /api/channels
    if (path && path[0] === 'channels') {
        url = `${API_BASE}/api/channels`;
    }
    // Si es /api/stream/espn
    else if (path && path[0]) {
        refererChannel = path[0];
        const target = req.query.target || 1;
        url = `${API_BASE}/api/stream/${path[0]}?target=${target}`;
    }
    // Por defecto
    else {
        url = `${API_BASE}/api/channels`;
    }
    
    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
                'Referer': `${API_BASE}/ver/${refererChannel}`,
                'Accept': '*/*',
            }
        });
        
        const data = await response.arrayBuffer();
        const contentType = response.headers.get('Content-Type') || 
                           (url.includes('channels') ? 'application/json' : 'application/vnd.apple.mpegurl');
        
        res.setHeader('Content-Type', contentType);
        res.status(response.status).send(Buffer.from(data));
    } catch (error) {
        res.status(500).json({ error: 'Proxy error: ' + error.message });
    }
}

export const config = {
    api: {
        bodyParser: false,
        responseLimit: false,
    },
};
