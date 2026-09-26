import argparse
import json
import os
import uuid

import psycopg2
import requests
from dotenv import dotenv_values


STATE_PATH = "/tmp/wevnsec-admin-ui-test-credentials.json"


def read_env(name: str, env_file: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    loaded = dotenv_values(env_file).get(name)
    if loaded:
        return loaded
    raise RuntimeError(f"Missing environment variable: {name}")


def api(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/api{path}"


def setup_disposable_admin(email: str, password: str, name: str, slug_prefix: str):
    base_url = read_env("REACT_APP_BACKEND_URL", "/app/frontend/.env")
    database_url = read_env("DATABASE_URL", "/app/backend/.env")

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    register_payload = {"name": name, "email": email, "password": password}
    register_response = session.post(api(base_url, "/auth/register"), json=register_payload, timeout=30)
    if register_response.status_code != 200:
        raise RuntimeError(f"Register failed: {register_response.status_code} {register_response.text}")

    register_data = register_response.json()
    user_id = register_data["user"]["id"]

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE wevnsec.profiles SET role='admin' WHERE id=%s", (user_id,))
    finally:
        conn.close()

    login_response = session.post(api(base_url, "/auth/login"), json={"email": email, "password": password}, timeout=30)
    if login_response.status_code != 200:
        raise RuntimeError(f"Login failed after promotion: {login_response.status_code} {login_response.text}")

    login_data = login_response.json()
    if login_data.get("user", {}).get("role") != "admin":
        raise RuntimeError("Promoted user did not authenticate as admin")

    state = {
        "user_id": user_id,
        "email": email,
        "password": password,
        "slug_prefix": slug_prefix,
        "token": login_data.get("token"),
    }
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.chmod(STATE_PATH, 0o600)

    print(f"SETUP_OK state_file={STATE_PATH} user_id={user_id}")


def cleanup_disposable_admin():
    database_url = read_env("DATABASE_URL", "/app/backend/.env")

    if not os.path.exists(STATE_PATH):
        print("CLEANUP_OK no_state_file")
        return

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    user_id = state.get("user_id")
    slug_prefix = state.get("slug_prefix") or "qa-admin-ui-iter4"

    conn = psycopg2.connect(database_url)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM wevnsec.documentation WHERE slug LIKE %s", (f"{slug_prefix}%",))
                if user_id:
                    cur.execute("DELETE FROM wevnsec.profiles WHERE id=%s", (user_id,))
                    cur.execute("DELETE FROM auth.users WHERE id=%s", (user_id,))
    finally:
        conn.close()

    try:
        os.remove(STATE_PATH)
    except OSError:
        pass

    print("CLEANUP_OK")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup")
    setup.add_argument("--email", required=False)
    setup.add_argument("--password", required=False)
    setup.add_argument("--name", required=False)
    setup.add_argument("--slug-prefix", required=False, default="qa-admin-ui-iter4")

    sub.add_parser("cleanup")

    args = parser.parse_args()

    if args.command == "setup":
        email = args.email or f"qa-admin-ui-{uuid.uuid4().hex[:10]}@example.com"
        password = args.password or f"QaPwd!{uuid.uuid4().hex[:10]}"
        name = args.name or f"QA Admin {uuid.uuid4().hex[:6]}"
        setup_disposable_admin(email=email, password=password, name=name, slug_prefix=args.slug_prefix)
    else:
        cleanup_disposable_admin()


if __name__ == "__main__":
    main()
