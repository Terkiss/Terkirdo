---
name: universal-crawler
description: 도메인에 종속되지 않는 합법적·복원력(Resilience) 중심의 범용 웹 데이터 수집 파이프라인을 제공하는 스킬. 공식 API·피드·구조화 문서를 최우선 활용하며, UltimateMake Phase 2의 초심층 웹 리서치나 대규모 기술 문서 수집 시 표준 수집기를 제작/운용할 때 적용한다.
---

# Universal Web Data Collection & Resilience Pipeline

공개된 기술 문서, 표준 규격(RFC, W3C, ISO), 공식 블로그, 오픈소스 레퍼런스를 안정적이고 정중하게 수집하기 위한 **범용 웹 데이터 수집 및 복원력(Resilience) 파이프라인**입니다. `UltimateMake`의 Phase 2 (초심층 웹 탐색) 및 합법적 공개 자료 수집 시 표준 템플릿으로 활용합니다.

---

## 0. 최우선 원칙 및 안전 중단 불변식 (Governance & Safety Invariants)

### 0-1. 공식·구조화 소스 최우선 원칙 (Sanctioned & Structured Sources First)
커스텀 HTML 크롤러를 작성하기 전에 반드시 아래의 공식·구조화 데이터 경로를 0순위로 탐색합니다:
1. **공식 Open API / REST·GraphQL 엔드포인트** (예: GitHub REST API, PyPI/npm/Crates 메타데이터 API, 공식 문서 검색 API)
2. **구조화 피드 및 인덱스**: RSS/Atom 피드, `sitemap.xml`, `llms.txt`, `llms-full.txt`, 원시 마크다운(`raw.githubusercontent.com`)
3. **정책 확인**: 수집 착수 전 대상 도메인의 `robots.txt` 규칙(`urllib.robotparser`)과 서비스 이용약관(ToS)을 확인하고 준수합니다.

### 0-2. 안전 중단 불변식 (Anti-Bot & CAPTCHA Strict Stop Rule)
> **[CRITICAL SAFETY INVARIANT]**
>
> 데이터 수집 중 **CAPTCHA(reCAPTCHA, hCaptcha 등), Cloudflare Turnstile, "사람인지 확인(Verify you are human)", Proof-of-Work 안티봇 챌린지, 또는 인증·접근통제(401/403 Paywall·Login Gate) 장벽**을 마주치면, **어떠한 도구(헤드리스 브라우저 조작, 핑거프린트/헤더 스푸핑, 프록시 우회, 캐시/대체 URL 우회 등)로도 해결하거나 우회하려 시도하지 마십시오.**
> 즉시 해당 대상에 대한 수집을 **중단(STOP)**하고, 차단 상태(HTTP 상태 코드, 챌린지 유형)와 대상 URL을 주인님께 정직하게 보고하십시오.

---

## 1. 정중한 요청 정책 (Polite HTTP & Adaptive Rate Limiting)

서버에 과부하를 주지 않도록 투명하고 표준적인 HTTP 세션 헤더를 설정하며, `429 Too Many Requests` 및 `Retry-After` 응답 헤더를 엄격히 존중합니다.

### 1-1. 표준 세션 헤더 구성 (Transparent & Standard HTTP Headers)

```python
def get_standard_headers(contact_agent: str = "TerukirdoResearchClient/1.0") -> dict[str, str]:
    """투명하고 표준적인 HTTP 요청 헤더를 반환합니다 (랜덤 UA 스푸핑 금지)."""
    return {
        "User-Agent": contact_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
```

### 1-2. `Retry-After` 존중 지수 백오프 레이트 리미터 (`AdaptiveRateLimiter`)

```python
import random
import time
from email.utils import parsedate_to_datetime
from typing import Optional


class AdaptiveRateLimiter:
    """서버 부하 방지 및 Retry-After 헤더를 존중하는 적응형 속도 제한기."""

    def __init__(self, base_delay: float = 1.5, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.max_delay = max_delay

    def wait(self, retry_after_header: Optional[str] = None) -> None:
        if retry_after_header:
            parsed_wait = self._parse_retry_after(retry_after_header)
            if parsed_wait is not None:
                time.sleep(min(parsed_wait, self.max_delay))
                return
        jitter = random.uniform(0.9, 1.15)
        time.sleep(self.current_delay * jitter)

    def backoff(self) -> None:
        self.current_delay = min(self.current_delay * 2.0, self.max_delay)

    def reset(self) -> None:
        self.current_delay = self.base_delay

    @staticmethod
    def _parse_retry_after(value: str) -> Optional[float]:
        value = value.strip()
        if value.isdigit():
            return float(value)
        try:
            dt = parsedate_to_datetime(value)
            delta = (dt.timestamp() - time.time())
            return max(0.0, delta)
        except Exception:
            return None
```

---

## 2. 복원력 기반 수집 베이스 클래스 (`ResilientCollectorBase`)

공개 기술 문서, RFC, 블로그 수집 시 네트워크 일시 오류(5xx, 타임아웃)에만 정중하게 재시도하고, 접근통제(401/403)나 안티봇 챌린지 감지 시 즉시 중단·기록하는 베이스 클래스입니다.

