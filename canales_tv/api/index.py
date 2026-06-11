#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
import urllib.parse

API_BASE = "https://www.noveopartidos.xyz"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

def handler(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    headers_response = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Referer',
    }
    
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers_response, 'body': ''}
    
    # Servir HTML
    if path == '/' or path == '/index.html':
        with open('index.html', 'r') as f:
            return {'statusCode': 200, 'headers': {'Content-Type': 'text/html'}, 'body': f.read()}
    
    # API Canales
    if path == '/api/channels':
        try:
            headers = HEADERS.copy()
            headers['Referer'] = f'{API_BASE}/'
            resp = requests.get(f'{API_BASE}/api/channels', headers=headers, timeout=10)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', **headers_response},
                'body': resp.text
            }
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    
    # API Stream
    if path.startswith('/api/stream/'):
        channel = path.split('/')[-1].split('?')[0]
        try:
            headers = HEADERS.copy()
            headers['Referer'] = f'{API_BASE}/ver/{channel}'
            resp = requests.get(f'{API_BASE}/api/stream/{channel}?target=1', headers=headers, timeout=10)
            return {
                'statusCode': resp.status_code,
                'headers': {'Content-Type': 'application/vnd.apple.mpegurl', **headers_response},
                'body': resp.text,
                'isBase64Encoded': False
            }
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    
    # Proxy segmentos
    if path.startswith('/api/segment'):
        try:
            headers = HEADERS.copy()
            headers['Referer'] = f'{API_BASE}/ver/espn'
            full_url = f'{API_BASE}{path}'
            if event.get('queryStringParameters'):
                full_url += '?' + urllib.parse.urlencode(event['queryStringParameters'])
            resp = requests.get(full_url, headers=headers, timeout=15)
            return {
                'statusCode': resp.status_code,
                'headers': {'Content-Type': 'video/mp2t', **headers_response},
                'body': resp.content,
                'isBase64Encoded': True
            }
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    
    return {'statusCode': 404, 'body': 'Not found'}
