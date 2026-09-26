import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import asyncio
import logging
import re
import socket
import ssl
import time
import uuid
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
import httpx


import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from supabase import create_async_client

from database import AsyncSessionLocal, engine, get_db
from models import Alert, Domain, Profile, Scan, utcnow
from monitoring import MonitoringWorker, record_scan
from pdf_report import build_pdf
from auth_throttle import lock_attempt, failed_attempt, successful_attempt
from domain_routes import domain_router
from domain_cleanup import router as cleanup_router
from domain_validation import VerificationError, normalize_domain
from ownership import require_ownership

app = FastAPI()
api_router = APIRouter(prefix="/api")

JWT_ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TRUSTED_ORIGINS = [origin.strip().rstrip('/') for origin in os.environ["CORS_ORIGINS"].split(',') if origin.strip() and origin.strip() != '*']
TRUSTED_ORIGINS = list(dict.fromkeys([*TRUSTED_ORIGINS, os.environ["APP_URL"].rstrip('/'), os.environ['WEVNSEC_APP_URL'].rstrip('/'), *[origin.strip().rstrip('/') for origin in os.environ['WEVNSEC_TRUSTED_ORIGINS'].split(',') if origin.strip()]]))
if not TRUSTED_ORIGINS or any(origin == '*' or not origin.startswith(('https://', 'http://')) for origin in TRUSTED_ORIGINS):
    raise RuntimeError('CORS_ORIGINS must list explicit trusted origins')
COOKIE_SECURE = os.environ["APP_URL"].startswith('https://')

supa = None       # service-role client (admin operations)
anon_supa = None  # publishable-key client (password verification)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ---------- auth ----------

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload if payload.get("type") == "access" else None
    except jwt.InvalidTokenError:
        return None


def public_user(profile: Profile, email: str) -> dict:
    return {"id": profile.id, "email": email, "name": profile.name, "role": profile.role}


async def resolve_profile(request: Request, creds: HTTPAuthorizationCredentials, db: AsyncSession):
    token = creds.credentials if creds else request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    profile = await db.get(Profile, payload["sub"])
    if not profile:
        return None
    return profile, payload["email"]


async def get_current_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    resolved = await resolve_profile(request, creds, db)
    if not resolved:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile, email = resolved
    return {"profile": profile, "email": email, "id": profile.id}


