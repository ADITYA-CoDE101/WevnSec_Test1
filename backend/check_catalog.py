"""Implemented scanner outputs, not an aspirational vulnerability count."""
CHECK_CATALOG = [
    {'id': 'TLS-01', 'title': 'TLS certificates and protocol', 'mode': 'instant'},
    {'id': 'NET-00', 'title': 'Website reachability', 'mode': 'instant'},
    {'id': 'NET-01', 'title': 'HTTPS availability', 'mode': 'instant'},
    {'id': 'NET-02', 'title': 'HTTP to HTTPS redirects', 'mode': 'instant'},
    {'id': 'HDR-strict', 'title': 'HTTP Strict Transport Security', 'mode': 'instant'},
    {'id': 'HDR-conten', 'title': 'Content Security Policy', 'mode': 'instant'},
    {'id': 'HDR-x-fram', 'title': 'Clickjacking protection', 'mode': 'instant'},
    {'id': 'HDR-x-cont', 'title': 'MIME sniffing protection', 'mode': 'instant'},
    {'id': 'HDR-referr', 'title': 'Referrer policy', 'mode': 'instant'},
    {'id': 'HDR-permis', 'title': 'Browser permissions policy', 'mode': 'instant'},
    {'id': 'HDR-SRV', 'title': 'Server fingerprint disclosure', 'mode': 'instant'},
    {'id': 'CK-01', 'title': 'Cookie security flags', 'mode': 'instant'},
    {'id': 'CORS-01', 'title': 'Cross-origin resource sharing', 'mode': 'instant'},
    {'id': 'LEAK-01', 'title': 'Exposed secrets and configuration', 'mode': 'advanced'},
]
CHECK_IDS = {item['id'] for item in CHECK_CATALOG}