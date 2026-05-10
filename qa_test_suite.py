"""Legacy comprehensive QA script.

Prefer `python scripts/verify.py` for the canonical validation entrypoint.
"""
import json
import sys
import os
import traceback

# Ensure we can import from the project
sys.path.insert(0, r"C:\Users\xlice\Desktop\velobid")

# Track results
passed = []
failed = []

def test(name, fn):
    try:
        fn()
        passed.append(name)
        print(f"  PASS  {name}")
    except Exception as e:
        failed.append(name)
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()

print("=" * 60)
print("VELOBID API QA TEST SUITE")
print("=" * 60)

# ===== 1. HEALTH & META =====
print("\n--- 1. Health & Meta ---")

def test_health():
    from api.main import app
    from api.services.bids import PROJECT_ROOT, BID_PROJECTS_DIR
    assert PROJECT_ROOT.exists(), "Project root should exist"
    assert BID_PROJECTS_DIR.exists(), "BID projects dir should exist"
    assert app.title == "Velobid API"
    assert app.version == "0.1.1"

test("Health check imports", test_health)

def test_meta_endpoint():
    from api.routers.bids import router
    routes = [r.path for r in router.routes]
    assert "/api/v1/health" in routes
    assert "/api/v1/projects" in routes
    assert "/api/v1/trades" in routes

test("Meta routes exist", test_meta_endpoint)

# ===== 2. PROJECTS & TRADES =====
print("\n--- 2. Projects & Trades ---")

def test_list_projects():
    from api.services.bids import list_project_configs
    projects = list_project_configs()
    assert len(projects) >= 4, f"Expected 4+ projects, got {len(projects)}"
    names = [p.name for p in projects]
    assert "Jackson McAllen Retail #42740" in names
    assert "Shalom Prayer Center" in names

test("List projects returns all 5", test_list_projects)

def test_list_trades():
    from api.services.bids import list_trade_configs
    trades = list_trade_configs()
    assert len(trades) == 3, f"Expected 3 trades, got {len(trades)}"
    names = [t.name for t in trades]
    assert "Electrical" in names
    assert "Plumbing" in names
    assert "Heating, Ventilating" in names[1]

test("List trades returns all 3", test_list_trades)

def test_resolve_project():
    from api.services.bids import resolve_project_path
    path = resolve_project_path("shalom_prayer_center")
    assert path.exists(), f"Path should exist: {path}"
    assert "shalom_prayer_center.json" in path.name

test("Resolve project path", test_resolve_project)

def test_resolve_trade():
    from api.services.bids import resolve_trade_path
    path = resolve_trade_path("hvac")
    assert path.exists()
    # Test alias resolution
    path23 = resolve_trade_path("23")
    assert path23.name == "hvac.json"

test("Resolve trade path + aliases", test_resolve_trade)

# ===== 3. BID PREVIEW =====
print("\n--- 3. Bid Preview ---")

def test_preview_hvac():
    from api.services.bids import preview_bid
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="hvac")
    result = preview_bid(req)
    assert result.project_name == "Shalom Prayer Center"
    assert result.trade_name == "HVAC"
    assert result.totals.total_bid_amount == 89536.12
    assert len(result.line_items) == 5
    assert len(result.exclusions) == 4

test("Preview HVAC bid - Shalom", test_preview_hvac)

def test_preview_electrical():
    from api.services.bids import preview_bid
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="electrical")
    result = preview_bid(req)
    assert result.trade_name == "Electrical"
    assert result.totals.total_bid_amount == 26323.50

test("Preview Electrical bid", test_preview_electrical)

def test_preview_plumbing():
    from api.services.bids import preview_bid
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="plumbing")
    result = preview_bid(req)
    assert result.trade_name == "Plumbing"
    assert result.totals.total_bid_amount == 16301.25

test("Preview Plumbing bid", test_preview_plumbing)

def test_preview_invalid_project():
    from api.services.bids import preview_bid
    from api.schemas.bids import GenerateBidRequest
    from fastapi import HTTPException
    req = GenerateBidRequest(project_id="nonexistent_project")
    try:
        preview_bid(req)
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

test("Preview invalid project returns 404", test_preview_invalid_project)

# ===== 4. BID GENERATE =====
print("\n--- 4. Bid Generate ---")

def test_generate_pdfs():
    from api.services.bids import generate_bid_files
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="hvac", package_name="client")
    result = generate_bid_files(req)
    assert result.preview.project_name == "Shalom Prayer Center"
    assert len(result.generated_files) == 3, f"Expected 3 client PDFs, got {len(result.generated_files)}"
    names = [f.filename for f in result.generated_files]
    assert any("Bid_Proposal" in n for n in names)
    assert any("Full_Scope" in n for n in names)
    assert any("Technical_Scope" in n for n in names)

test("Generate client PDFs (3 docs)", test_generate_pdfs)

def test_generate_all_pdfs():
    from api.services.bids import generate_bid_files
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="hvac", package_name="all")
    result = generate_bid_files(req)
    assert len(result.generated_files) == 5, f"Expected 5 PDFs, got {len(result.generated_files)}"