async def get_optional_user(request: Request, creds: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)):
    resolved = await resolve_profile(request, creds, db)
    if not resolved:
        return None
    profile, email = resolved
    return {"profile": profile, "email": email, "id": profile.id}


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@api_router.post("/auth/register")
async def register(body: RegisterIn, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.lower()
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    name = body.name.strip() or email.split("@")[0]
    try:
        res = await supa.auth.admin.create_user({
            "email": email,
            "password": body.password,
            "email_confirm": True,
            "user_metadata": {"name": name},
        })
    except Exception as e:
        if "already" in str(e).lower():
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        logger.error(f"supabase create_user failed: {e}")
        raise HTTPException(status_code=502, detail="Could not create account")
    uid = res.user.id
    db.add(Profile(id=uid, name=name, role="user"))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
    token = create_access_token(uid, email)
    response.set_cookie("access_token", token, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=86400, path="/")
    return {"token": token, "user": {"id": uid, "email": email, "name": name, "role": "user"}}


@api_router.post("/auth/login")
async def login(body: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.lower()
    throttle = await lock_attempt(db, email)
    try:
        res = await asyncio.wait_for(anon_supa.auth.sign_in_with_password({"email": email, "password": body.password}), timeout=15)
    except Exception as exc:
        if str(getattr(exc, 'status', '')) not in ('400', '401', '403', '422'):
            await db.rollback()
            raise HTTPException(status_code=502, detail="Sign-in service unavailable. Please try again.")
        await failed_attempt(db, throttle)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await successful_attempt(db, throttle)
    uid = res.user.id
    profile = await db.get(Profile, uid)
    if not profile:
        name = (res.user.user_metadata or {}).get("name") or email.split("@")[0]
        profile = Profile(id=uid, name=name, role="user")
        db.add(profile)
        await db.commit()
    token = create_access_token(uid, email)
    response.set_cookie("access_token", token, httponly=True, secure=COOKIE_SECURE, samesite="lax", max_age=86400, path="/")
    return {"token": token, "user": public_user(profile, email)}


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api_router.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return public_user(user["profile"], user["email"])


# ---------- scan engine ----------

HOST_RE = re.compile(r"^(?=.{1,253}\.?$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\.?$")

PROBE_PATHS = [
    "/.env",
    "/.env.production",
    "/.git/HEAD",
    "/.git/config",
    "/config.json",
    "/server-status",
    "/.DS_Store",
    "/docker-compose.yml",
]

SECURITY_HEADERS = [
    ("strict-transport-security", "HSTS (HTTP Strict Transport Security)", "high",
     "Browsers are not forced onto HTTPS after the first visit.",
     "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload"),
    ("content-security-policy", "Content Security Policy", "medium",
     "Without CSP, injected scripts can execute freely (XSS).",
     "Content-Security-Policy: default-src 'self'; script-src 'self'"),
    ("x-frame-options", "Clickjacking protection (X-Frame-Options)", "medium",
     "Pages can be iframed by hostile sites (clickjacking).",
     "X-Frame-Options: DENY  (or CSP: frame-ancestors 'none')"),
    ("x-content-type-options", "MIME sniffing protection", "low",
     "Browsers may sniff content types and execute uploaded files.",
     "X-Content-Type-Options: nosniff"),
    ("referrer-policy", "Referrer-Policy", "low",
     "Full URLs (with tokens/params) may leak to third parties.",
     "Referrer-Policy: strict-origin-when-cross-origin"),
    ("permissions-policy", "Permissions-Policy", "low",
     "Browser features (camera, mic, geo) are unrestricted.",
     "Permissions-Policy: camera=(), microphone=(), geolocation=()"),
]

SEVERITY_WEIGHT = {"critical": 25, "high": 15, "medium": 8, "low": 3}


def normalize_host(target: str) -> str:
    t = target.strip().lower()
    t = re.sub(r"^https?://", "", t)
    t = t.split("/")[0].split("?")[0].split("#")[0].split(":")[0].strip(".")
    if not t or not HOST_RE.match(t):
        raise HTTPException(status_code=400, detail="Enter a valid public domain, e.g. yourapp.com")
    if t == "localhost" or t.endswith((".local", ".internal", ".localhost", ".test")):
        raise HTTPException(status_code=400, detail="Only public domains can be scanned")
    try:
        ip = ip_address(t)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise HTTPException(status_code=400, detail="Private or reserved addresses cannot be scanned")
    except ValueError:
        pass
    return t


def mk(cid, name, category, status, severity, detail, fix, t0):
    return {
        "id": cid,
        "name": name,
        "category": category,
        "status": status,
        "severity": severity,
        "detail": detail,
        "fix": fix,
        "latency_ms": max(1, round((time.perf_counter() - t0) * 1000)),
    }


def _tls_probe(host):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=6) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ss:
            cert = ss.getpeercert()
            not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            issuer = dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "Unknown CA")
            days = (not_after - datetime.now(timezone.utc)).days
            return {"version": ss.version() or "unknown", "days_left": days, "issuer": issuer}


