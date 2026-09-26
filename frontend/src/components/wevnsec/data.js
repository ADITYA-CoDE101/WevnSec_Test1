export const SAMPLE_DOMAINS = ["example.com", "github.com", "stripe.com"];

export const MARQUEE_ITEMS = [
    "TLS & CERTIFICATES", "HTTP SECURITY HEADERS", "OWNERSHIP VERIFICATION", "CORS OBSERVATIONS",
    "COOKIE FLAGS", "MITIGATION GUIDANCE", "HSTS HEADER CHECK", "PUBLIC SCAN REPORTS",
    "CSP HEADER CHECK", "REFERENCE LIBRARY", "REAL SCAN RESULTS", "SCOPED MANUAL REVIEW",
];

export const STEPS = [
    {
        step: "01",
        title: "Instant Scan",
        lead: "Non-invasive passive recon in seconds",
        description: "Enter a public domain to check TLS, root-response security headers, HTTPS redirects, cookie flags, and CORS behavior.",
        badge: "No install",
        code: 'POST /api/scan\n{"target": "example.com", "advanced": false}',
    },
    {
        step: "02",
        title: "Verified Deep Scan",
        lead: "Ownership-gated configuration checks",
        description: "Verify your apex domain to unlock sensitive-path probes and scheduled scans. Findings include context and remediation guidance.",
        badge: "DNS Verified",
        code: "TXT on your apex domain\nwevnsec-verify=<your verification token>",
    },
    {
        step: "03",
        title: "Human Pentest Report",
        lead: "Request a separately scoped assessment",
        description: "Discuss application-specific logic, authorization, and authenticated flows that a public automated scan cannot assess.",
        badge: "Audit Ready",
        code: "REPORT #WN-8821\nHIGH [CVSS 8.2] — BOLA in /api/v2/workspace/export\nRemediation diff provided.",
    },
];

export const GRID = [
    {
        category: "OWASP A01:2021",
        title: "Cross-Origin Configuration",
        description: "Observes root-endpoint CORS behavior. Application-specific authorization flaws such as IDOR require a separate review.",
        items: ["Origin Reflection", "Wildcard Observations", "Response Headers", "Context-Aware Guidance"],
    },
    {
        category: "OWASP A02:2021",
        title: "Cryptographic Failures",
        description: "Checks certificate trust and expiry, the negotiated TLS version, HTTPS availability, and root HTTP redirects.",
        items: ["Negotiated TLS Version", "Certificate Expiry", "HTTPS Availability", "HTTP Redirects"],
    },
    {
        category: "OWASP A03:2021",
        title: "Browser Defense Headers",
        description: "Checks for CSP, framing protection, and MIME-sniffing headers. Their presence does not prove that injection vulnerabilities are absent.",
        items: ["CSP Header Presence", "X-Frame-Options", "Content-Type Protection", "Documented Limitations"],
    },
    {
        category: "OWASP A05:2021",
        title: "Security Misconfiguration",
        description: "Ownership-gated advanced scans probe a bounded set of sensitive paths and flag possible exposure for manual confirmation.",
        items: [".env Path Probes", ".git Path Probes", "Configuration Paths", "Catch-All Baseline"],
    },
    {
        category: "OWASP A06:2021",
        title: "Privacy & Information Exposure",
        description: "Observes referrer and permissions-policy headers alongside server banners that may disclose implementation details.",
        items: ["Referrer-Policy", "Permissions-Policy", "Server Banners", "X-Powered-By"],
    },
    {
        category: "OWASP A07:2021",
        title: "Auth & Session Flaws",
        description: "Inspects cookies set by the public root response. Login behavior and authenticated session handling need application-specific testing.",
        items: ["Secure Attribute", "HttpOnly Attribute", "SameSite Attribute", "Public-Response Scope"],
    },
];

export const VERIFY_METHODS = [
    {
        type: "DNS TXT Record",
        tag: "Recommended for APIs & multi-domain",
        code: "Host:  @ (your apex domain)\nType:  TXT\nValue: wevnsec-verify=<your generated token>",
        latency: "DNS propagation time varies",
    },
    {
        type: "HTML Meta Tag",
        tag: "For server-rendered root HTML",
        code: '<meta name="wevnsec-verification"\n      content="<your generated token>" />',
        latency: "Checked when you select Verify now",
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