```python
import logging
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHALLENGE_MARKERS = (
    "cf-turnstile",
    "verify you are human",
    "g-recaptcha",
    "hcaptcha",
    "just a moment...",
)


class ChallengeOrAccessBlockedError(RuntimeError):
    """안티봇 챌린지 또는 접근통제 장벽 감지 시 즉시 중단하기 위한 예외."""


class ResilientCollectorBase:
    def __init__(self, user_agent: str = "TerukirdoResearchClient/1.0"):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update(get_standard_headers(user_agent))
        self.rate_limiter = AdaptiveRateLimiter()
        self._robots_cache: dict[str, RobotFileParser] = {}
        self.blocked_urls: list[tuple[str, str]] = []

    def is_allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(f"{origin}/robots.txt")
            try:
                rp.read()
            except Exception:
                pass
            self._robots_cache[origin] = rp
        rp = self._robots_cache[origin]
        return rp.can_fetch(self.user_agent, url) if rp.default_entry or rp.entries else True

    @staticmethod
    def _contains_challenge(html_head: str) -> bool:
        lowered = html_head.lower()
        return any(marker in lowered for marker in CHALLENGE_MARKERS)

    def fetch(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """robots.txt 준수, Retry-After 반영, 챌린지 즉시 중단이 적용된 안전한 수집 메서드."""
        if not self.is_allowed_by_robots(url):
            reason = "Disallowed by robots.txt"
            logger.warning(f"[STOP] {reason}: {url}")
            self.blocked_urls.append((url, reason))
            return None

        retry_after: Optional[str] = None
        for attempt in range(1, max_retries + 1):
            self.rate_limiter.wait(retry_after_header=retry_after)
            retry_after = None
            try:
                response = self.session.get(url, timeout=15, allow_redirects=True)

                if response.status_code in (401, 403):
                    reason = f"HTTP {response.status_code} Access Control / Anti-Bot Gate"
                    logger.error(f"[STOP] 접근통제 또는 차단 장벽 감지 — 우회 금지, 즉시 중단: {url}")
                    self.blocked_urls.append((url, reason))
                    raise ChallengeOrAccessBlockedError(f"{reason}: {url}")

                if self._contains_challenge(response.text[:4096]):
                    reason = "Anti-bot / CAPTCHA challenge detected in response"
                    logger.error(f"[STOP] 챌린지 페이지 감지 — 즉시 수집 중단 및 보고 필요: {url}")
                    self.blocked_urls.append((url, reason))
                    raise ChallengeOrAccessBlockedError(f"{reason}: {url}")

                if response.status_code == 200:
                    self.rate_limiter.reset()
                    return response

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    logger.warning(f"[429] Rate limited on {url} (attempt {attempt}/{max_retries}). Respecting Retry-After.")
                    self.rate_limiter.backoff()
                    continue

                if 500 <= response.status_code < 600:
                    logger.warning(f"[{response.status_code}] Transient server error on {url} (attempt {attempt}/{max_retries}).")
                    self.rate_limiter.backoff()
                    continue

                logger.error(f"[{response.status_code}] Non-retryable HTTP status: {url}")
                return None

            except ChallengeOrAccessBlockedError:
                raise
            except requests.RequestException as exc:
                logger.warning(f"Network error on {url} (attempt {attempt}/{max_retries}): {exc}")
                self.rate_limiter.backoff()

        logger.error(f"Max retries exhausted for transient errors: {url}")
        return None
```

---

## 3. 데이터 파싱 표준화 (`BeautifulSoup` / `lxml`)

수집된 정적 HTML 문서에서 불필요한 내비게이션·스크립트 노이즈를 제거하고 본문 텍스트만 추출할 때 `lxml` 파서를 권장합니다.

```python
from bs4 import BeautifulSoup


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for noisy_tag in soup(["script", "style", "noscript", "nav", "footer"]):
        noisy_tag.decompose()
    container = soup.select_one("article") or soup.select_one("main") or soup.select_one("body")
    return container.get_text(separator="\n", strip=True) if container else ""
```

---

## 4. 정당한 CSR/SPA 동적 렌더링 (`Standard Playwright Headless`)

안티봇 우회 목적이 아니라, 공개된 API 문서(예: Swagger/Redoc, SPA 기반 기술 레퍼런스)가 순수 클라이언트 사이드 렌더링(CSR)으로만 본문을 구성하는 경우에 한해 표준 `playwright.sync_api`를 사용합니다. 렌더링 도중 안티봇 챌린지나 인증 게이트가 감지되면 즉시 예외를 발생시켜 중단합니다.

```python
from playwright.sync_api import sync_playwright


def render_csr_documentation(url: str, content_selector: str, timeout_ms: int = 10000) -> str:
    """순수 CSR 공개 기술 문서 렌더링 전용. 챌린지 감지 시 즉시 중단(ChallengeOrAccessBlockedError)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            if response is not None and response.status in (401, 403):
                raise ChallengeOrAccessBlockedError(
                    f"HTTP {response.status} access barrier encountered at {url}; stopping immediately."
                )

            head_sample = page.content()[:4096].lower()
            if any(marker in head_sample for marker in CHALLENGE_MARKERS):
                raise ChallengeOrAccessBlockedError(
                    f"Anti-bot or CAPTCHA challenge detected at {url}; stopping immediately for user report."
                )

            page.wait_for_selector(content_selector, timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()
```
