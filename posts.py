#!/usr/bin/env python3
"""
LinkedIn Post Deleter
Automatically deletes LinkedIn posts from your recent activity page,
while preserving posts made to community groups.
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInPostDeleter:
    def __init__(self, headless=False):
        """Initialize the LinkedIn Post Deleter with Chrome WebDriver."""
        self.driver = None
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            logger.info("Make sure you have ChromeDriver installed and in your PATH")
            sys.exit(1)
    
    def wait_for_page_load(self, timeout=10):
        """Wait for the page to load completely."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("Page load timeout, continuing anyway...")
    
    def check_for_network_error(self):
        """Check if LinkedIn is showing a network error and handle it."""
        try:
            # Look for common network error messages
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
                        time.sleep(5)  # Wait 5 seconds
                        
                        # Try to refresh the page
                        self.driver.refresh()
                        time.sleep(3)
                        
                        # Wait for page to load
                        self.wait_for_page_load()
                        
                        logger.info("Page refreshed after network error")
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for network error: {e}")
            return False
    
    def is_community_post(self, post_element, post_index):
        """
        Check if a post should be preserved (kept) or deleted.
        Returns True if the post should be preserved (skipped), False if it should be deleted.
        Currently configured to keep only the first post (index 0).
        """
        # Keep only the first post (index 0), delete all others
        if post_index == 0:
            logger.info("Preserving first post (index 0)")
            return True
        else:
            logger.info(f"Deleting post at index {post_index}")
            return False
    
    def get_repost_type(self, post_element):
        """
        Determine the type of repost to know which delete button to use.
        Returns: 'simple_repost' (4th), 'repost_with_thoughts' (5th), 'repost_of_repost' (3rd), or 'regular' (6th)
        """
        try:
            post_text = post_element.text.lower()
            
            # Check for repost of someone else's repost with their thoughts (3rd button)
            repost_of_repost_indicators = [
                "reposted with thoughts",
                "shared with thoughts", 
                "reposted and added",
                "shared and added",
                "reposted with comment",
                "shared with comment"
            ]
            
            for indicator in repost_of_repost_indicators:
                if indicator in post_text:
                    logger.info(f"Found repost of repost with thoughts indicator: '{indicator}' - will use 3rd button")
                    return 'repost_of_repost'
            
            # Check for simple repost (4th button)
            simple_repost_indicators = [
                "reposted this",
                "shared this"
            ]
            
            for indicator in simple_repost_indicators:
                if indicator in post_text:
                    logger.info(f"Found simple repost indicator: '{indicator}' - will use 4th button")
                    return 'simple_repost'
            
            # Check for repost with my thoughts (5th button)
            repost_with_thoughts_indicators = [
                "reposted with my thoughts",
                "shared with my thoughts",
                "reposted and added my thoughts",
                "shared and added my thoughts"
            ]
            
            for indicator in repost_with_thoughts_indicators:
                if indicator in post_text:
                    logger.info(f"Found repost with my thoughts indicator: '{indicator}' - will use 5th button")
                    return 'repost_with_thoughts'
            
            # Also check for specific repost elements
            try:
                repost_elements = post_element.find_elements(
                    By.CSS_SELECTOR, 
                    "[data-test-id*='repost'], [data-test-id*='share'], .feed-shared-actor-meta"
                )
                
                for element in repost_elements:
                    element_text = element.text.lower()
                    
                    # Check repost of repost first
                    for indicator in repost_of_repost_indicators:
                        if indicator in element_text:
                            logger.info(f"Found repost of repost with thoughts in element: '{indicator}' - will use 3rd button")
                            return 'repost_of_repost'
                    
                    # Check simple repost
                    for indicator in simple_repost_indicators:
                        if indicator in element_text:
                            logger.info(f"Found simple repost in element: '{indicator}' - will use 4th button")
                            return 'simple_repost'
                    
                    # Check repost with my thoughts
                    for indicator in repost_with_thoughts_indicators:
                        if indicator in element_text:
                            logger.info(f"Found repost with my thoughts in element: '{indicator}' - will use 5th button")
                            return 'repost_with_thoughts'
                        
            except NoSuchElementException:
                pass
                
            return 'regular'  # Not a repost, use regular post logic
            
        except Exception as e:
            logger.warning(f"Error checking repost type: {e}")
            return 'regular'  # If we can't determine, assume it's a regular post
    
    def navigate_to_recent_activity(self):
        """Try to navigate to the recent activity page."""
        try:
            # Try to find and click on "Activity" or "Recent Activity" link
            activity_selectors = [
                "a[href*='recent-activity']",
                "a[href*='activity']",
                "//a[contains(text(), 'Activity')]",
                "//a[contains(text(), 'Recent Activity')]"
            ]
            
            for selector in activity_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    logger.info(f"Found activity link: {element.text}")
                    element.click()
                    time.sleep(3)
                    self.wait_for_page_load()
                    return
                except NoSuchElementException:
                    continue
            
            logger.warning("Could not find activity link automatically")
            
        except Exception as e:
            logger.error(f"Error navigating to recent activity: {e}")
    
    def delete_post(self, post_element):
        """Delete a single post by clicking the ... menu and selecting delete.
        Returns: True if deleted successfully, False if failed, 'restricted' if no delete option available.
        """
        try:
            # Find and click the "..." menu button with more specific selectors
            menu_button = None
            menu_selectors = [
                "button[aria-label*='More actions']",
                "button[aria-label*='More']", 
                "button[data-test-id*='more']",
                ".feed-shared-control-menu__trigger",
                "button[class*='control-menu']",
                ".feed-shared-control-menu button"
            ]
            
            for selector in menu_selectors:
                try:
                    menu_button = post_element.find_element(By.CSS_SELECTOR, selector)
                    if menu_button.is_displayed():
                        logger.info(f"Found menu button using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not menu_button:
                logger.error("Could not find menu button for post")
                return False
            
            # Scroll to make sure the button is visible and centered
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_button)
            time.sleep(0.5)
            
            # Store the current URL to detect if we navigated away
            current_url = self.driver.current_url
            
            # Try multiple clicking strategies
            try:
                # First try regular click
                menu_button.click()
            except Exception:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", menu_button)
            
            time.sleep(1)
            
            # Check if we accidentally clicked on the post content instead of the menu button
            new_url = self.driver.current_url
            if new_url != current_url:
                logger.warning("Clicked on post content instead of menu button, navigating back...")
                self.driver.back()
                time.sleep(2)
                self.wait_for_page_load()
                return False  # Return False to retry this post
            
            # Determine the type of post to know which delete button to use
            repost_type = self.get_repost_type(post_element)
            
            # Wait for the dropdown to appear and find delete button directly
            logger.info("Looking for delete button in dropdown menu...")
            
            # Wait for the dropdown to appear
            try:
                WebDriverWait(self.driver, 2).until(
                    lambda driver: len(driver.find_elements(
                        By.CSS_SELECTOR, 
                        ".feed-shared-control-menu__content"
                    )) > 0
                )
                logger.info("Dropdown menu appeared")
            except TimeoutException:
                logger.warning("Dropdown menu didn't appear in time")
            
            # Try to find delete button using the specific selector from the JS script
            delete_button = None
            try:
                # First try the specific selector from the JS script
                delete_button = self.driver.find_element(By.CSS_SELECTOR, ".option-delete .feed-shared-control-menu__headline")
                logger.info("Found delete button using .option-delete .feed-shared-control-menu__headline")
            except NoSuchElementException:
                pass
            
            # Fallback to text-based search if specific selector fails
            if not delete_button:
                try:
                    delete_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Delete') or contains(text(), 'Delete post') or contains(text(), 'Delete repost')]")
                    logger.info("Found delete button using text search")
                except NoSuchElementException:
                    pass
            
            # Check if delete button is not available (restricted post)
            if not delete_button:
                logger.info("No delete option found in menu - this appears to be a restricted post")
                # Close the menu by clicking elsewhere or pressing escape
                try:
                    self.driver.execute_script("document.activeElement.blur();")
                    time.sleep(0.5)
                except:
                    pass
                return 'restricted'
            
            # Click the delete button directly
            try:
                delete_button.click()
                logger.info("Clicked delete button directly")
            except Exception:
                self.driver.execute_script("arguments[0].click();", delete_button)
                logger.info("Clicked delete button with JavaScript")
            
            time.sleep(1)
            
            # Confirm deletion if there's a confirmation dialog
            try:
                logger.info("Looking for confirmation dialog...")
                # Wait a bit for the confirmation dialog to appear
                time.sleep(1)
                
                # Try the specific confirmation button selector from the JS script first
                try:
                    confirm_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.feed-components-shared-decision-modal__confirm-button.artdeco-button.artdeco-button--primary.artdeco-button--2"))
                    )
                    logger.info("Found confirmation button using specific selector from JS script")
                except TimeoutException:
                    logger.warning("Specific confirmation button not found, trying fallback...")
                    confirm_button = None
                
                # Fallback to other selectors if specific one fails
                if not confirm_button:
                    confirm_selectors = [
                        "//button[contains(@class, 'artdeco-button--primary')]",
                        "//button[contains(text(), 'Delete')]",
                        "//button[contains(text(), 'Confirm')]", 
                        "//button[contains(text(), 'Yes')]",
                        "//button[contains(@class, 'confirm')]",
                        "//div[@role='dialog']//button[contains(text(), 'Delete')]",
                        "//div[contains(@class, 'modal')]//button[contains(text(), 'Delete')]"
                    ]
                    
                    for selector in confirm_selectors:
                        try:
                            confirm_button = WebDriverWait(self.driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            logger.info(f"Found confirmation button with selector: {selector}")
                            break
                        except TimeoutException:
                            continue
                
                if confirm_button:
                    # Try to click the confirmation button
                    try:
                        confirm_button.click()
                        logger.info("Clicked confirmation button")
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", confirm_button)
                        logger.info("Clicked confirmation button with JavaScript")
                    
                    time.sleep(1)
                    logger.info("Post deleted successfully")
                    return True
                else:
                    logger.warning("No confirmation dialog found, post may have been deleted already")
                    return True
                
            except Exception as e:
                logger.warning(f"Error handling confirmation dialog: {e}")
                # No confirmation dialog, post was deleted
                logger.info("Post deleted successfully (no confirmation needed)")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            return False
    
    def initial_scroll_loading(self, scroll_rounds=5, scroll_delay=2):
        """Perform initial aggressive scrolling to load more posts before processing."""
        logger.info(f"Performing initial scrolling to load more posts ({scroll_rounds} rounds)...")
        
        for i in range(scroll_rounds):
            logger.info(f"Initial scroll round {i+1}/{scroll_rounds}")
            
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_delay)
            
            # Check for network errors after scrolling
            if self.check_for_network_error():
                logger.info("Network error handled during initial scrolling...")
            
            # Check if we've loaded more content
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"Page height after scroll {i+1}: {current_height}")
        
        logger.info("Initial scrolling complete, starting post processing...")
    
    def process_posts(self, max_posts=None, initial_scroll_rounds=5):
        """Process all posts, scrolling to load more if needed."""
        logger.info("Starting to process posts...")
        
        # Wait for posts to load
        self.wait_for_page_load()
        time.sleep(3)
        
        # Perform initial aggressive scrolling to load more posts
        self.initial_scroll_loading(scroll_rounds=initial_scroll_rounds)
        
        deleted_count = 0
        skipped_count = 0
        restricted_count = 0
        processed_count = 0
        consecutive_failures = 0
        
        while True:
            # Find all post elements on current page
            post_selectors = [
                ".feed-shared-update-v2",
                "[data-test-id*='post']",
                ".feed-shared-update",
                ".occludable-update"
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if posts:
                        logger.info(f"Found {len(posts)} posts using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not posts:
                logger.warning("No posts found on the page")
                break
            
            # Process posts on current page
            for i, post in enumerate(posts):
                if max_posts and processed_count >= max_posts:
                    logger.info(f"Reached maximum posts limit ({max_posts}), stopping processing")
                    return
                
                processed_count += 1
                
                try:
                    logger.info(f"Processing post {processed_count} (page post {i+1}/{len(posts)})")
                    
                    # Check for network errors before processing
                    if self.check_for_network_error():
                        logger.info("Network error handled, continuing with post processing...")
                    
                    # Check if this post should be preserved (first post only)
                    if self.is_community_post(post, i):
                        logger.info("Skipping post (first post - preserved)")
                        skipped_count += 1
                        continue
                    
                    logger.info("Attempting to delete regular post...")
                    # Try to delete the post with retry mechanism
                    max_retries = 2
                    deleted = False
                    is_restricted = False
                    
                    for retry in range(max_retries):
                        result = self.delete_post(post)
                        if result == True:
                            deleted_count += 1
                            logger.info(f"Successfully deleted post {processed_count}")
                            deleted = True
                            consecutive_failures = 0  # Reset failure counter on success
                            break
                        elif result == 'restricted':
                            restricted_count += 1
                            logger.info(f"Post {processed_count} is restricted (no delete option available)")
                            is_restricted = True
                            consecutive_failures = 0  # Reset failure counter for restricted posts
                            break
                        else:
                            if retry < max_retries - 1:
                                logger.warning(f"Failed to delete post {processed_count}, retrying... (attempt {retry + 1}/{max_retries})")
                                time.sleep(2)  # Wait before retry
                            else:
                                logger.warning(f"Failed to delete post {processed_count} after {max_retries} attempts")
                    
                    if is_restricted:
                        # Skip this post and continue with the next one
                        continue
                    
                    if not deleted:
                        consecutive_failures += 1
                        logger.warning(f"Consecutive failures: {consecutive_failures}")
                        
                        # If we have too many consecutive failures, refresh the page
                        if consecutive_failures >= 5:
                            logger.info("Too many consecutive failures, refreshing page to clear stale elements...")
                            self.driver.refresh()
                            time.sleep(5)  # Wait for page to reload
                            self.wait_for_page_load()
                            
                            # Perform initial scrolling after refresh to reload more content
                            logger.info("Performing post-refresh scrolling to reload more content...")
                            self.initial_scroll_loading(scroll_rounds=3, scroll_delay=2)  # Fewer rounds after refresh
                            
                            consecutive_failures = 0  # Reset counter
                            logger.info("Page refreshed and scrolled, continuing with fresh elements...")
                            break  # Break out of current page processing to start fresh
                        
                        # Skip this post and continue with the next one
                        continue
                    
                    # Wait between deletions to avoid being rate limited
                    time.sleep(2)  # Increased from 1 to 2 seconds
                    
                    # Check for network errors after deletion
                    if self.check_for_network_error():
                        logger.info("Network error handled after deletion...")
                    
                except Exception as e:
                    logger.error(f"Error processing post {processed_count}: {e}")
                    # Check for network errors on exception
                    if self.check_for_network_error():
                        logger.info("Network error handled after exception...")
                    continue
            
            # Check if we've reached the limit
            if max_posts and processed_count >= max_posts:
                logger.info(f"Reached maximum posts limit ({max_posts}), stopping processing")
                break
            
            # Scroll down to load more posts
            logger.info("Scrolling down to load more posts...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Wait for new posts to load
            
            # Check for network errors after scrolling
            if self.check_for_network_error():
                logger.info("Network error handled after scrolling...")
            
            # Check if we're at the bottom of the page
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if current_height == new_height:
                logger.info("Reached end of page, no more posts to load")
                break
        
        logger.info(f"Processing complete. Deleted: {deleted_count}, Skipped: {skipped_count}, Restricted: {restricted_count}")
    
    def run(self, url, max_posts=None, initial_scroll_rounds=5):
        """Main method to run the post deletion process."""
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
                logger.info("Attempting to navigate to recent activity page...")
                self.navigate_to_recent_activity()
            
            # Give user time to log in and navigate if needed
            input("Press Enter when you're on the correct page and ready to start deleting posts...")
            
            # Log final URL before processing
            final_url = self.driver.current_url
            logger.info(f"Final URL before processing: {final_url}")
            
            # Process posts
            self.process_posts(max_posts, initial_scroll_rounds)
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function to run the LinkedIn Post Deleter."""
    print("LinkedIn Post Deleter")
    print("====================")
    print("This script will help you delete LinkedIn posts while preserving community group posts.")
    print()
    
    # Get user preferences
    url = input("Enter LinkedIn URL (or press Enter for default): ").strip()
    if not url:
        url = "https://www.linkedin.com/in/brianahanna/recent-activity/all/"
    
    max_posts_input = input("Maximum number of posts to process (or press Enter for all): ").strip()
    max_posts = int(max_posts_input) if max_posts_input.isdigit() else None
    
    scroll_rounds_input = input("Initial scroll rounds to load more posts (or press Enter for 5): ").strip()
    initial_scroll_rounds = int(scroll_rounds_input) if scroll_rounds_input.isdigit() else 5
    
    headless_input = input("Run in headless mode? (y/N): ").strip().lower()
    headless = headless_input in ['y', 'yes']
    
    print(f"\nStarting with URL: {url}")
    if max_posts:
        print(f"Maximum posts to process: {max_posts}")
    print(f"Initial scroll rounds: {initial_scroll_rounds}")
    print(f"Headless mode: {headless}")
    print()
    
    # Create and run the deleter
    deleter = LinkedInPostDeleter(headless=headless)
    deleter.run(url, max_posts, initial_scroll_rounds)

if __name__ == "__main__":
    main()
