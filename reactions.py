#!/usr/bin/env python3
"""
LinkedIn Reactions Deleter
Automatically removes likes/reactions from your LinkedIn posts and comments.
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

class LinkedInReactionsDeleter:
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
                "//*[contains(text(), 'There was an issue')]",
                "//*[contains(text(), 'Something went wrong')]",
                "//*[contains(text(), 'Try again')]",
                ".feed-shared-error-message",
                "[data-test-id*='error']",
                ".error-message",
                ".error-page",
                ".error-container"
            ]
            for selector in error_selectors:
                try:
                    if selector.startswith("//"):
                        error_element = self.driver.find_element(By.XPATH, selector)
                    else:
                        error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if error_element.is_displayed():
                        logger.warning("LinkedIn error page detected, refreshing...")
                        time.sleep(2)
                        self.driver.refresh()
                        time.sleep(5)
                        self.wait_for_page_load()
                        logger.info("Page refreshed after LinkedIn error")
                        return True
                except NoSuchElementException:
                    continue
            return False
        except Exception as e:
            logger.warning(f"Error checking for network error: {e}")
            return False

    def check_for_empty_page(self) -> bool:
        """Check if the page has no content (likely due to LinkedIn error)."""
        try:
            # Check if we're on a page with no posts/comments
            content_selectors = [
                ".feed-shared-update-v2",
                ".feed-shared-update", 
                ".comments-comments-list__comment-item",
                ".comments-comment-item",
                "[data-test-id*='post']",
                "[data-test-id*='comment']"
            ]
            
            has_content = False
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        has_content = True
                        break
                except NoSuchElementException:
                    continue
            
            if not has_content:
                logger.warning("No content found on page, likely LinkedIn error - refreshing...")
                time.sleep(2)
                self.driver.refresh()
                time.sleep(5)
                self.wait_for_page_load()
                logger.info("Page refreshed due to empty content")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Error checking for empty page: {e}")
            return False

    def unlike_post(self, like_button) -> bool:
        """Unlike a post by clicking the like button.
        Returns: True if unliked successfully, False if failed.
        """
        try:
            # Verify it's actually liked (aria-pressed="true")
            aria_pressed = like_button.get_attribute("aria-pressed")
            if aria_pressed != "true":
                logger.info("Post is not liked, skipping")
                return False
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
            time.sleep(0.3)
            
            try:
                like_button.click()
                logger.info("Successfully unliked post")
                return True
            except Exception as e:
                logger.warning(f"Regular click failed: {e}, trying JavaScript click")
                try:
                    self.driver.execute_script("arguments[0].click();", like_button)
                    logger.info("Successfully unliked post with JavaScript")
                    return True
                except Exception as e2:
                    logger.error(f"JavaScript click also failed: {e2}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to unlike post: {e}")
            return False

    def unlike_comment(self, like_button) -> bool:
        """Unlike a comment by clicking the like button.
        Returns: True if unliked successfully, False if failed.
        """
        try:
            # Verify it's actually liked (aria-pressed="true")
            aria_pressed = like_button.get_attribute("aria-pressed")
            if aria_pressed != "true":
                logger.info("Comment is not liked, skipping")
                return False
            
            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
            time.sleep(0.3)
            
            try:
                like_button.click()
                logger.info("Successfully unliked comment")
                return True
            except Exception as e:
                logger.warning(f"Regular click failed: {e}, trying JavaScript click")
                try:
                    self.driver.execute_script("arguments[0].click();", like_button)
                    logger.info("Successfully unliked comment with JavaScript")
                    return True
                except Exception as e2:
                    logger.error(f"JavaScript click also failed: {e2}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to unlike comment: {e}")
            return False

    def load_more_comments(self) -> int:
        """Load more comments by clicking 'Show previous comments' buttons.
        Returns: Number of buttons clicked.
        """
        try:
            load_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".button.comments-comments-list__show-previous-button")
            clicked_count = 0
            
            for button in load_buttons:
                try:
                    if button.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.2)
                        button.click()
                        clicked_count += 1
                        logger.info("Clicked 'Show previous comments' button")
                except Exception as e:
                    logger.warning(f"Failed to click load more comments button: {e}")
                    continue
            
            return clicked_count
        except Exception as e:
            logger.warning(f"Error loading more comments: {e}")
            return 0

    def load_previous_replies(self) -> int:
        """Load previous replies by clicking 'Show previous replies' buttons.
        Returns: Number of buttons clicked.
        """
        try:
            load_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.show-prev-replies")
            clicked_count = 0
            
            for button in load_buttons:
                try:
                    if button.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.2)
                        button.click()
                        clicked_count += 1
                        logger.info("Clicked 'Show previous replies' button")
                except Exception as e:
                    logger.warning(f"Failed to click load previous replies button: {e}")
                    continue
            
            return clicked_count
        except Exception as e:
            logger.warning(f"Error loading previous replies: {e}")
            return 0

    def expand_comment_sections(self) -> int:
        """Click on comment count links to expand comment sections.
        Returns: Number of comment sections expanded.
        """
        try:
            # Look for comment count links/buttons
            comment_link_selectors = [
                "button[data-control-name='comment_count']",
                ".social-counts-comments__count",
                ".social-counts__item--comments button",
                ".feed-shared-social-action-bar__action-button[data-control-name='comment_count']",
                "//button[contains(., 'comment') and contains(., 'Show')]",
                "//button[contains(., 'comment') and contains(text(), 'Show')]",
                "//a[contains(., 'comment') and contains(text(), 'Show')]"
            ]
            
            expanded_count = 0
            
            for selector in comment_link_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed():
                                # Check if it's a comment count link (contains numbers or "Show")
                                text = element.text.lower()
                                if any(keyword in text for keyword in ['comment', 'show', 'reply']) and any(char.isdigit() for char in text):
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(0.3)
                                    element.click()
                                    expanded_count += 1
                                    logger.info(f"Expanded comment section: {element.text}")
                                    time.sleep(1)  # Wait for comments to load
                        except Exception as e:
                            logger.warning(f"Failed to click comment link: {e}")
                            continue
                            
                except NoSuchElementException:
                    continue
            
            return expanded_count
        except Exception as e:
            logger.warning(f"Error expanding comment sections: {e}")
            return 0

    def initial_scroll_loading(self, scroll_rounds: int = 5, scroll_delay: int = 2) -> None:
        """Perform initial aggressive scrolling to load more content."""
        logger.info(f"Performing initial scrolling to load more content ({scroll_rounds} rounds)...")
        
        for i in range(scroll_rounds):
            logger.info(f"Initial scroll round {i+1}/{scroll_rounds}")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            
            # Load more comments and replies
            comments_loaded = self.load_more_comments()
            replies_loaded = self.load_previous_replies()
            
            # Expand comment sections to reveal liked comments
            comment_sections_expanded = self.expand_comment_sections()
            
            if comments_loaded > 0 or replies_loaded > 0 or comment_sections_expanded > 0:
                logger.info(f"Loaded {comments_loaded} comment sections, {replies_loaded} reply sections, and expanded {comment_sections_expanded} comment sections")
                time.sleep(1)  # Wait for content to load
            
            # Check for network errors
            if self.check_for_network_error():
                logger.info("Network error handled during initial scrolling...")
            
            # Check if we've loaded more content
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"Page height after scroll {i+1}: {current_height}")
        
        logger.info("Initial scrolling complete, starting reactions processing...")

    def process_reactions(self, max_reactions: int | None = None, initial_scroll_rounds: int = 5) -> None:
        """Process all reactions, scrolling to load more if needed."""
        logger.info("Starting to process reactions...")
        
        # Wait for content to load
        self.wait_for_page_load()
        time.sleep(3)
        
        # Perform initial aggressive scrolling to load more content
        self.initial_scroll_loading(scroll_rounds=initial_scroll_rounds)
        
        unliked_posts = 0
        unliked_comments = 0
        processed_count = 0
        consecutive_failures = 0
        refresh_interval = 50  # Refresh page every 50 successful unlikes
        
        while True:
            # Find liked posts
            post_like_selectors = [
                ".react-button__trigger.artdeco-button[aria-pressed='true']",
                "button[data-control-name='like_toggle'][aria-pressed='true']",
                ".feed-shared-social-action-bar__action-button[aria-pressed='true']"
            ]
            
            liked_posts = []
            for selector in post_like_selectors:
                try:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if posts:
                        liked_posts = posts
                        logger.info(f"Found {len(liked_posts)} liked posts using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            # Find liked comments
            comment_like_selectors = [
                ".comments-comment-social-bar__like-action-button[aria-pressed='true']",
                ".comment-social-bar__like-button[aria-pressed='true']",
                "button[data-control-name='comment_like_toggle'][aria-pressed='true']"
            ]
            
            liked_comments = []
            for selector in comment_like_selectors:
                try:
                    comments = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if comments:
                        liked_comments = comments
                        logger.info(f"Found {len(liked_comments)} liked comments using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            total_reactions = len(liked_posts) + len(liked_comments)
            
            if total_reactions == 0:
                logger.info("No liked posts or comments found on current page")
                
                # Check for LinkedIn error pages or empty content
                if self.check_for_network_error() or self.check_for_empty_page():
                    logger.info("LinkedIn error detected, continuing after refresh...")
                    continue
                
                # Try scrolling to load more content
                logger.info("Scrolling to load more content...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Load more comments and replies
                comments_loaded = self.load_more_comments()
                replies_loaded = self.load_previous_replies()
                
                # Expand comment sections to reveal liked comments
                comment_sections_expanded = self.expand_comment_sections()
                
                if comments_loaded == 0 and replies_loaded == 0 and comment_sections_expanded == 0:
                    logger.info("No more content to load, reached end of page")
                    break
                else:
                    logger.info(f"Loaded {comments_loaded} comment sections, {replies_loaded} reply sections, and expanded {comment_sections_expanded} comment sections, continuing...")
                    continue
            
            # Process liked posts
            for i, like_button in enumerate(liked_posts):
                if max_reactions and processed_count >= max_reactions:
                    logger.info(f"Reached maximum reactions limit ({max_reactions}), stopping processing")
                    return
                
                processed_count += 1
                
                try:
                    logger.info(f"Processing liked post {processed_count} (post {i+1}/{len(liked_posts)})")
                    
                    # Check for network errors
                    if self.check_for_network_error():
                        logger.info("Network error handled, continuing with reactions processing...")
                    
                    # Unlike the post
                    if self.unlike_post(like_button):
                        unliked_posts += 1
                        consecutive_failures = 0
                        
                        # Check if we need to refresh the page
                        if (unliked_posts + unliked_comments) % refresh_interval == 0:
                            logger.info(f"Refreshing page after {unliked_posts + unliked_comments} successful unlikes...")
                            self.driver.refresh()
                            time.sleep(5)
                            self.wait_for_page_load()
                            self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)
                            logger.info("Page refreshed and scrolled, continuing with fresh content...")
                            break
                    else:
                        consecutive_failures += 1
                        logger.warning(f"Failed to unlike post {processed_count}")
                    
                    # Wait between unlikes to avoid being rate limited
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing liked post {processed_count}: {e}")
                    consecutive_failures += 1
                    continue
            
            # Process liked comments
            for i, like_button in enumerate(liked_comments):
                if max_reactions and processed_count >= max_reactions:
                    logger.info(f"Reached maximum reactions limit ({max_reactions}), stopping processing")
                    return
                
                processed_count += 1
                
                try:
                    logger.info(f"Processing liked comment {processed_count} (comment {i+1}/{len(liked_comments)})")
                    
                    # Check for network errors
                    if self.check_for_network_error():
                        logger.info("Network error handled, continuing with reactions processing...")
                    
                    # Unlike the comment
                    if self.unlike_comment(like_button):
                        unliked_comments += 1
                        consecutive_failures = 0
                        
                        # Check if we need to refresh the page
                        if (unliked_posts + unliked_comments) % refresh_interval == 0:
                            logger.info(f"Refreshing page after {unliked_posts + unliked_comments} successful unlikes...")
                            self.driver.refresh()
                            time.sleep(5)
                            self.wait_for_page_load()
                            self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)
                            logger.info("Page refreshed and scrolled, continuing with fresh content...")
                            break
                    else:
                        consecutive_failures += 1
                        logger.warning(f"Failed to unlike comment {processed_count}")
                    
                    # Wait between unlikes to avoid being rate limited
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing liked comment {processed_count}: {e}")
                    consecutive_failures += 1
                    continue
            
            # Check if we've reached the limit
            if max_reactions and processed_count >= max_reactions:
                logger.info(f"Reached maximum reactions limit ({max_reactions}), stopping processing")
                break
            
            # If we have too many consecutive failures, refresh the page
            if consecutive_failures >= 10:
                logger.info("Too many consecutive failures, refreshing page to clear stale elements...")
                self.driver.refresh()
                time.sleep(5)
                self.wait_for_page_load()
                self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)
                consecutive_failures = 0
                logger.info("Page refreshed and scrolled, continuing with fresh elements...")
                continue
        
        logger.info(f"Processing complete. Unliked posts: {unliked_posts}, Unliked comments: {unliked_comments}")

    def run(self, url: str, max_reactions: int | None = None, initial_scroll_rounds: int = 5) -> None:
        """Main method to run the reactions deletion process."""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            logger.info("Waiting for page to load...")
            self.wait_for_page_load()
            time.sleep(3)
            
            # Check current URL and log it
            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")
            
            # Check if we're on a login page
            if "login" in current_url.lower() or "auth" in current_url.lower():
                logger.info("Detected login page. Please log in manually.")
            elif "recent-activity" not in current_url.lower():
                logger.warning(f"URL doesn't contain 'recent-activity'. Current URL: {current_url}")
                logger.info("Please navigate to your Recent activity page")
            
            # Give user time to log in and navigate if needed
            input("Press Enter when you're on the correct page and ready to start removing reactions...")
            
            # Log final URL before processing
            final_url = self.driver.current_url
            logger.info(f"Final URL before processing: {final_url}")
            
            # Process reactions
            self.process_reactions(max_reactions, initial_scroll_rounds)
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main() -> None:
    print("LinkedIn Reactions Deleter")
    print("=========================")
    print("This script will help you remove likes/reactions from your LinkedIn posts and comments.")
    print()
    
    url = input("Enter LinkedIn URL (or press Enter for default activity page): ").strip()
    if not url:
        url = "https://www.linkedin.com/in/brianahanna/recent-activity/"
    
    max_reactions_input = input("Maximum number of reactions to process (or press Enter for all): ").strip()
    max_reactions = int(max_reactions_input) if max_reactions_input.isdigit() else None
    
    scroll_rounds_input = input("Initial scroll rounds to load more content (or press Enter for 5): ").strip()
    initial_scroll_rounds = int(scroll_rounds_input) if scroll_rounds_input.isdigit() else 5
    
    headless_input = input("Run in headless mode? (y/N): ").strip().lower()
    headless = headless_input in ['y', 'yes']
    
    print(f"\nStarting with URL: {url}")
    if max_reactions:
        print(f"Maximum reactions to process: {max_reactions}")
    print(f"Initial scroll rounds: {initial_scroll_rounds}")
    print(f"Headless mode: {headless}")
    print()
    
    deleter = LinkedInReactionsDeleter(headless=headless)
    deleter.run(url, max_reactions, initial_scroll_rounds)

if __name__ == "__main__":
    main()