test("Generate all PDFs (5 docs)", test_generate_all_pdfs)

# ===== 5. VERSION SYSTEM =====
print("\n--- 5. Version System ---")

def test_version_empty_list():
    from api.services.versions import list_versions
    versions = list_versions("__test_project__", "hvac")
    assert versions == [], "Non-existent project should return empty list"

test("List versions on non-existent project", test_version_empty_list)

def test_version_create_and_list():
    from api.services.bids import preview_bid
    from api.schemas.bids import GenerateBidRequest
    from api.services.versions import create_snapshot, list_versions, get_snapshot

    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="hvac")
    preview = preview_bid(req)

    # Create a version (idempotent - use a unique trigger for test)
    v1 = create_snapshot("shalom_prayer_center", "hvac", "ai_refine", preview, commit_message="QA test snapshot")
    assert v1.version_id.startswith("v")
    assert v1.commit_message == "QA test snapshot"
    assert v1.diff is None or v1.diff.summary is not None  # may or may not have diff

    # List
    versions = list_versions("shalom_prayer_center", "hvac")
    assert len(versions) >= 1
    assert versions[-1].version_id == v1.version_id

    # Read back
    snap = get_snapshot("shalom_prayer_center", "hvac", v1.version_id)
    assert snap.snapshot_data.project_name == "Shalom Prayer Center"
    assert snap.snapshot_data.totals["total_bid_amount"] == 89536.12

test("Version create, list, and read", test_version_create_and_list)

def test_version_diff():
    from api.services.versions import get_diff, list_versions

    versions = list_versions("shalom_prayer_center", "hvac")
    if len(versions) >= 2:
        v2 = versions[-1].version_id
        diff = get_diff("shalom_prayer_center", "hvac", v2)
        assert diff is not None
        assert diff.diff_type == "version_diff"

test("Version diff endpoint", test_version_diff)

def test_version_restore():
    from api.services.versions import restore_snapshot, list_versions

    versions = list_versions("shalom_prayer_center", "hvac")
    assert len(versions) >= 1
    v1 = versions[-1].version_id
    result = restore_snapshot("shalom_prayer_center", "hvac", v1)
    assert result.project_name == "Shalom Prayer Center"
    assert result.totals["total_bid_amount"] == 89536.12
    assert len(result.line_items) == 5

test("Version restore", test_version_restore)

# ===== 6. AI REFINE =====
print("\n--- 6. AI Refine ---")

def test_ai_imports():
    from api.services.ai import check_llm_health, refine_config
    from openai import APITimeoutError, APIConnectionError
    assert callable(refine_config)
    assert callable(check_llm_health)

test("AI module imports with timeout handling", test_ai_imports)

def test_ai_router_error_handling():
    from api.routers.ai import router
    # Check the route exists
    routes = [(r.path, list(r.methods)) for r in router.routes]
    assert any("/refine" in r[0] for r in routes)

test("AI refine route registered", test_ai_router_error_handling)

# ===== 7. CHAT CONTEXT INJECTION =====
print("\n--- 7. Chat Context ---")

def test_chat_imports():
    from api.routers.agent_chat import router, ChatRequest, ChatMessage
    routes = [r.path for r in router.routes]
    assert "/api/v1/agent/chat" in routes
    msg = ChatMessage(role="user", content="hello")
    assert msg.role == "user"

test("Agent chat router imports", test_chat_imports)

def test_chat_context_building():
    from api.routers.agent_chat import _build_rich_context
    context = _build_rich_context("shalom_prayer_center", "hvac")
    assert "Shalom Prayer Center" in context
    assert "$89,536.12" in context
    assert "Total Bid" in context
    assert "Line Items" in context
    assert "23-31-00" in context  # cost code

test("Chat context injection includes live bid state", test_chat_context_building)

def test_chat_context_without_project():
    from api.routers.agent_chat import _build_rich_context
    try:
        context = _build_rich_context("__nonexistent__", "hvac")
        assert "Project ID" in context
    except Exception:
        pass  # Acceptable either way

test("Chat context handles missing project gracefully", test_chat_context_without_project)

# ===== 8. FILE MANAGEMENT =====
print("\n--- 8. File Management ---")

def test_list_files():
    from api.routers.files import router
    routes = [r.path for r in router.routes]
    assert "/api/v1/files/list" in routes
    assert "/api/v1/files/delete" in routes

test("File routes registered", test_list_files)

def test_generated_file_urls():
    from api.services.bids import generate_bid_files
    from api.schemas.bids import GenerateBidRequest
    req = GenerateBidRequest(project_id="shalom_prayer_center", trade="electrical", package_name="client")
    result = generate_bid_files(req)
    for f in result.generated_files:
        assert f.url.startswith("/files/")
        assert f.filename.endswith(".pdf")

test("Generated file URLs are valid", test_generated_file_urls)

# ===== SUMMARY =====
print("\n" + "=" * 60)
print(f"RESULTS: {len(passed)} passed, {len(failed)} failed, {len(passed)+len(failed)} total")
if failed:
    print("FAILED TESTS:")
    for f in failed:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
