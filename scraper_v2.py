import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import csv
from urllib.parse import urljoin
import re
from typing import List, Dict, Optional, Set
import time
from pathlib import Path


class UstasiScraperV2:
    """Improved scraper with crash protection and duplicate detection"""

    def __init__(self, max_pages: int = 100):
        self.base_url = "https://ustasi.az"
        self.homelist_url = f"{self.base_url}/homelist/"
        self.ajax_url = f"{self.base_url}/ajax.php"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.max_pages = max_pages  # Hard limit on pages
        self.listings = []
        self.session = None
        self.seen_urls: Set[str] = set()  # Track seen URLs
        self.progress_file = Path('scraper_progress.json')
        self.scraped_ids: Set[str] = set()  # Track scraped listing IDs

    async def create_session(self):
        """Create aiohttp session with cookies"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout
        )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    def save_progress(self, urls: List[str], stage: str):
        """Save progress to file"""
        try:
            data = {
                'stage': stage,
                'urls': list(urls),
                'scraped_ids': list(self.scraped_ids),
                'timestamp': time.time()
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")

    def load_progress(self) -> Optional[Dict]:
        """Load progress from file"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scraped_ids = set(data.get('scraped_ids', []))
                    return data
        except Exception as e:
            print(f"Warning: Could not load progress: {e}")
        return None

    async def fetch_listings_page(self, start: int) -> Optional[str]:
        """Fetch a single listings page using POST request"""
        try:
            async with self.session.post(
                self.homelist_url,
                params={'start': start},
                data=f'start={start}'
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"  Warning: HTTP {response.status} for page start={start}")
                    return None
        except asyncio.TimeoutError:
            print(f"  Timeout fetching page start={start}")
            return None
        except Exception as e:
            print(f"  Error fetching page start={start}: {e}")
            return None

    def parse_listing_urls(self, html: str) -> List[str]:
        """Parse listing URLs from the listings page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        # Find all product divs
        products = soup.find_all('div', class_='nobj prod')

        for product in products:
            link = product.find('a', href=True)
            if link and link['href']:
                full_url = urljoin(self.base_url, link['href'])
                urls.append(full_url)

        return urls

    async def fetch_all_listing_urls(self) -> List[str]:
        """Fetch all listing URLs from pages with duplicate detection"""
        print(f"Fetching listing pages (max {self.max_pages} pages)...")

        all_urls = []
        start = 0
        consecutive_no_new = 0
        max_consecutive_no_new = 10  # Stop if 10 pages with no new URLs (increased from 5)

        while start < self.max_pages and consecutive_no_new < max_consecutive_no_new:
            print(f"Page {start+1}/{self.max_pages}...", end=' ')

            try:
                html = await asyncio.wait_for(
                    self.fetch_listings_page(start),
                    timeout=30
                )

                if html:
                    urls = self.parse_listing_urls(html)

                    # Count new URLs
                    new_urls = [url for url in urls if url not in self.seen_urls]

                    if new_urls:
                        all_urls.extend(new_urls)
                        self.seen_urls.update(new_urls)
                        consecutive_no_new = 0
                        print(f"Found {len(new_urls)} new listings (total: {len(all_urls)})")
                    else:
                        consecutive_no_new += 1
                        print(f"No new listings (consecutive: {consecutive_no_new}/{max_consecutive_no_new})")

                else:
                    consecutive_no_new += 1
                    print(f"Failed to fetch (consecutive: {consecutive_no_new}/{max_consecutive_no_new})")

                start += 1
                await asyncio.sleep(0.2)  # Faster delay

            except Exception as e:
                print(f"Error: {e}")
                consecutive_no_new += 1
                start += 1

        if consecutive_no_new >= max_consecutive_no_new:
            print(f"\nStopped: {max_consecutive_no_new} consecutive pages with no new listings")
        elif start >= self.max_pages:
            print(f"\nStopped: Reached max pages limit ({self.max_pages})")

        print(f"Total unique listings found: {len(all_urls)}")
        return all_urls

    def extract_listing_id(self, url: str) -> Optional[str]:
        """Extract listing ID from URL"""
        match = re.search(r'-(\d+)\.html$', url)
        return match.group(1) if match else None

    def extract_hash_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hash value from telzona div"""
        # Look for the telshow div with data-h attribute
        telshow_div = soup.find('div', id='telshow')
        if telshow_div and telshow_div.has_attr('data-h'):
            return telshow_div['data-h']

        # Fallback: look in the page source for the hash pattern
        page_text = str(soup)
        hash_match = re.search(r'data-h="([a-f0-9]{32})"', page_text)
        if hash_match:
            return hash_match.group(1)

        return None

    async def fetch_phone_number(self, listing_id: str, hash_value: str) -> Optional[str]:
        """Fetch phone number via AJAX call"""
        try:
            data = {
                'act': 'telshow',
                'id': listing_id,
                't': 'product',
                'h': hash_value,
                'rf': ''
            }

            async with self.session.post(
                self.ajax_url,
                data=data,
                headers={
                    **self.headers,
                    'Accept': 'application/json, text/javascript, */*; q=0.01'
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('ok') == 1:
                        return result.get('tel', '')
        except Exception:
            pass  # Silent fail for phone numbers

        return None

    async def scrape_detail_page(self, url: str) -> Optional[Dict]:
        """Scrape data from a detail page"""
        listing_id = self.extract_listing_id(url)

        # Skip if already scraped
        if listing_id in self.scraped_ids:
            return None

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Find the main content div
                content_div = soup.find('div', id='openhalf')
                if not content_div:
                    return None

                data = {
                    'url': url,
                    'listing_id': listing_id
                }

                # Extract title
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    data['title'] = title_elem.get_text(strip=True)
                else:
                    data['title'] = url.split('/')[-1].replace('.html', '').replace('-', ' ')

                # Extract categories
                categories = []
                category_links = content_div.find_all('a', href=re.compile(r'^/[^/]+$'))
                for link in category_links[:2]:
                    categories.append(link.get_text(strip=True))
                data['categories'] = ', '.join(categories) if categories else ''

                # Extract price
                price_elem = content_div.find('span', class_='pricecolor')
                data['price'] = price_elem.get_text(strip=True) if price_elem else ''

                # Extract description
                desc_elem = content_div.find('p', class_='infop100')
                data['description'] = desc_elem.get_text(strip=True) if desc_elem else ''

                # Extract contact info
                contact_div = content_div.find('div', class_='infocontact')
                if contact_div:
                    user_link = contact_div.find('a', href=re.compile(r'/user/'))
                    if user_link:
                        data['user_name'] = user_link.get_text(strip=True).replace('(Bütün Elanları)', '').strip()
                        data['user_id'] = user_link['href'].split('/')[-1]
                    else:
                        data['user_name'] = data['user_id'] = ''

                    lines = list(contact_div.stripped_strings)
                    location = ''
                    for line in lines:
                        if 'şəhəri' in line or 'rayonu' in line:
                            location = line
                            break
                    data['location'] = location
                else:
                    data['user_name'] = data['user_id'] = data['location'] = ''

                # Extract date
                date_elem = content_div.find('span', class_='viewsbb')
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    date_match = re.search(r'Tarix:\s*(.+)', date_text)
                    data['date'] = date_match.group(1) if date_match else date_text
                else:
                    data['date'] = ''

                # Fetch phone number via AJAX
                if listing_id:
                    hash_value = self.extract_hash_from_html(soup)
                    if hash_value:
                        phone = await self.fetch_phone_number(listing_id, hash_value)
                        data['phone'] = phone if phone else ''
                    else:
                        data['phone'] = ''
                else:
                    data['phone'] = ''

                # Mark as scraped
                if listing_id:
                    self.scraped_ids.add(listing_id)

                return data

        except Exception as e:
            print(f"    Error scraping {url}: {e}")
            return None

    async def scrape_all_listings(self, urls: List[str], max_concurrent: int = 10):
        """Scrape all listing detail pages with concurrency control"""
        total = len(urls)
        print(f"\nScraping {total} listings (max {max_concurrent} concurrent)...")

        semaphore = asyncio.Semaphore(max_concurrent)
        successful = 0
        failed = 0

        async def scrape_with_semaphore(url, index):
            nonlocal successful, failed
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self.scrape_detail_page(url),
                        timeout=30
                    )
                    await asyncio.sleep(0.1)  # Small delay

                    if result:
                        successful += 1
                        return result
                    else:
                        failed += 1
                        return None
                except asyncio.TimeoutError:
                    failed += 1
                    print(f"    Timeout: {url}")
                    return None
                except Exception as e:
                    failed += 1
                    print(f"    Error: {e}")
                    return None

        # Create tasks
        tasks = [scrape_with_semaphore(url, i) for i, url in enumerate(urls)]

        # Process with progress
        completed = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                self.listings.append(result)

            completed += 1
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed}/{total} | Success: {successful} | Failed: {failed}")
                # Save intermediate progress
                self.save_intermediate_results()

        print(f"\nCompleted! Success: {successful} | Failed: {failed}")

    def save_intermediate_results(self):
        """Save intermediate results during scraping"""
        if self.listings:
            try:
                with open('ustasi_listings_temp.json', 'w', encoding='utf-8') as f:
                    json.dump(self.listings, f, ensure_ascii=False, indent=2)
            except Exception:
                pass  # Silent fail

    def save_to_json(self, filename: str = 'ustasi_listings.json'):
        """Save listings to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.listings, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.listings)} listings to {filename}")

    def save_to_csv(self, filename: str = 'ustasi_listings.csv'):
        """Save listings to CSV file"""
        if not self.listings:
            print("No listings to save")
            return

        fieldnames = ['listing_id', 'title', 'categories', 'price', 'phone',
                     'user_name', 'user_id', 'location', 'date', 'description', 'url']

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for listing in self.listings:
                row = {field: listing.get(field, '') for field in fieldnames}
                writer.writerow(row)

        print(f"Saved {len(self.listings)} listings to {filename}")

    async def run(self):
        """Main scraping workflow"""
        start_time = time.time()

        try:
            await self.create_session()

            # Check for existing progress
            progress = self.load_progress()

            if progress and progress.get('stage') == 'urls_collected':
                print("Found saved progress! Resuming...")
                urls = progress['urls']
            else:
                # Step 1: Fetch all listing URLs
                urls = await self.fetch_all_listing_urls()

                if not urls:
                    print("No listings found!")
                    return

                # Save progress
                self.save_progress(urls, 'urls_collected')

            # Step 2: Scrape all detail pages
            await self.scrape_all_listings(urls, max_concurrent=10)

            # Step 3: Save final results
            self.save_to_json()
            self.save_to_csv()

            # Clean up temp files
            try:
                Path('ustasi_listings_temp.json').unlink(missing_ok=True)
                self.progress_file.unlink(missing_ok=True)
            except:
                pass

        except KeyboardInterrupt:
            print("\n\nInterrupted by user!")
            print(f"Scraped {len(self.listings)} listings so far")
            if self.listings:
                self.save_to_json('ustasi_listings_partial.json')
                self.save_to_csv('ustasi_listings_partial.csv')
                print("Saved partial results")
        except Exception as e:
            print(f"\nError: {e}")
            if self.listings:
                self.save_to_json('ustasi_listings_partial.json')
                self.save_to_csv('ustasi_listings_partial.csv')
                print("Saved partial results")
        finally:
            await self.close_session()

        elapsed = time.time() - start_time
        print(f"\nTotal time: {elapsed:.2f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Total listings scraped: {len(self.listings)}")


async def main():
    # You can adjust max_pages here
    # Recommended: 100-200 pages for full dataset
    # The scraper will stop automatically if no new listings are found
    scraper = UstasiScraperV2(max_pages=100)  # Limit to 100 pages (adjust as needed)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
