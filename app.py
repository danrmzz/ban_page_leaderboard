from flask import Flask, render_template
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from collections import Counter
import requests
import aiocache

app = Flask(__name__)

# Initialize the counter for usernames
username_counts = Counter()

# Cache for UUIDs
uuid_cache = aiocache.SimpleMemoryCache()

# Semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(10)

# Function to process a single page
async def process_page(page_number, browser):
    url = f"https://saicopvp.com/bans/bans.php?page={page_number}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://saicopvp.com"
    }

    async with semaphore:
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

# Function to fetch UUID for a given username
async def fetch_uuid(username):
    cached_uuid = await uuid_cache.get(username)
    if cached_uuid:
        return cached_uuid

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            uuid = data.get("id")
            await uuid_cache.set(username, uuid, ttl=3600)  # Cache for 1 hour
            return uuid
        else:
            print(f"Failed to fetch UUID for {username}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching UUID for {username}: {e}")
        return None

# Function to format UUID with dashes
def format_uuid(uuid):
    return f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"

@app.route('/')
async def index():
    # Reset the global username_counts
    global username_counts
    username_counts = Counter()
    
    # Run the scraper and wait for it to complete
    await run_scraper()

    # Get the top 10 players
    top_players = username_counts.most_common()

    # Sort top players lexicographically if they have the same count
    sorted_top_players = sorted(top_players, key=lambda x: (-x[1], x[0].lower()))

    # Get the top 10 sorted players
    top_10_sorted = sorted_top_players[:10]

    # Fetch UUIDs for the top 10 players and add to the dictionary
    top_10_with_uuids = []
    for username, count in top_10_sorted:
        uuid = await fetch_uuid(username)
        if uuid:
            uuid = format_uuid(uuid)
        top_10_with_uuids.append({"username": username, "count": count, "uuid": uuid})

    # Pass the list to the template
    return render_template('index.html', top_10_sorted=top_10_with_uuids)

if __name__ == '__main__':
    app.run(debug=True)