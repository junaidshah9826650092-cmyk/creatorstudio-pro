import urllib.request

try:
    req = urllib.request.urlopen('http://localhost:5000/rules.html', timeout=5)
    content = req.read().decode('utf-8', errors='ignore')
    print('STATUS:', req.status)
    print('CONTENT LENGTH:', len(content), 'bytes')
    print()

    checks = [
        ('Spine div',          'class="spine"'),
        ('Page-edge div',      'class="page-edge"'),
        ('Book-wrapper',       'class="book-wrapper"'),
        ('Leather cover CSS',  'front.cover'),
        ('15 page z-index',    'nth-child(15)'),
        ('TOTAL=14',           'TOTAL = 14'),
        ('flip() function',    'function flip'),
        ('Red Zone page',      'RED ZONE'),
        ('Claim reward btn',   'claimBtn'),
        ('Quiz buttons',       'class="qbtn"'),
        ('Privacy rules pg',   'PRIVACY RULES'),
        ('Premium rules pg',   'PREMIUM RULES'),
        ('Enforcement board',  'VITOX MONITORING BOARD'),
        ('Back cover FINIS',   'FINIS'),
        ('Paper texture SVG',  'fractalNoise'),
        ('Mouse parallax',     'mousemove'),
        ('Appeal system',      'APPEALS'),
    ]

    all_ok = True
    for name, token in checks:
        found = token in content
        status = 'OK' if found else 'MISSING'
        if not found:
            all_ok = False
        print(f'  [{status:7}] {name}')

    print()
    if all_ok:
        print('ALL CHECKS PASSED - Rule book is complete!')
    else:
        print('SOME ELEMENTS MISSING - Check above')

except Exception as e:
    print('ERROR connecting to server:', e)
    print('Make sure server.py is running on port 5000')
