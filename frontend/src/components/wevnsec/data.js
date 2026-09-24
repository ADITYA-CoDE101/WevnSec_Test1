export const CHECKS = [
    { id: "CHK-01", name: "TLS Certificate & Cipher Suite", category: "SSL/TLS", status: "PASS", latency: "14ms", details: "TLS 1.3 enforced, HSTS preload active (31536000s)" },
    { id: "CHK-02", name: "HTTP Security Headers", category: "HEADERS", status: "WARN", latency: "38ms", details: "CSP missing report-uri; X-Frame-Options set to SAMEORIGIN" },
    { id: "CHK-03", name: "Reflected DOM & Stored XSS Surfaces", category: "XSS", status: "PASS", latency: "112ms", details: "No dangerous innerHTML sinks across 43 analyzed scripts" },
    { id: "CHK-04", name: "Exposed Secrets & .env Probes", category: "ENV_LEAK", status: "FAIL", latency: "22ms", details: "Public access to /.env.production detected (AWS_KEY leak alert)" },
    { id: "CHK-05", name: "CORS Misconfiguration & Origin Reflection", category: "CORS", status: "PASS", latency: "19ms", details: "Access-Control-Allow-Origin strictly whitelist validated" },
    { id: "CHK-06", name: "DNSSEC & Subdomain Takeover Vectors", category: "DNS", status: "PASS", latency: "45ms", details: "Zone valid; no orphaned CNAME to dangling S3/GitHub pages" },
];

export const SAMPLE_DOMAINS = ["example.com", "github.com", "stripe.com"];

export const MARQUEE_ITEMS = [
    "OWASP TOP 10", "CVE FEED · LIVE", "TLS 1.3 ENFORCED", "crt.sh MONITOR",
    "SOC2 READY", "ZERO-DAY WATCH", "HSTS PRELOAD", "SUBDOMAIN GUARD",
    "CSP AUDIT", "JWT HARDENING", "27 VULN CLASSES", "CREST VETTED",
];

export const LOGOS = [
    { name: "FINTECH_SERIES_B", badge: "SOC2 TYPE II" },
    { name: "DEV_INFRA_UNIFIED", badge: "ISO 27001" },
    { name: "HEALTH_API_GATEWAY", badge: "HIPAA" },
    { name: "NEOBANK_CORE", badge: "PCI-DSS 4.0" },
    { name: "IDENTITY_VAULT_LABS", badge: "GDPR AUDITED" },
];

export const STEPS = [
    {
        step: "01",
        title: "Instant Scan",
        lead: "Non-invasive passive recon in seconds",
        description: "Zero install. Enter your public URL to probe open ports, cryptographic hygiene, exposed config secrets, and outdated dependencies.",
        badge: "30 Seconds",
        code: 'curl -X POST https://api.wevnsec.dev/v1/scan \\\n  -d \'{"target": "https://yourapp.com"}\'',
    },
    {
        step: "02",
        title: "Verified Deep Scan",
        lead: "Authenticated attack surface validation",
        description: "Confirm ownership via DNS TXT or meta-tag to unlock active fuzzing, an authenticated route crawler, and API endpoint stress checks.",
        badge: "DNS Verified",
        code: "TXT  _wevnsec-verify=wn_9f82d1c5a9b\nValidating record across 12 edge nodes...",
    },
    {
        step: "03",
        title: "Human Pentest Report",
        lead: "Manual exploitation triage by certified engineers",
        description: "Machine precision meets human intuition. Certified researchers hunt logic flaws, broken auth, and IDOR issues with clear remediation snippets.",
        badge: "Audit Ready",
        code: "REPORT #WN-8821\nHIGH [CVSS 8.2] — BOLA in /api/v2/workspace/export\nRemediation diff provided.",
    },
];

export const GRID = [
    {
        category: "OWASP A01:2021",
        title: "Broken Access Control",
        description: "Checks for IDOR, unauthenticated admin routes, CORS misconfigurations, and role leakage across REST & GraphQL endpoints.",
        items: ["Direct Object References", "Privilege Escalation", "CORS Origin Reflection", "API Route Bypasses"],
    },
    {
        category: "OWASP A02:2021",
        title: "Cryptographic Failures",
        description: "Validates TLS 1.3 negotiation, deprecated cipher suites, HSTS preloading, and certificate expiration alerts.",
        items: ["TLS 1.0/1.1 Deprecation", "Weak Cipher Detection", "HSTS Header Preload", "Cert Chain Validation"],
    },
    {
        category: "OWASP A03:2021",
        title: "Injection & XSS Surfaces",
        description: "Detects DOM injection sinks, reflected query parameters, unescaped payload templates, and legacy script imports.",
        items: ["Reflected & DOM XSS", "SQLi & NoSQL Injection", "Template Injection", "Prototype Pollution"],
    },
    {
        category: "OWASP A05:2021",
        title: "Security Misconfiguration",
        description: "Scans for publicly accessible .env files, debug stack traces, open git repositories, and directory listings.",
        items: ["Exposed .env & .git", "Verbose Stack Traces", "Default Credentials", "Missing Security Headers"],
    },
    {
        category: "OWASP A06:2021",
        title: "Vulnerable Dependencies",
        description: "Inventories client-side packages against live CVE databases (NVD, GitHub Advisories) with upgrade paths.",
        items: ["Known CVEs in Bundles", "Outdated Frameworks", "Deprecation Warnings", "Supply Chain Alerts"],
    },
    {
        category: "OWASP A07:2021",
        title: "Auth & Session Flaws",
        description: "Tests cookie flags, JWT signature algorithms, login rate-limiting, and session invalidation behavior.",
        items: ["Missing Cookie Flags", "JWT 'None' Algorithm", "Missing Rate Limiting", "Session Fixation"],
    },
];

