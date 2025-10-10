#!/usr/bin/env python3
"""
LinkedIn Comment Deleter
Automatically deletes your LinkedIn comments from your recent activity (comments) page.
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInCommentDeleter:
    def __init__(self, headless: bool = False):
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self) -> None:
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            logger.info("Make sure you have ChromeDriver installed and in your PATH")
            sys.exit(1)
    
    def wait_for_page_load(self, timeout: int = 10) -> None:
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("Page load timeout, continuing anyway...")
    
    def check_for_network_error(self) -> bool:
        try:
            error_selectors = [
                "//*[contains(text(), 'Error with your network')]",
                "//*[contains(text(), 'Something went wrong')]",
                "//*[contains(text(), 'Please try again')]",
                "//*[contains(text(), 'Network error')]",
                "//*[contains(text(), 'Connection error')]",
                ".feed-shared-error-message",
                "[data-test-id*='error']",
                ".error-message"
            ]
            for selector in error_selectors:
                try:
                    if selector.startswith("//"):
                        error_element = self.driver.find_element(By.XPATH, selector)
                    else:
                        error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if error_element.is_displayed():
                        logger.warning("Network error detected, waiting and retrying...")
                        time.sleep(5)
                        self.driver.refresh()
                        time.sleep(3)
                        self.wait_for_page_load()
                        logger.info("Page refreshed after network error")
                        return True
                except NoSuchElementException:
                    continue
            return False
        except Exception as e:
            logger.warning(f"Error checking for network error: {e}")
            return False

    def delete_comment(self, comment_element) -> bool | str:
        """Delete a single comment via its overflow menu.
        Returns: True if deleted, False if failed, 'restricted' if no delete option.
        """
        try:
            menu_button = None
            comment_menu_attempts = [
                ("css", "button[aria-label*='Open options'][aria-label*='comment']"),
                ("css", "button[aria-label*='options'][aria-label*='comment']"),
                ("xpath", ".//button[contains(@aria-label, 'options') and contains(@aria-label, 'comment')]") ,
                ("xpath", ".//button[.//svg[@data-test-icon='overflow-web-ios-small']]"),
                ("css", "button.comment-options-dropdown__dropdown-trigger"),
                ("css", ".comment-options-dropdown__trigger, .comment-options-dropdown__trigger-icon")
            ]
            for strategy, selector in comment_menu_attempts:
                try:
                    if strategy == "css":
                        el = comment_element.find_element(By.CSS_SELECTOR, selector)
                    else:
                        el = comment_element.find_element(By.XPATH, selector)
                    if el and el.is_displayed():
                        menu_button = el
                        logger.info(f"Found comment menu via {strategy}: {selector}")
                        break
                except NoSuchElementException:
                    continue
            if not menu_button:
                logger.error("Could not find overflow menu for comment")
                return False
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_button)
            time.sleep(0.5)
            try:
                menu_button.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", menu_button)
            # Wait for menu to appear with more specific selectors
            try:
                WebDriverWait(self.driver, 3).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".artdeco-dropdown__content, [role='menu'], .feed-shared-control-menu__content")) > 0
                )
                logger.info("Comment options menu appeared")
            except TimeoutException:
                logger.warning("Comment options menu did not appear in time")
            
            # Wait a bit more for menu to fully render
            time.sleep(1)
            
            # Try to find delete button with more comprehensive selectors
            delete_button = None
            delete_option_attempts = [
                # Try specific LinkedIn comment delete selectors
                ("css", ".artdeco-dropdown__content button[data-control-name='delete_comment']"),
                ("css", ".artdeco-dropdown__content button[data-control-name='delete']"),
                ("css", "[role='menu'] button[data-control-name='delete_comment']"),
                ("css", "[role='menu'] button[data-control-name='delete']"),
                # Try text-based selectors
                ("xpath", "//div[@class='artdeco-dropdown__content']//button[contains(., 'Delete')]"),
                ("xpath", "//div[@role='menu']//button[contains(., 'Delete')]"),
                ("xpath", "//button[contains(., 'Delete comment')]"),
                ("xpath", "//button[contains(., 'Delete')]"),
                # Try any button with delete in aria-label
                ("xpath", "//button[contains(@aria-label, 'Delete')]"),
                # Try any clickable element with delete text
                ("xpath", "//*[contains(., 'Delete') and (self::button or self::a or self::div[@role='button'])]")
            ]
            
            for strategy, selector in delete_option_attempts:
                try:
                    if strategy == "css":
                        delete_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    else:
                        delete_button = self.driver.find_element(By.XPATH, selector)
                    
                    if delete_button and delete_button.is_displayed():
                        logger.info(f"Found delete option using {strategy}: {selector}")
                        break
                    else:
                        delete_button = None
                except NoSuchElementException:
                    continue
            
            if not delete_button:
                logger.info("No delete option found for this comment (likely not your comment)")
                # Close the menu by clicking elsewhere
                try:
                    self.driver.execute_script("document.activeElement && document.activeElement.blur();")
                    # Click on a safe area to close menu
                    self.driver.execute_script("document.body.click();")
                except Exception:
                    pass
                return 'restricted'
            
            # Scroll delete button into view and wait
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", delete_button)
            time.sleep(0.5)
            
            # Try to click delete button with better error handling
            try:
                logger.info("Attempting to click delete button...")
                delete_button.click()
                logger.info("Successfully clicked delete button")
            except Exception as e:
                logger.warning(f"Regular click failed: {e}, trying JavaScript click")
                try:
                    self.driver.execute_script("arguments[0].click();", delete_button)
                    logger.info("Successfully clicked delete button with JavaScript")
                except Exception as e2:
                    logger.error(f"JavaScript click also failed: {e2}")
                    return False
            
            # Wait for confirmation dialog to appear
            time.sleep(0.3)
            try:
                confirm_selectors = [
                    ("css", "button.feed-components-shared-decision-modal__confirm-button.artdeco-button.artdeco-button--primary.artdeco-button--2"),
                    ("xpath", "//div[@role='dialog']//button[contains(@class, 'artdeco-button--primary') and (contains(., 'Delete') or contains(., 'Confirm') or contains(., 'Yes'))]")
                ]
                confirm_button = None
                for strategy, selector in confirm_selectors:
                    try:
                        if strategy == "css":
                            confirm_button = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        else:
                            confirm_button = WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except TimeoutException:
                        continue
                if confirm_button:
                    try:
                        confirm_button.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", confirm_button)
                else:
                    logger.warning("No confirmation modal found; assuming deletion proceeded")
                time.sleep(1)
                logger.info("Comment deleted")
                return True
            except Exception as e:
                logger.warning(f"Error confirming deletion: {e}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete comment: {e}")
            return False

    def initial_scroll_loading(self, scroll_rounds: int = 5, scroll_delay: int = 2) -> None:
        logger.info(f"Performing initial scrolling to load more comments ({scroll_rounds} rounds)...")
        for i in range(scroll_rounds):
            logger.info(f"Initial scroll round {i+1}/{scroll_rounds}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            if self.check_for_network_error():
                logger.info("Network error handled during initial scrolling...")
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"Page height after scroll {i+1}: {current_height}")
        logger.info("Initial scrolling complete, starting comment processing...")

    def process_comments(self, max_comments: int | None = None, initial_scroll_rounds: int = 5) -> None:
        logger.info("Starting to process comments...")
        self.wait_for_page_load()
        time.sleep(3)
        self.initial_scroll_loading(scroll_rounds=initial_scroll_rounds)
        deleted_count = 0
        restricted_count = 0
        processed_count = 0
        consecutive_failures = 0
        refresh_interval = 200  # Refresh page every 50 successful deletes
        while True:
            comment_selectors = [
                "li.comments-comments-list__comment-item",
                "article.comments-comment-item",
                "div.comments-comment-item",
                "div.update-components-comment",
                "[data-test-id*='comment']",
                "[data-id*='comment']"
            ]
            comments = []
            for selector in comment_selectors:
                try:
                    comments = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comments:
                        logger.info(f"Found {len(comments)} comments using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            if not comments:
                logger.warning("No comments found on the page")
                break
            for i, comment in enumerate(comments):
                if max_comments and processed_count >= max_comments:
                    logger.info(f"Reached maximum comments limit ({max_comments}), stopping processing")
                    return
                processed_count += 1
                try:
                    logger.info(f"Processing comment {processed_count} (page comment {i+1}/{len(comments)})")
                    if self.check_for_network_error():
                        logger.info("Network error handled, continuing with comment processing...")
                    
                    # Skip the first comment (preserve it)
                    if i == 0:
                        logger.info("Skipping first comment (preserved)")
                        continue
                    
                    logger.info("Attempting to delete comment...")
                    max_retries = 2
                    deleted = False
                    is_restricted = False
                    for retry in range(max_retries):
                        result = self.delete_comment(comment)
                        if result == True:
                            deleted_count += 1
                            logger.info(f"Successfully deleted comment {processed_count}")
                            deleted = True
                            consecutive_failures = 0
                            
                            # Check if we need to refresh the page
                            if deleted_count % refresh_interval == 0:
                                logger.info(f"Refreshing page after {deleted_count} successful deletions to clear old posts...")
                                self.driver.refresh()
                                time.sleep(5)  # Wait for page to reload
                                self.wait_for_page_load()
                                
                                # Perform initial scrolling after refresh to reload more content
                                logger.info("Performing post-refresh scrolling to reload more comments...")
                                self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)
                                
                                logger.info("Page refreshed and scrolled, continuing with fresh content...")
                                break  # Break out of current page processing to start fresh
                            
                            break
                        elif result == 'restricted':
                            restricted_count += 1
                            logger.info(f"Comment {processed_count} is restricted (no delete option available)")
                            is_restricted = True
                            consecutive_failures = 0
                            break
                        else:
                            if retry < max_retries - 1:
                                logger.warning(f"Failed to delete comment {processed_count}, retrying... (attempt {retry + 1}/{max_retries})")
                                time.sleep(2)
                            else:
                                logger.warning(f"Failed to delete comment {processed_count} after {max_retries} attempts")
                    if is_restricted:
                        continue
                    if not deleted:
                        consecutive_failures += 1
                        logger.warning(f"Consecutive failures: {consecutive_failures}")
                        if consecutive_failures >= 5:
                            logger.info("Too many consecutive failures, refreshing page to clear stale elements...")
                            self.driver.refresh()
                            time.sleep(5)
                            self.wait_for_page_load()
                            logger.info("Performing post-refresh scrolling to reload more content...")
                            self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)
                            consecutive_failures = 0
                            logger.info("Page refreshed and scrolled, continuing with fresh elements...")
                            break
                        continue
                    time.sleep(2)
                    if self.check_for_network_error():
                        logger.info("Network error handled after deletion...")
                except Exception as e:
                    logger.error(f"Error processing comment {processed_count}: {e}")
                    if self.check_for_network_error():
                        logger.info("Network error handled after exception...")
                    continue
            if max_comments and processed_count >= max_comments:
                logger.info(f"Reached maximum comments limit ({max_comments}), stopping processing")
                break
            logger.info("Scrolling down to load more comments...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            if self.check_for_network_error():
                logger.info("Network error handled after scrolling...")
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if current_height == new_height:
                logger.info("Reached end of page, no more comments to load")
                break
        logger.info(f"Processing complete. Deleted: {deleted_count}, Restricted: {restricted_count}")

    def run(self, url: str, max_comments: int | None = None, initial_scroll_rounds: int = 5) -> None:
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            logger.info("Waiting for page to load...")
            self.wait_for_page_load()
            time.sleep(3)
            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")
            if "login" in current_url.lower() or "auth" in current_url.lower():
                logger.info("Detected login page. Please log in manually.")
            elif "recent-activity" not in current_url.lower():
                logger.warning(f"URL doesn't contain 'recent-activity'. Current URL: {current_url}")
                logger.info("Please navigate to your Recent activity → Comments page")
            input("Press Enter when you're on the correct page and ready to start deleting comments...")
            final_url = self.driver.current_url
            logger.info(f"Final URL before processing: {final_url}")
            self.process_comments(max_comments, initial_scroll_rounds)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main() -> None:
    print("LinkedIn Comment Deleter")
    print("=======================")
    print("This script will help you delete your LinkedIn comments from your activity page.")
    print()
    url = input("Enter LinkedIn URL (or press Enter for default comments page): ").strip()
    if not url:
        url = "https://www.linkedin.com/in/brianahanna/recent-activity/comments/"
    max_comments_input = input("Maximum number of comments to process (or press Enter for all): ").strip()
    max_comments = int(max_comments_input) if max_comments_input.isdigit() else None
    scroll_rounds_input = input("Initial scroll rounds to load more comments (or press Enter for 5): ").strip()
    initial_scroll_rounds = int(scroll_rounds_input) if scroll_rounds_input.isdigit() else 5
    headless_input = input("Run in headless mode? (y/N): ").strip().lower()
    headless = headless_input in ['y', 'yes']
    print(f"\nStarting with URL: {url}")
    if max_comments:
        print(f"Maximum comments to process: {max_comments}")
    print(f"Initial scroll rounds: {initial_scroll_rounds}")
    print(f"Headless mode: {headless}")
    print()
    deleter = LinkedInCommentDeleter(headless=headless)
    deleter.run(url, max_comments, initial_scroll_rounds)

if __name__ == "__main__":
    main()
