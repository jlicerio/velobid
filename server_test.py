"""Legacy server smoke script.

Prefer `python scripts/verify.py --live` for the canonical smoke entrypoint.
"""
import sys
import requests
import time
import subprocess
import os
import re

SERVER_DIR = r"C:\Users\xlice\Desktop\velobid"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=SERVER_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

time.sleep(3)
passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}" + (f" -- {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  FAIL  {name}" + (f" -- {detail}" if detail else ""))

try:
    print("\n=== Server Integration Tests ===\n")

    # 1. Health
    r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=5)
    check("Health endpoint", r.status_code == 200, str(r.json()))

    # 2. Projects
    r = requests.get("http://127.0.0.1:8000/api/v1/projects", timeout=5)
    projects = r.json()
    check("List projects", r.status_code == 200 and len(projects) >= 4, f"{len(projects)} projects")

    # 3. Trades
    r = requests.get("http://127.0.0.1:8000/api/v1/trades", timeout=5)
    trades = r.json()
    check("List trades", r.status_code == 200 and len(trades) == 3, f"{len(trades)} trades")

    # 4. Bid preview
    r = requests.post(
        "http://127.0.0.1:8000/api/v1/bids/preview",
        json={"project_id": "shalom_prayer_center", "trade": "hvac"},
        timeout=10,
    )
    preview = r.json()
    check("Bid preview", r.status_code == 200, f"${preview['totals']['total_bid_amount']:,.2f}")

    # 5. Frontend serves
    r = requests.get("http://127.0.0.1:8000/", timeout=5)
    check("Frontend index.html", r.status_code == 200, f"{len(r.text)} bytes")
    check("Frontend has title", "VeloBid" in r.text, "")
    check("Frontend has static paths", "/static/assets/" in r.text, "")

    # 6. JS bundle loads
    js_match = re.search(r'src="(/static/assets/[^"]+)"', r.text)
    if js_match:
        r_js = requests.get(f"http://127.0.0.1:8000{js_match.group(1)}", timeout=5)
        check("JS bundle loads", r_js.status_code == 200, f"{len(r_js.text)} bytes")
    else:
        check("JS bundle referenced", False, "No src=/static/assets/ found")

    # 7. CSS bundle loads
    css_match = re.search(r'href="(/static/assets/[^"]+)"', r.text)
    if css_match:
        r_css = requests.get(f"http://127.0.0.1:8000{css_match.group(1)}", timeout=5)
        check("CSS bundle loads", r_css.status_code == 200, f"{len(r_css.text)} bytes")
    else:
        check("CSS bundle referenced", False, "No href=/static/assets/ found")

    # 8. Version create
    r = requests.post(
        "http://127.0.0.1:8000/api/v1/bids/shalom_prayer_center/hvac/versions",
        json={"trigger_source": "ai_refine", "commit_message": "Server test snapshot"},
        timeout=15,
    )
    check("Version create", r.status_code == 201, r.json().get('version_id', ''))

    # 9. Version list
    r = requests.get("http://127.0.0.1:8000/api/v1/bids/shalom_prayer_center/hvac/versions", timeout=5)
    versions = r.json().get('versions', [])
    check("Version list", r.status_code == 200 and len(versions) > 0, f"{len(versions)} versions")

    # 10. Version diff
    if len(versions) >= 2:
        v_id = versions[-1]['version_id']
        r = requests.get(
            f"http://127.0.0.1:8000/api/v1/bids/shalom_prayer_center/hvac/versions/{v_id}/diff",
            timeout=5,
        )
        check("Version diff", r.status_code == 200, r.json().get('diff', {}).get('summary', '')[:60])

    # 11. Blueprint upload
    test_file = os.path.join(SERVER_DIR, "test_upload.png")
    with open(test_file, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    with open(test_file, "rb") as f:
        r = requests.post(
            "http://127.0.0.1:8000/api/v1/blueprints/test_project",
            files={"file": ("test.png", f, "image/png")},
            timeout=10,
        )
    os.remove(test_file)
    check("Blueprint upload", r.status_code == 200, r.json().get('blueprint_id', ''))

    # 12. Blueprint list
    r = requests.get("http://127.0.0.1:8000/api/v1/blueprints/test_project", timeout=5)
    check("Blueprint list", r.status_code == 200,
          f"{len(r.json().get('blueprints', []))} blueprints")

    # 13. AI refine route
    r = requests.get("http://127.0.0.1:8000/openapi.json", timeout=5)
    paths = list(r.json().get('paths', {}).keys())
    check("AI refine route exists", "/api/v1/ai/refine" in paths if r.ok else False, "")

    # 14. Vision route
    check("Vision route exists", "/api/v1/vision/analyze/{project_id}/{blueprint_id}" in paths if r.ok else False, "")

    print(f"\n=== RESULTS: {passed} passed, {failed} failed ===")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    proc.terminate()
    proc.wait(timeout=5)
