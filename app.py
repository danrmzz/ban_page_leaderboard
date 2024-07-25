from flask import Flask, render_template
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from collections import Counter

app = Flask(__name__)

# Initialize the counter for usernames
username_counts = Counter()

# Function to process a single page
async def process_page(page_number, browser):
    url = f"https://saicopvp.com/bans/bans.php?page={page_number}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://saicopvp.com"
    }

    context = await browser.new_context(extra_http_headers=headers)
    page = await context.new_page()
    await page.goto(url)
    content = await page.content()
    await context.close()

    # Parse the relevant part of the HTML with BeautifulSoup using lxml parser
    soup = BeautifulSoup(content, "lxml")
    table_body = soup.select_one("table.table tbody")

    # Extract usernames from the rows and count occurrences
    local_counts = Counter()
    if table_body:
        for row in table_body.select("tr"):
            username_cell = row.find_all("td")[0]
            username = username_cell.find("p").text.strip()
            local_counts[username] += 1
    
    return local_counts

# Function to merge results from multiple pages
def merge_counts(counts_list):
    global username_counts
    for counts in counts_list:
        username_counts.update(counts)

# Asynchronous function to run the web scraping process
async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        tasks = [process_page(page_number, browser) for page_number in range(1, 110)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out results that raised exceptions
        successful_results = [result for result in results if isinstance(result, Counter)]
        
        # Merge all counts
        merge_counts(successful_results)
        
        await browser.close()

@app.route('/')
def index():
    # Reset the global username_counts
    global username_counts
    username_counts = Counter()
    
    # Run the scraper and wait for it to complete
    asyncio.run(run_scraper())

    # Get the top 10 players
    top_players = username_counts.most_common()

    # Sort top players lexicographically if they have the same count
    sorted_top_players = sorted(top_players, key=lambda x: (-x[1], x[0].lower()))

    # Get the top 10 sorted players
    top_10_sorted = sorted_top_players[:10]

    return render_template('index.html', top_10_sorted=top_10_sorted)

if __name__ == '__main__':
    app.run(debug=True)
