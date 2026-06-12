const API_BASE = 'https://www.noveopartidos.xyz';

// Datos de respaldo en caso de que Cloudflare bloquee
const FALLBACK_CHANNELS = [
    {"id":"espn","name":"ESPN","country":"us","worldcup":true},
    {"id":"espn2","name":"ESPN 2","country":"us","worldcup":true},
    {"id":"espn3","name":"ESPN 3","country":"us","worldcup":true},
    {"id":"foxsports","name":"Fox Sports","country":"us","worldcup":true},
    {"id":"foxsports2","name":"Fox Sports 2","country":"us","worldcup":true},
    {"id":"tntsportsar","name":"TNT Sports Argentina","country":"ar","worldcup":true},
    {"id":"tycsports","name":"TyC Sports","country":"ar","worldcup":true},
    {"id":"espnmexico","name":"ESPN Mexico","country":"mx","worldcup":true},
    {"id":"foxsportsmexico","name":"Fox Sports Mexico","country":"mx","worldcup":true},
];

const HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Referer': 'https://www.noveopartidos.xyz/',
};

export default async function handler(req, res) {
    const url = req.url;
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Referer, User-Agent');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    
    // API Canales - con fallback
    if (url === '/api/channels' || url === '/api/stream?channels') {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 8000);
            
            const response = await fetch(`${API_BASE}/api/channels`, { 
                headers: HEADERS,
                signal: controller.signal 
            });
            clearTimeout(timeoutId);
            
            const data = await response.text();
            
            // Verificar si es HTML de Cloudflare
            if (data.includes('Just a moment') || data.includes('cf-challenge')) {
                console.log('Cloudflare detectado, usando fallback');
                res.setHeader('Content-Type', 'application/json');
                return res.status(200).json(FALLBACK_CHANNELS);
            }
            
            // Verificar si es JSON válido
            try {
                JSON.parse(data);
                res.setHeader('Content-Type', 'application/json');
                return res.status(response.status).send(data);
            } catch (e) {
                console.log('JSON inválido, usando fallback');
                return res.status(200).json(FALLBACK_CHANNELS);
            }
        } catch (error) {
            console.log('Error, usando fallback:', error.message);
            res.setHeader('Content-Type', 'application/json');
            return res.status(200).json(FALLBACK_CHANNELS);
        }
    }
    
    res.status(404).json({ error: 'Not found' });
}

export const config = {
    api: { bodyParser: false, responseLimit: false },
};