async def check_tls(host):
    t0 = time.perf_counter()
    try:
        info = await asyncio.to_thread(_tls_probe, host)
    except Exception as e:
        return [mk("TLS-01", "TLS certificate & protocol", "SSL/TLS", "fail", "critical",
                   f"TLS handshake failed ({type(e).__name__}). Clients cannot establish a secure connection.",
                   "Install a valid certificate from a trusted CA (e.g. Let's Encrypt) and enable TLS 1.2+.", t0)]
    version, days, issuer = info["version"], info["days_left"], info["issuer"]
    if days < 0:
        return [mk("TLS-01", "TLS certificate & protocol", "SSL/TLS", "fail", "critical",
                   f"Certificate issued by {issuer} EXPIRED {-days} days ago.",
                   "Renew the certificate immediately; automate renewal with certbot or your platform.", t0)]
    if version not in ("TLSv1.2", "TLSv1.3"):
        return [mk("TLS-01", "TLS certificate & protocol", "SSL/TLS", "fail", "high",
                   f"Negotiated deprecated protocol {version} (issuer {issuer}).",
                   "Disable TLS 1.0/1.1 at the edge; allow only TLS 1.2 and 1.3.", t0)]
    if days < 21:
        return [mk("TLS-01", "TLS certificate & protocol", "SSL/TLS", "warn", "low",
                   f"{version} active · cert by {issuer} expires in {days} days.",
                   "Renew the certificate soon or enable auto-renewal.", t0)]
    return [mk("TLS-01", "TLS certificate & protocol", "SSL/TLS", "pass", "none",
               f"{version} enforced · {issuer} · valid for {days} more days", "", t0)]