export const VERIFY_METHODS = [
    {
        type: "DNS TXT Record",
        tag: "Recommended for APIs & multi-domain",
        code: "Host:  _wevnsec-verification.yourdomain.com\nType:  TXT\nValue: wn-site-token-7e8b91a320c",
        latency: "Propagates in ~60 seconds",
    },
    {
        type: "HTML Meta Tag",
        tag: "Fastest for SPAs & Next.js",
        code: '<meta name="wevnsec-verify"\n      content="wn-site-token-7e8b91a320c" />',
        latency: "Instant crawl verification",
    },
];

export const DOCS_TABS = [
    {
        id: "curl",
        label: "cURL",
        code: "curl -X POST https://api.wevnsec.dev/v1/scans \\\n  -H 'Authorization: Bearer wn_live_sec_9941a87b' \\\n  -H 'Content-Type: application/json' \\\n  -d '{\n    \"target_url\": \"https://api.yourdomain.com\",\n    \"mode\": \"deep_verified\",\n    \"notify_webhook\": \"https://yourdomain.com/webhooks/security\"\n  }'",
    },
    {
        id: "gha",
        label: "GitHub Action",
        code: "name: WevnSec CI Gate\non: [pull_request]\njobs:\n  audit:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: wevnsec/scan-action@v2\n        with:\n          target: ${{ secrets.STAGING_PREVIEW_URL }}\n          api_key: ${{ secrets.WEVNS_TOKEN }}\n          fail_on: high,critical",
    },
    {
        id: "node",
        label: "Node.js SDK",
        code: "import { WevnSec } from '@wevnsec/sdk';\n\nconst client = new WevnSec(process.env.WEVNSEC_KEY);\nconst audit = await client.scans.create({\n  target: 'https://staging.app.io',\n  depth: 'full'\n});\nconsole.log(`Scan started: ${audit.id}`);",
    },
    {
        id: "webhook",
        label: "Webhooks",
        code: '{\n  "event": "scan.completed",\n  "scan_id": "scn_8819a",\n  "verdict": "ACTION_REQUIRED",\n  "critical_count": 1,\n  "high_count": 0,\n  "report_url": "https://app.wevnsec.dev/r/scn_8819a"\n}',
    },
];

export const PRICING = [
    {
        id: "free",
        name: "Instant Scan",
        price: "$0",
        period: "forever free",
        description: "Essential perimeter inspection for early-stage prototypes and side projects.",
        badge: "No card required",
        highlighted: false,
        features: [
            "Non-invasive passive reconnaissance",
            "SSL / TLS cipher configuration check",
            "Top 15 HTTP security headers",
            "Exposed secrets (.env, .git) probe",
            "Public scan link valid for 7 days",
        ],
        cta: "Run Free Scan",
        testId: "pricing-cta-free",
    },
    {
        id: "verified",
        name: "Verified Continuous",
        price: "$79",
        period: "per domain / month",
        description: "Automated daily deep scans with ownership verification and CI/CD integration.",
        badge: "Most Popular",
        highlighted: true,
        features: [
            "Everything in Instant Scan",
            "Automated daily & on-commit scans",
            "Authenticated deep route crawler",
            "GitHub Actions & Slack alerts",
            "Exportable PDF/JSON audit reports",
            "Subdomain takeover monitoring",
            "Fast-track false-positive triage",
        ],
        cta: "Start 14-Day Free Trial",
        testId: "pricing-cta-verified",
    },
    {
        id: "pentest",
        name: "Pentest On Request",
        price: "$1,450",
        period: "per engagement",
        description: "Human-led manual penetration test with certified whitehats and formal attestation.",
        badge: "CREST & OSCP Vetted",
        highlighted: false,
        features: [
            "Manual pentest (5–7 days)",
            "Business logic & auth bypass testing",
            "Executive summary + fix diffs",
            "1-on-1 re-test consultation call",
            "Signed attestation for SOC2/ISO",
            "Direct channel with lead researcher",
        ],
        cta: "Schedule Scope Call",
        testId: "pricing-cta-pentest",
    },
];

export const FAQS = [
    {
        q: "Will the Instant Scan slow down my production site?",
        a: "No. The Instant Scan uses lightweight, passive HTTP queries and TLS handshakes identical to a search engine bot or curl request. We strictly throttle to under 5 requests per second.",
    },
    {
        q: "Why do I need to verify DNS ownership for deeper scans?",
        a: "Active scans test input fields, injection parameters, and rate-limiting. To prevent misuse, legal ethics require proof of authority before dispatching dynamic payloads.",
    },
    {
        q: "How does this compare to running OWASP ZAP locally?",
        a: "WevnSec automates the entire orchestration with zero setup, correlates findings with live CVE feeds, filters noisy false positives, and gives you instant shareable links for your team.",
    },
    {
        q: "Can I integrate WevnSec into my GitHub Actions pipeline?",
        a: "Yes. Our official GitHub Action lets you fail builds when high or critical vulnerabilities are introduced in staging preview deployments.",
    },
];

export const INITIAL_STATS = {
    scanned: 1428914,
    vulns: 89240,
    avgTime: 28.4,
    researchers: 180,
};
