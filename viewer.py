"""
GitHub Profile Viewer - Core Logic Module

A Selenium-based tool to simulate profile views on GitHub.

Created by: dewhush
"""

import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache the driver path once to avoid repeated calls to manager
_DRIVER_PATH: Optional[str] = None


@dataclass
class ViewResult:
    """Result of a single view operation."""
    success: bool
    visit_id: int
    error: Optional[str] = None


@dataclass
class BatchViewResult:
    """Result of a batch view operation."""
    username: str
    total_count: int
    success_count: int
    failed_count: int
    status: str


def _get_driver_path() -> str:
    """Get or initialize the cached ChromeDriver path."""
    global _DRIVER_PATH
    if _DRIVER_PATH is None:
        _DRIVER_PATH = ChromeDriverManager().install()
    return _DRIVER_PATH


class GitHubProfileVisitor:
    """Selenium-based GitHub profile visitor with anti-detection features."""
    
    def __init__(self):
        """Initialize the Chrome WebDriver with optimized settings."""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        
        # Anti-detection settings
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance optimizations
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.page_load_strategy = 'eager'
        
        # User agent
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Initialize driver
        driver_path = _get_driver_path()
        self.driver = webdriver.Chrome(
            service=Service(driver_path),
            options=self.chrome_options
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    def _simulate_scroll(self) -> None:
        """Simulate human-like scrolling behavior."""
        try:
            scroll_amounts = [random.randint(300, 700) for _ in range(2)]
            for amount in scroll_amounts:
                self.driver.execute_script(f"window.scrollBy(0, {amount});")
                time.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass
    
    def visit_profile(self, username: str) -> bool:
        """
        Visit a GitHub profile.
        
        Args:
            username: GitHub username to visit
            
        Returns:
            True if visit was successful, False otherwise
        """
        url = f"https://github.com/{username}"
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simulate human interaction
            self._simulate_scroll()
            time.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            logger.error(f"Error visiting {username}: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """Close the browser and clean up resources."""
        try:
            self.driver.quit()
        except Exception:
            pass


def _execute_single_visit(
    username: str,
    visit_id: int,
    total_visits: int
) -> ViewResult:
    """
    Execute a single profile visit.
    
    Args:
        username: Target GitHub username
        visit_id: Current visit number
        total_visits: Total number of visits planned
        
    Returns:
        ViewResult with success status
    """
    visitor = None
    try:
        visitor = GitHubProfileVisitor()
        success = visitor.visit_profile(username)
        
        if success:
            logger.info(f"[+] Visit {visit_id}/{total_visits} success")
        else:
            logger.info(f"[-] Visit {visit_id}/{total_visits} failed")
            
        return ViewResult(success=success, visit_id=visit_id)
        
    except Exception as e:
        logger.error(f"Error in visit {visit_id}: {e}")
        return ViewResult(success=False, visit_id=visit_id, error=str(e))
        
    finally:
        if visitor:
            visitor.cleanup()


def execute_batch_views(
    username: str,
    view_count: int,
    max_workers: int = 5
) -> BatchViewResult:
    """
    Execute multiple profile views concurrently.
    
    Args:
        username: Target GitHub username
        view_count: Number of views to generate
        max_workers: Maximum concurrent threads (default: 5)
        
    Returns:
        BatchViewResult with aggregated results
    """
    # Pre-initialize driver path
    _get_driver_path()
    
    logger.info(f"Starting batch view: @{username} | Views: {view_count} | Threads: {max_workers}")
    
    success_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_execute_single_visit, username, i + 1, view_count)
            for i in range(view_count)
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result.success:
                success_count += 1
    
    failed_count = view_count - success_count
    status = "completed" if success_count > 0 else "failed"
    
    logger.info(f"Batch complete: {success_count}/{view_count} successful")
    
    return BatchViewResult(
        username=username,
        total_count=view_count,
        success_count=success_count,
        failed_count=failed_count,
        status=status
    )