async def check_http(host, advanced=False):
    checks = []
    headers_cfg = {"User-Agent": "WevnSec-Scanner/2.4 (+https://wevnsec.dev)"}
    async with httpx.AsyncClient(timeout=7.0, follow_redirects=False, verify=False, headers=headers_cfg) as client:
        resp, scheme = None, "https"
        t0 = time.perf_counter()
        try:
            resp = await client.get(f"https://{host}/")
        except Exception:
            try:
                scheme = "http"
                resp = await client.get(f"http://{host}/")
                checks.append(mk("NET-01", "HTTPS availability", "TRANSPORT", "fail", "critical",
                                 "Site is only reachable over plain HTTP — all traffic is unencrypted.",
                                 "Install a TLS certificate and redirect all port-80 traffic to HTTPS.", t0))
            except Exception as e:
                checks.append(mk("NET-00", "Host reachability", "NETWORK", "fail", "critical",
                                 f"No HTTP connection could be established ({type(e).__name__}).",
                                 "Check DNS records and that ports 80/443 are open on a live server.", t0))
                return checks
        if scheme == "https":
            checks.append(mk("NET-01", "HTTPS availability", "TRANSPORT", "pass", "none",
                             f"HTTPS endpoint reachable · HTTP {resp.status_code}", "", t0))

            t1 = time.perf_counter()
            try:
                r80 = await client.get(f"http://{host}/")
                loc = r80.headers.get("location", "")
                if r80.status_code in (301, 302, 303, 307, 308) and loc.lower().startswith("https://"):
                    checks.append(mk("NET-02", "HTTP → HTTPS redirect", "TRANSPORT", "pass", "none",
                                     f"HTTP {r80.status_code} redirect to {loc[:80]}", "", t1))
                else:
                    checks.append(mk("NET-02", "HTTP → HTTPS redirect", "TRANSPORT", "fail", "medium",
                                     f"Port 80 answers with HTTP {r80.status_code} instead of redirecting to HTTPS.",
                                     "Return a 301 to https:// for every HTTP request at the edge/load balancer.", t1))
            except Exception:
                checks.append(mk("NET-02", "HTTP → HTTPS redirect", "TRANSPORT", "warn", "low",
                                 "Port 80 unreachable; redirect behavior could not be verified.",
                                 "Confirm HTTP requests 301-redirect to HTTPS.", t1))

        for key, name, sev, why, fix in SECURITY_HEADERS:
            t2 = time.perf_counter()
            value = resp.headers.get(key)
            if value:
                checks.append(mk(f"HDR-{key[:6]}", name, "HEADERS", "pass", "none",
                                 f"{key}: {value[:90]}", "", t2))
            else:
                checks.append(mk(f"HDR-{key[:6]}", name, "HEADERS", "fail", sev, f"Missing header. {why}", fix, t2))

        t3 = time.perf_counter()
        server = resp.headers.get("server")
        powered = resp.headers.get("x-powered-by")
        leaked = [f"Server: {server}" if server else "", f"X-Powered-By: {powered}" if powered else ""]
        leaked = [l for l in leaked if l]
        if leaked:
            checks.append(mk("HDR-SRV", "Server fingerprint disclosure", "HEADERS", "warn", "low",
                             " · ".join(leaked) + " — reveals software versions to attackers.",
                             "Remove or genericize Server / X-Powered-By headers at the reverse proxy.", t3))
        else:
            checks.append(mk("HDR-SRV", "Server fingerprint disclosure", "HEADERS", "pass", "none",
                             "No Server or X-Powered-By banners exposed", "", t3))

        t4 = time.perf_counter()
        cookies = resp.headers.get_list("set-cookie")
        if not cookies:
            checks.append(mk("CK-01", "Cookie security flags", "SESSION", "pass", "none",
                             "No cookies set on the entry route", "", t4))
        else:
            weak = [c.split("=")[0] for c in cookies
                    if "secure" not in c.lower() or "httponly" not in c.lower() or "samesite" not in c.lower()]
            if weak:
                checks.append(mk("CK-01", "Cookie security flags", "SESSION", "fail", "medium",
                                 f"Cookies missing Secure/HttpOnly/SameSite: {', '.join(weak[:4])}",
                                 "Set Secure, HttpOnly and SameSite=Lax (or Strict) on all session cookies.", t4))
            else:
                checks.append(mk("CK-01", "Cookie security flags", "SESSION", "pass", "none",
                                 f"{len(cookies)} cookie(s) carry Secure, HttpOnly and SameSite flags", "", t4))

        t5 = time.perf_counter()
        try:
            rc = await client.get(f"{scheme}://{host}/", headers={"Origin": "https://probe.wevnsec.dev"})
            acao = rc.headers.get("access-control-allow-origin", "")
            if acao == "*" or acao.lower() == "https://probe.wevnsec.dev":
                checks.append(mk("CORS-01", "CORS origin reflection", "CORS", "fail", "high",
                                 f"Access-Control-Allow-Origin answers '{acao}' to an arbitrary Origin.",
                                 "Whitelist trusted origins explicitly; never reflect the Origin header or use '*' with credentials.", t5))
            else:
                checks.append(mk("CORS-01", "CORS origin reflection", "CORS", "pass", "none",
                                 "Arbitrary origins are not reflected or wildcarded", "", t5))
        except Exception:
            checks.append(mk("CORS-01", "CORS origin reflection", "CORS", "warn", "low",
                             "CORS probe timed out; configuration could not be verified.", "", t5))

        if not advanced:
            return checks
        t6 = time.perf_counter()
        try:
            canary = await client.get(f"{scheme}://{host}/wevnsec-canary-{uuid.uuid4().hex[:10]}")

            async def probe(path):
                try:
                    r = await client.get(f"{scheme}://{host}{path}")
                    return path, r.status_code, len(r.content)
                except Exception:
                    return path, 0, 0

            results = await asyncio.gather(*[probe(p) for p in PROBE_PATHS])
            exposed = []
            for path, status, size in results:
                if status == 200 and size > 0:
                    if canary.status_code == 200 and abs(size - len(canary.content)) < 64:
                        continue  # SPA catch-all route, not a real file
                    exposed.append(path)
            if exposed:
                checks.append(mk("LEAK-01", "Exposed secrets & config files", "ENV_LEAK", "fail", "critical",
                                 f"Publicly accessible: {', '.join(exposed)}",
                                 "Remove dotfiles from the webroot and deny them at the edge: location ~ /\\.(env|git) { deny all; }", t6))
            else:
                checks.append(mk("LEAK-01", "Exposed secrets & config files", "ENV_LEAK", "pass", "none",
                                 f"Probed {len(PROBE_PATHS)} sensitive paths (.env, .git, config) — none exposed", "", t6))
        except Exception:
            checks.append(mk("LEAK-01", "Exposed secrets & config files", "ENV_LEAK", "warn", "low",
                             "Exposure probes could not be completed (timeouts).", "", t6))
    return checks


