'''
Scraping Amazon without permission violates their Terms of Service
Through their official APIs:
Amazon Product Advertising API (PA-API): 
- search for items
- find similar items
- retrieve product data, including pricing and customer review data 
(often limited to summary data or top reviews rather than the entire historical catalog).

Selling Partner API (SP-API): 
If you are an Amazon Seller needing to access data regarding your own products, 
for managing listings, orders, and reports.
'''
import time  # For adding delays between requests
from selenium import webdriver  # Browser automation library
from selenium.webdriver.chrome.options import Options  # Chrome options
from selenium.webdriver.chrome.service import Service  # Chrome service
from webdriver_manager.chrome import ChromeDriverManager  # Auto-manage ChromeDriver
from bs4 import BeautifulSoup  # HTML parser for extracting content
from tabulate import tabulate  # Library for formatting output as a table


def get_reviews(driver, url):  # Function to extract reviews from a single page using Selenium
    driver.get(url)  # Load the page in the browser
    time.sleep(3)  # Wait for page to load fully
    soup = BeautifulSoup(driver.page_source, "html.parser")  # Parse the loaded HTML

    reviews = []  # List to store extracted reviews
    review_containers = soup.find_all("div", class_="a-section review")  # Find review containers

    for review in review_containers:  # Loop through each review
        reviewer = review.find("span", class_="a-profile-name")  # Extract reviewer name
        reviewer = reviewer.get_text(strip=True) if reviewer else "Anonymous"

        title = review.find("a", {"data-hook": "review-title"})  # Extract review title
        title = title.get_text(strip=True) if title else ""

        body = review.find("span", {"data-hook": "review-body"})  # Extract review body
        body = body.get_text(strip=True) if body else ""

        date = review.find("span", {"data-hook": "review-date"})  # Extract review date
        date = date.get_text(strip=True) if date else ""

        helpful = review.find("span", {"data-hook": "helpful-vote-statement"})  # Extract helpful votes
        helpful = helpful.get_text(strip=True) if helpful else "0"

        reviews.append({  # Add review data to list
            "Reviewer": reviewer,
            "Title": title,
            "Body": body,
            "Date": date,
            "Helpful": helpful
        })

    return reviews, soup  # Return reviews and soup for pagination


def scrape_all_reviews(start_url):  # Function to scrape all pages
    options = Options()  # Set up Chrome options
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    service = Service(ChromeDriverManager().install())  # Set up ChromeDriver service
    driver = webdriver.Chrome(service=service, options=options)  # Initialize Chrome driver

    all_reviews = []  # List for all reviews
    current_url = start_url  # Start with the given URL

    try:
        while current_url:  # Loop until no more pages
            print(f"Scraping: {current_url}")  # Print current page being scraped
            reviews, soup = get_reviews(driver, current_url)  # Get reviews from current page
            all_reviews.extend(reviews)  # Add to all reviews

            next_link = soup.find("li", class_="a-last")  # Find next page link
            if next_link and next_link.find("a"):  # If next page exists
                next_url = "https://www.amazon.com" + next_link.find("a")["href"]  # Build next URL
                current_url = next_url  # Update current URL
            else:
                current_url = None  # No more pages

            time.sleep(2)  # Delay to avoid being blocked
    finally:
        driver.quit()  # Close the browser

    return all_reviews  # Return all collected reviews


if __name__ == "__main__":  # Main execution block
    url = "https://www.amazon.com/product-reviews/B07TM215P9/ref=acr_dp_hist_3?ie=UTF8&filterByStar=three_star&reviewerType=all_reviews"  # Starting URL
    reviews = scrape_all_reviews(url)  # Scrape all reviews

    if reviews:  # If reviews were found
        print(tabulate(reviews, headers="keys", tablefmt="grid"))  # Print as table
    else:
        print("No reviews found.")  # Message if no reviews
