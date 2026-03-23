#!/usr/bin/env python3
"""
xSmartDeepResearch API Integration Test
========================================
Verify the service on bigdata-ambari-30 is working properly.

Usage:
    python tests/test_remote_api.py                        # default tests
    python tests/test_remote_api.py --test health          # health only
    python tests/test_remote_api.py --test stream          # SSE stream
    python tests/test_remote_api.py --test async           # async + poll
    python tests/test_remote_api.py --test sync            # sync (blocking)
    python tests/test_remote_api.py --test history         # history list
    python tests/test_remote_api.py --host http://x:4004   # custom host
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Please install httpx first: pip install httpx")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────
DEFAULT_HOST = "https://xsmartdeepresearch.fusionxlink.com"
DEFAULT_QUESTION = "Python 3.13 has what new features? List 3 briefly"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print("  " + GREEN + "PASS" + RESET + "  " + msg)

def fail(msg):
    print("  " + RED + "FAIL" + RESET + "  " + msg)

def dim(msg):
    print("  " + DIM + msg + RESET)

def header(title):
    print("\n" + "=" * 60)
    print("  " + BOLD + title + RESET)
    print("=" * 60)


# ── Test 1: Health ───────────────────────────────────────
async def test_health(base_url, question):
    header("Test 1: Health Check")
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(base_url + "/health")
            data = resp.json()
            if resp.status_code == 200:
                ok("GET /health -> " + str(resp.status_code))
            else:
                fail("GET /health -> " + str(resp.status_code))
            status = data.get("status", "unknown")
            if status == "healthy":
                ok("status: " + status)
            else:
                fail("status: " + status)
            dim("version: %s, model: %s" % (data.get("version"), data.get("model")))

            resp2 = await client.get(base_url + "/api/health")
            if resp2.status_code == 200:
                ok("GET /api/health -> " + str(resp2.status_code))
            else:
                fail("GET /api/health -> " + str(resp2.status_code))

            return resp.status_code == 200
    except Exception as e:
        fail("Health check failed: " + str(e))
        return False


# ── Test 2: SSE Stream ───────────────────────────────────
async def test_stream(base_url, question):
    header("Test 2: SSE Stream Research")
    dim("Question: " + question)
    print()

    event_counts = {}
    final_answer = None
    t0 = time.time()

    try:
        async with httpx.AsyncClient(verify=False, timeout=300) as client:
            async with client.stream(
                "POST",
                base_url + "/api/v1/research/stream",
                json={"question": question, "max_iterations": 5},
            ) as response:
                if response.status_code == 200:
                    ok("POST /api/v1/research/stream -> 200")
                else:
                    fail("POST /api/v1/research/stream -> " + str(response.status_code))
                    return False

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type", "unknown")
                    event_counts[etype] = event_counts.get(etype, 0) + 1
                    content = event.get("content", "")
                    preview = content[:80].replace("\n", " ") if content else ""

                    if etype == "task_created":
                        print("    " + DIM + "[task_created] task_id=" + str(event.get("task_id")) + RESET)
                    elif etype == "status":
                        print("    " + CYAN + "[status]" + RESET + " " + preview)
                    elif etype == "think":
                        print("    " + YELLOW + "[think]" + RESET + " " + preview[:60] + "...")
                    elif etype == "tool_start":
                        print("    " + GREEN + "[tool_start]" + RESET + " " + str(event.get("tool", "?")))
                    elif etype == "tool_response":
                        tool = event.get("tool", "?")
                        print("    " + GREEN + "[tool_response]" + RESET + " %s (%d chars)" % (tool, len(content)))
                    elif etype == "answer":
                        print("    " + BOLD + "[answer]" + RESET + " " + preview[:60] + "...")
                    elif etype == "final_answer":
                        final_answer = content
                        iters = event.get("iterations", "?")
                        term = event.get("termination", "?")
                        print("    " + GREEN + "[final_answer]" + RESET + " iterations=%s, termination=%s" % (iters, term))
                    elif etype == "error":
                        print("    " + RED + "[error]" + RESET + " " + preview)

        elapsed = time.time() - t0
        print()
        dim("Total time: %.1fs" % elapsed)
        dim("Events: " + json.dumps(event_counts))

        total_events = sum(event_counts.values())
        if total_events > 0:
            ok("Received %d SSE events" % total_events)
        else:
            fail("No SSE events received")

        if "status" in event_counts:
            ok("Got %d status events" % event_counts["status"])
        else:
            fail("No status events")

        if final_answer:
            ok("Got final_answer (%d chars)" % len(final_answer))
            print()
            print("  " + BOLD + "--- Answer Preview ---" + RESET)
            print("  " + final_answer[:300] + "...")
        else:
            fail("No final_answer received")

        return total_events > 0

    except Exception as e:
        fail("Stream failed: " + str(e))
        return False


# ── Test 3: Async + Polling ──────────────────────────────
async def test_async(base_url, question):
    header("Test 3: Async Research + Polling")
    dim("Question: " + question)
    print()

    try:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            resp = await client.post(
                base_url + "/api/v1/research/async",
                json={"question": question, "max_iterations": 3},
            )
            data = resp.json()
            if resp.status_code == 200:
                ok("POST /api/v1/research/async -> 200")
            else:
                fail("POST /api/v1/research/async -> " + str(resp.status_code))
                return False

            task_id = data.get("task_id")
            if not task_id:
                fail("No task_id in response")
                return False
            dim("task_id: " + task_id)
            ok("Task created: " + str(data.get("status")))

            dim("Polling for completion (max 60s)...")
            for i in range(12):
                await asyncio.sleep(5)
                sr = await client.get(base_url + "/api/v1/research/" + task_id + "/status")
                if sr.status_code == 200:
                    sd = sr.json()
                    s = sd.get("status", "unknown")
                    it = sd.get("current_iteration", "?")
                    print("    [%ds] status=%s, iteration=%s" % ((i + 1) * 5, s, it))
                    if s == "completed":
                        ok("Task completed!")
                        rr = await client.get(base_url + "/api/v1/research/" + task_id)
                        answer = rr.json().get("answer", "")
                        if answer:
                            ok("Answer received (%d chars)" % len(answer))
                        else:
                            fail("Empty answer")
                        return True
                    elif s == "failed":
                        fail("Task failed: " + str(sd.get("termination_reason")))
                        return False

            fail("Polling timeout (60s)")
            return False

    except Exception as e:
        fail("Async research failed: " + str(e))
        return False


# ── Test 4: Sync ─────────────────────────────────────────
async def test_sync(base_url, question):
    header("Test 4: Sync Research (blocking)")
    dim("Question: " + question)
    dim("This may take 30-120 seconds...")
    print()

    t0 = time.time()
    try:
        async with httpx.AsyncClient(verify=False, timeout=300) as client:
            resp = await client.post(
                base_url + "/api/v1/research",
                json={"question": question, "max_iterations": 3},
            )
            elapsed = time.time() - t0
            data = resp.json()
            if resp.status_code == 200:
                ok("POST /api/v1/research -> 200 (%.1fs)" % elapsed)
            else:
                fail("POST /api/v1/research -> " + str(resp.status_code))
            answer = data.get("answer", "")
            if answer:
                ok("Answer received (%d chars)" % len(answer))
                print()
                print("  " + BOLD + "--- Answer Preview ---" + RESET)
                print("  " + answer[:300] + "...")
            else:
                fail("Empty answer")
            return resp.status_code == 200 and len(answer) > 0

    except httpx.ReadTimeout:
        fail("Request timed out (300s)")
        return False
    except Exception as e:
        fail("Sync failed: " + str(e))
        return False


# ── Test 5: History ──────────────────────────────────────
async def test_history(base_url, question):
    header("Test 5: Research History")
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            resp = await client.get(base_url + "/api/v1/research/history")
            data = resp.json()
            if resp.status_code == 200:
                ok("GET /api/v1/research/history -> 200")
            else:
                fail("GET /api/v1/research/history -> " + str(resp.status_code))
            if isinstance(data, list):
                ok("History is list: %d items" % len(data))
                if data:
                    latest = data[0]
                    s = latest.get("status", "?")
                    q = latest.get("question", "")[:50]
                    dim("Latest: [%s] %s..." % (s, q))
            else:
                fail("History is not a list")
            return resp.status_code == 200
    except Exception as e:
        fail("History failed: " + str(e))
        return False


# ── Main ─────────────────────────────────────────────────
TEST_MAP = {
    "health": test_health,
    "stream": test_stream,
    "async": test_async,
    "sync": test_sync,
    "history": test_history,
}


async def main():
    parser = argparse.ArgumentParser(description="xSmartDeepResearch API Test")
    parser.add_argument("--host", default=DEFAULT_HOST, help="API base URL")
    parser.add_argument("--test", choices=list(TEST_MAP.keys()), help="Run specific test")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="Test question")
    args = parser.parse_args()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print(BOLD + "xSmartDeepResearch API Integration Test" + RESET)
    dim("Target: " + args.host)
    dim("Time:   " + now_str)

    if args.test:
        tests = {args.test: TEST_MAP[args.test]}
    else:
        tests = {"health": test_health, "stream": test_stream, "history": test_history}

    results = {}
    for name, fn in tests.items():
        try:
            results[name] = await fn(args.host, args.question)
        except KeyboardInterrupt:
            print("\n  " + YELLOW + "Interrupted" + RESET)
            results[name] = False
            break

    # Summary
    header("Test Summary")
    passed = 0
    for name, p in results.items():
        icon = GREEN + "PASS" + RESET if p else RED + "FAIL" + RESET
        print("  [%s] %s" % (icon, name))
        if p:
            passed += 1

    total = len(results)
    print()
    print("  " + BOLD + "%d/%d tests passed" % (passed, total) + RESET)
    print()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
