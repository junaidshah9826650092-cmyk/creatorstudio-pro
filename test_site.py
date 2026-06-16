import os, requests, json

BASE_URL = 'http://127.0.0.1:5000'
ROOT = r'F:/vv'

# Collect all .html files in project root
html_files = [f for f in os.listdir(ROOT) if f.lower().endswith('.html')]

results = {}

# Test static HTML pages
for html in html_files:
    url = f"{BASE_URL}/{html}"
    try:
        r = requests.get(url, timeout=5)
        results[html] = r.status_code
    except Exception as e:
        results[html] = str(e)

# Test a few key API endpoints
api_tests = {
    'suggest': {'method': 'POST', 'endpoint': '/api/ai/suggest', 'json': {'topic': 'music'}},
    'moderate': {'method': 'POST', 'endpoint': '/api/video/moderate', 'json': {'title': 'Test', 'description': 'Test desc'}},
    'adsense': {'method': 'POST', 'endpoint': '/api/user/adsense', 'json': {'adsense_id': 'test'}},
    'brand_check': {'method': 'POST', 'endpoint': '/api/brand/check-eligibility', 'json': {'email': 'test@brand.com'}},
    'db_debug': {'method': 'GET', 'endpoint': '/api/debug/db'}
}

for name, cfg in api_tests.items():
    url = BASE_URL + cfg['endpoint']
    try:
        if cfg['method'] == 'GET':
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=cfg['json'], timeout=5)
        results[name] = {'status': r.status_code, 'body': r.json() if r.headers.get('Content-Type','').startswith('application/json') else r.text[:200]}
    except Exception as e:
        results[name] = str(e)

print(json.dumps(results, indent=2))