def compute_score(checks):
    penalty = 0
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "warning": 0, "passed": 0}
    for c in checks:
        if c["status"] == "fail":
            counts[c["severity"]] = counts.get(c["severity"], 0) + 1
            penalty += SEVERITY_WEIGHT.get(c["severity"], 5)
        elif c["status"] == "warn":
            counts["warning"] += 1
            penalty += 3
        else:
            counts["passed"] += 1
    score = max(5, 100 - penalty)
    grade = "A+" if score >= 95 else "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"
    return score, grade, counts


class ScanIn(BaseModel):
    target: str
    advanced: bool = False


def serialize_scan(s: Scan, include_checks: bool = True) -> dict:
    out = {
        "id": s.id,
        "share_id": s.share_id,
        "target": s.target,
        "user_id": s.user_id,
        "score": s.score,
        "grade": s.grade,
        "counts": s.counts,
        "duration_ms": s.duration_ms,
        "source": s.source,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
    if include_checks:
        out["checks"] = s.checks
    return out


async def run_scan(host, user_id=None, source="manual", advanced=False):
    try:
        host = normalize_domain(host)
    except VerificationError as exc:
        raise HTTPException(400, detail={'reason': exc.reason, 'message': exc.message})
    advanced = advanced or source == 'scheduled'
    if advanced:
        async with AsyncSessionLocal() as db:
            await require_ownership(db, user_id, host)
    started = time.perf_counter()
    tls_checks, http_checks = await asyncio.gather(check_tls(host), check_http(host, advanced=advanced))
    checks = tls_checks + http_checks
    duration = round((time.perf_counter() - started) * 1000)
    score, grade, counts = compute_score(checks)
    scan = Scan(
        share_id=uuid.uuid4().hex[:12],
        target=host,
        user_id=user_id,
        source=source,
        score=score,
        grade=grade,
        counts=counts,
        duration_ms=duration,
        checks=checks,
    )
    return scan


@api_router.post("/scan")
async def create_scan(body: ScanIn, user=Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    scan = await run_scan(body.target, user["id"] if user else None, advanced=body.advanced)
    await record_scan(db, scan)
    return serialize_scan(scan)


@api_router.get("/scan/{share_id}")
async def get_scan(share_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.share_id == share_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan report not found")
    return serialize_scan(scan)


@api_router.get("/scans/history")
async def scan_history(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).where(Scan.user_id == user["id"]).order_by(Scan.created_at.desc()).limit(50)
    )
    return [serialize_scan(s, include_checks=False) for s in result.scalars().all()]


@api_router.get("/scan/{share_id}/pdf")
async def download_scan_pdf(share_id: str, db: AsyncSession = Depends(get_db)):
    scan = (await db.execute(select(Scan).where(Scan.share_id == share_id))).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan report not found")
    pdf = await asyncio.to_thread(build_pdf, scan)
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="wevnsec-{scan.target}-{scan.share_id}.pdf"',
        "Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff",
    })


api_router.include_router(domain_router(get_current_user, serialize_scan))
api_router.include_router(cleanup_router)

class DomainPreferences(BaseModel):
    monitoring_enabled: bool | None = None
    email_alerts_enabled: bool | None = None


