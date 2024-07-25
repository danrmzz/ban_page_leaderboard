import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from collections import Counter
import json

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

# Main function to run the asyncio event loop
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Set the page range for this worker
        page_range = range(1001, 1501)  # Adjust this range for other workers

        # Increase the number of concurrent tasks to speed up processing
        concurrency = 50  # Number of concurrent tasks
        sem = asyncio.Semaphore(concurrency)

        async def bounded_process_page(page_number):
            async with sem:
                return await process_page(page_number, browser)

        # Create tasks for all pages
        tasks = [bounded_process_page(page_number) for page_number in page_range]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out results that raised exceptions
        successful_results = [result for result in results if isinstance(result, Counter)]
        
        # Merge all counts
        merge_counts(successful_results)
        
        await browser.close()

# Run the main function
asyncio.run(main())

# Get the top 10 players
top_players = username_counts.most_common(10)

# Sort top players lexicographically if they have the same count
sorted_top_players = sorted(top_players, key=lambda x: (-x[1], x[0].lower()))

# Save the top 10 players to a JSON file
with open('results3.json', 'w') as f:
    json.dump(sorted_top_players, f)
