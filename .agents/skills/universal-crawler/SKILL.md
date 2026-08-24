---
name: universal-crawler
description: 도메인에 종속되지 않는 범용 웹 크롤링 파이프라인과 차단 방어 방법론을 제공하는 스킬. UltimateMake Phase 2의 초심층 웹 리서치나 대규모 데이터 수집 시 크롤러를 제작/운용할 때 적용한다.
---

# Universal Web Crawler Skill

어떤 도메인이나 웹사이트든 안정적으로 수집할 수 있는 **범용 웹 크롤링 파이프라인 및 차단 우회(Anti-Block) 방법론**입니다. `UltimateMake`의 Phase 2 (초심층 웹 탐색) 및 대규모 기술 자료 수집 시 표준 크롤러 템플릿으로 활용합니다.

## 1. 차단 방어 (Anti-Block) 기본 원칙

IP 차단, Rate Limit, Captcha, Fingerprint 기반 차단을 회피하기 위한 기본 전략입니다.

### 1-1. 헤더 인간화 (Header Humanization)
가장 기본적이고 필수적인 회피 방법입니다. 단순 `User-Agent` 외에도 실제 브라우저가 보내는 상세 헤더를 일치시켜야 합니다.

```python
from fake_useragent import UserAgent

def get_universal_headers():
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
```

### 1-2. 지수 백오프 및 랜덤 딜레이 (Adaptive Delay)
고정된 딜레이는 봇으로 감지될 확률을 높입니다.

```python
import time
import random

class AdaptiveRateLimiter:
    def __init__(self, base_delay=2.0, max_delay=30.0):
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.max_delay = max_delay
        
    def wait(self):
        jitter = random.uniform(0.8, 1.2)
        time.sleep(self.current_delay * jitter)
        
    def increase_delay(self):
        self.current_delay = min(self.current_delay * 2, self.max_delay)
        
    def reset_delay(self):
        self.current_delay = self.base_delay
```

## 2. 범용 크롤러 클래스 템플릿

특정 기술 문서, RFC, GitHub 저장소, 기술 블로그를 크롤링할 때 사용할 수 있는 베이스 클래스입니다.

```python
import requests
import random
import time
import logging
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalCrawlerBase:
    def __init__(self, use_proxy=False):
        self.session = requests.Session()
        self.rate_limiter = AdaptiveRateLimiter()
        self.use_proxy = use_proxy
        self.failed_urls = []
        
    def get_proxies(self) -> Optional[Dict]:
        """프록시 풀에서 랜덤 프록시 반환. 필요시 오버라이드."""
        if not self.use_proxy:
            return None
        return {"http": "http://your_proxy", "https": "http://your_proxy"}
        
    def fetch(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """자동 재시도, 딜레이, 헤더, 프록시가 적용된 범용 요청 메서드"""
        headers = get_universal_headers()
        proxies = self.get_proxies()
        
        for attempt in range(max_retries):
            self.rate_limiter.wait()
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    proxies=proxies,
                    timeout=15,
                    allow_redirects=True
                )
                
                # 상태 코드 핸들링
                if response.status_code == 200:
                    self.rate_limiter.reset_delay()
                    return response
                elif response.status_code in [403, 429]:
                    logger.warning(f"[{response.status_code}] 차단 감지. 딜레이 증가. ({url})")
                    self.rate_limiter.increase_delay()
                else:
                    logger.error(f"[{response.status_code}] 에러 발생: {url}")
                    
            except requests.RequestException as e:
                logger.error(f"Request Error on {url}: {e}")
                self.rate_limiter.increase_delay()
                
        logger.error(f"최대 재시도 초과: {url}")
        self.failed_urls.append(url)
        return None
```

## 3. 데이터 파싱 표준화 (BeautifulSoup / lxml)

수집된 HTML의 DOM을 파싱할 때 견고한 파서인 `lxml` 백엔드를 권장합니다.

```python
from bs4 import BeautifulSoup

def parse_html(html: str):
    soup = BeautifulSoup(html, 'lxml')
    item = soup.select_one('article') or soup.select_one('main') or soup.select_one('body')
    return item.get_text(separator="\n", strip=True) if item else ""
```

## 4. 동적 페이지(SPA/JS Rendering) 대응 (최후 수단)

API가 노출되지 않은 순수 CSR 페이지이거나 Cloudflare가 적용된 경우 브라우저 에뮬레이션을 사용합니다.

```python
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_dynamic_content(url: str, wait_selector: str):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
        )
        return driver.page_source
    finally:
        driver.quit()
```