@api_router.patch("/domains/{domain_id}")
async def update_domain(domain_id: uuid.UUID, body: DomainPreferences, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    domain = (await db.execute(select(Domain).where(
        Domain.id == str(domain_id), Domain.user_id == user["id"]
    ).with_for_update())).scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    if body.monitoring_enabled is True and not domain.verified:
        raise HTTPException(403, detail={'reason': 'ownership_required', 'message': 'Verify ownership before enabling advanced daily scans.'})
    if body.monitoring_enabled is not None and body.monitoring_enabled != domain.monitoring_enabled:
        domain.monitoring_enabled = body.monitoring_enabled
        domain.next_scan_at = utcnow() if body.monitoring_enabled else None
        domain.scan_lock_until = domain.scan_lock_token = None
    if body.email_alerts_enabled is not None:
        domain.email_alerts_enabled = body.email_alerts_enabled
    await db.commit()
    return {"ok": True}


@api_router.get("/alerts")
async def list_alerts(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    alerts = (await db.execute(select(Alert).where(Alert.user_id == user["id"]).order_by(Alert.created_at.desc()).limit(100))).scalars().all()
    fields = ('id','domain','scan_share_id','delta','message','read','previous_grade','current_grade','previous_score','current_score','email_status','email_error')
    return [{**{key: getattr(a,key) for key in fields}, "created_at": a.created_at.isoformat(),
             "email_sent_at": a.email_sent_at.isoformat() if a.email_sent_at else None} for a in alerts]


@api_router.patch("/alerts/{alert_id}/read")
async def read_alert(alert_id: uuid.UUID, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    alert = (await db.execute(select(Alert).where(Alert.id == str(alert_id), Alert.user_id == user["id"]))).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.read = True
    await db.commit()
    return {"ok": True}


@api_router.get("/monitoring/status")
async def monitoring_status(user=Depends(get_current_user)):
    return {"scheduler_running": bool(monitor.task and not monitor.task.done()), "frequency_hours": 24,
            "email_configured": bool(os.environ["EMERGENT_EMAIL_KEY"]), "email_from_name": os.environ["EMAIL_FROM_NAME"]}


async def account_email(user_id):
    async with AsyncSessionLocal() as db:
        return (await db.execute(text('SELECT email FROM auth.users WHERE id = CAST(:id AS uuid)'), {"id": user_id})).scalar_one_or_none()


monitor = MonitoringWorker(run_scan, account_email)


@api_router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("""
        SELECT count(*) AS scans,
               COALESCE(SUM((counts->>'critical')::int + (counts->>'high')::int
                          + (counts->>'medium')::int + (counts->>'low')::int), 0) AS vulns
        FROM wevnsec.scans
    """))
    row = result.one()
    return {"scans": row.scans, "vulns": int(row.vulns)}


@api_router.get("/")
async def root():
    return {"message": "WevnSec API"}


# ---------- startup ----------

async def ensure_auth_user(email: str, password: str, name: str, role: str, db: AsyncSession):
    users = await supa.auth.admin.list_users()
    existing = next((u for u in users if u.email == email), None)
    if existing is None:
        res = await supa.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": name},
        })
        uid = res.user.id
    else:
        uid = existing.id
    profile = await db.get(Profile, uid)
    if not profile:
        db.add(Profile(id=uid, name=name, role=role))
        await db.commit()
    elif profile.role != role:
        profile.role = role
        await db.commit()


@app.on_event("startup")
async def startup():
    global supa, anon_supa
    supa = await create_async_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    anon_supa = await create_async_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    async with AsyncSessionLocal() as db:
        await ensure_auth_user(os.environ["ADMIN_EMAIL"],
                               os.environ["ADMIN_PASSWORD"], "Admin", "admin", db)
        await ensure_auth_user(os.environ["DEMO_EMAIL"], os.environ["DEMO_PASSWORD"], "Demo Engineer", "user", db)
        await db.execute(text("DELETE FROM wevnsec.login_throttle WHERE updated_at < now() - interval '1 day'"))
        await db.commit()
    logger.info("WevnSec API ready (Supabase)")
    monitor.start()


@app.on_event("shutdown")
async def shutdown():
    await monitor.stop()
    await engine.dispose()


app.include_router(api_router)


@app.middleware("http")
async def trusted_write_origin(request: Request, call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin = request.headers.get('origin')
        if origin is not None and origin not in TRUSTED_ORIGINS:
            logger.warning('Rejected write origin %r; configured origins %r', origin, TRUSTED_ORIGINS)
            return JSONResponse(status_code=403, content={'detail':'Origin not allowed'})
        if not origin and request.cookies.get('access_token') and not request.headers.get('authorization') and request.url.path not in ('/api/auth/login','/api/auth/register'):
            return JSONResponse(status_code=403, content={'detail':'Origin required for cookie-authenticated changes'})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=TRUSTED_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
