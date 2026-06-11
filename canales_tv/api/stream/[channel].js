const API_BASE = 'https://www.noveopartidos.xyz';

export default async function handler(req, res) {
    const { channel } = req.query;
    const target = req.query.target || 1;
    
    console.log('Channel:', channel);
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Referer');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    
    if (!channel) {
        return res.status(400).json({ error: 'Channel required' });
    }
    
    const url = `${API_BASE}/api/stream/${channel}?target=${target}`;
    console.log('Fetching:', url);
    
    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
                'Referer': `${API_BASE}/ver/${channel}`,
                'Accept': '*/*',
            }
        });
        const data = await response.arrayBuffer();
        const contentType = response.headers.get('Content-Type') || 'application/vnd.apple.mpegurl';
        res.setHeader('Content-Type', contentType);
        res.status(response.status).send(Buffer.from(data));
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
}

export const config = { api: { bodyParser: false, responseLimit: false } };
