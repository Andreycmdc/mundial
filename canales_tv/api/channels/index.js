const API_BASE = 'https://www.noveopartidos.xyz';

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Referer');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/channels`, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
                'Referer': `${API_BASE}/`,
            }
        });
        const data = await response.arrayBuffer();
        res.setHeader('Content-Type', 'application/json');
        res.status(response.status).send(Buffer.from(data));
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
}

export const config = { api: { bodyParser: false, responseLimit: false } };
