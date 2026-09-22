"""공공 사이트 접근성 프로브.

GitHub Actions 러너(해외 IP)와 국내 PC에서 같은 대상 목록을 호출해 결과를 비교한다.
해외 IP 차단·TLS 체인 오류·봇 차단 페이지를 크롤러 구현 전에 확인하는 용도.

    python scripts/probe_access.py --label local-kr
    python scripts/probe_access.py --label github-actions --summary "$GITHUB_STEP_SUMMARY"

표준 라이브러리만 사용한다(러너에서 의존성 설치 없이 실행).
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

USER_AGENT = "pledge-tracker-probe/0.1 (+https://github.com/khkim3115/pledge-tracker)"
BLOCK_STATUSES = {401, 403, 406, 429, 451, 503}
BLOCK_MARKERS = (
    "access denied",
    "request rejected",
    "captcha",
    "비정상적인 접근",
    "접근이 차단",
    "접근이 제한",
    "해외 ip",
    "해외에서",
)
BODY_SAMPLE_BYTES = 64 * 1024


@dataclass
class ProbeResult:
    name: str
    url: str
    verdict: str  # ok | suspect | blocked | tls_error | timeout | error
    status: int | None
    final_url: str | None
    elapsed_ms: int
    content_type: str | None
    body_bytes: int | None
    detail: str


def probe(name: str, url: str, timeout: float, expect: frozenset[int] = frozenset()) -> ProbeResult:
    """expect: 정상으로 볼 HTTP 상태 (예: 키 없이 호출한 API의 401 = 서버 도달 확인)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    started = time.monotonic()

    def done(verdict, detail, status=None, final_url=None, ctype=None, size=None):
        elapsed = int((time.monotonic() - started) * 1000)
        return ProbeResult(name, url, verdict, status, final_url, elapsed, ctype, size, detail)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(BODY_SAMPLE_BYTES)
            status, final_url = resp.status, resp.geturl()
            ctype = resp.headers.get("Content-Type")
    except urllib.error.HTTPError as e:
        body = e.read(BODY_SAMPLE_BYTES) if e.fp else b""
        status, final_url, ctype = e.code, e.geturl(), e.headers.get("Content-Type")
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLError):
            return done("tls_error", f"{type(reason).__name__}: {reason}")
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return done("timeout", f"no response within {timeout}s")
        return done("error", f"{type(reason).__name__}: {reason}")
    except TimeoutError:
        return done("timeout", f"no response within {timeout}s")
    except (ConnectionError, OSError) as e:
        return done("error", f"{type(e).__name__}: {e}")

    text = body.decode("utf-8", errors="ignore").lower()
    marker = next((m for m in BLOCK_MARKERS if m in text), None)
    if status in expect:
        verdict = "ok"
        detail = f"expected HTTP {status}"
    elif status in BLOCK_STATUSES:
        verdict = "blocked"
        detail = f"HTTP {status}" + (f", marker '{marker}'" if marker else "")
    elif marker:
        verdict = "suspect"
        detail = f"block marker '{marker}' in body"
    elif status >= 400:
        verdict = "error"
        detail = f"HTTP {status}"
    else:
        verdict = "ok"
        detail = ""
    return done(verdict, detail, status, final_url, ctype, len(body))


def to_markdown(label: str, results: list[ProbeResult]) -> str:
    lines = [
        f"### 접근성 프로브 — `{label}`",
        "",
        "| 대상 | 판정 | HTTP | 응답(ms) | 비고 |",
        "| :- | :- | -: | -: | :- |",
    ]
    for r in results:
        note = r.detail.replace("|", "\\|")[:120]
        status = r.status if r.status is not None else "-"
        lines.append(f"| [{r.name}]({r.url}) | {r.verdict} | {status} | {r.elapsed_ms} | {note} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--targets", type=Path, default=here / "probe_targets.json")
    ap.add_argument("--label", default="local")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--out", type=Path, help="결과 JSON 저장 경로")
    ap.add_argument(
        "--summary", type=Path, help="Markdown 표를 덧붙일 파일 (예: $GITHUB_STEP_SUMMARY)"
    )
    ap.add_argument("--strict", action="store_true", help="ok가 아닌 대상이 있으면 exit 1")
    args = ap.parse_args()

    targets = json.loads(args.targets.read_text(encoding="utf-8"))["targets"]
    results = [
        probe(t["name"], t["url"], args.timeout, frozenset(t.get("expect_status", [])))
        for t in targets
    ]

    report = {
        "label": args.label,
        "probed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "results": [asdict(r) for r in results],
    }
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = to_markdown(args.label, results)
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as f:
            f.write(md)
    sys.stdout.reconfigure(encoding="utf-8")
    print(md)

    not_ok = [r for r in results if r.verdict != "ok"]
    return 1 if args.strict and not_ok else 0


if __name__ == "__main__":
    sys.exit(main())
