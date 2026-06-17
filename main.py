import logging
import re
from typing import List, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import time
import os


@dataclass
class Place:
    name: str = ""
    address: str = ""
    website: str = ""
    phone_number: str = ""
    reviews_count: Optional[int] = None
    reviews_average: Optional[float] = None
    store_shopping: str = "No"
    in_store_pickup: str = "No"
    store_delivery: str = "No"
    place_type: str = ""
    opens_at: str = ""
    introduction: str = ""
    plus_code: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_url: str = ""


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )


def safe_text(page: Page, selectors: List[str]) -> str:
    """Try a list of CSS/XPath selectors and return the first non-empty inner_text."""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                txt = loc.inner_text(timeout=2000).strip()
                if txt:
                    return txt
        except Exception:
            continue
    return ""


def safe_attr(page: Page, selectors: List[str], attr: str) -> str:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                val = loc.get_attribute(attr, timeout=2000)
                if val:
                    return val.strip()
        except Exception:
            continue
    return ""


def dismiss_consent(page: Page):
    """Try to dismiss Google's consent/cookie banner if present, then wait for maps to be ready."""
    if "consent." not in page.url and "consent?" not in page.url:
        # Quick check for inline banner; if none, return fast
        try:
            page.wait_for_selector(
                'button:has-text("Accept all"), button:has-text("Reject all"), '
                'button:has-text("I agree"), form[action*="consent"]',
                timeout=2500,
            )
        except PlaywrightTimeoutError:
            return

    consent_selectors = [
        'button:has-text("Accept all")',
        'button:has-text("I agree")',
        'button:has-text("Reject all")',
        'form[action*="consent"] button[type="submit"]',
        'button[aria-label*="Accept"]',
        'button[aria-label*="Agree"]',
    ]
    for sel in consent_selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                try:
                    with page.expect_navigation(timeout=8000, wait_until="domcontentloaded"):
                        btn.click(timeout=3000)
                except PlaywrightTimeoutError:
                    pass
                except Exception:
                    pass
                page.wait_for_timeout(800)
                logging.info("Dismissed consent dialog")
                break
        except Exception:
            continue

    # If we ended up on consent.google.com still, force back to maps.
    if "consent." in page.url:
        try:
            page.goto("https://www.google.com/maps?hl=en", timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:
            pass


def parse_coords_from_url(url: str) -> (Optional[float], Optional[float]):
    """Extract lat/lng from a Google Maps place URL (e.g. !3d35.7..!4d51.4..)."""
    if not url:
        return None, None
    m = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except Exception:
            pass
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except Exception:
            pass
    return None, None


def extract_place(page: Page) -> Place:
    place = Place()

    # Name — try h1 in the main panel.
    place.name = safe_text(page, [
        'h1.DUwDvf',
        '//h1[contains(@class, "DUwDvf")]',
        '//div[contains(@role,"main")]//h1',
    ])

    # Address
    place.address = safe_text(page, [
        'button[data-item-id="address"] >> div.fontBodyMedium',
        '//button[@data-item-id="address"]//div[contains(@class,"fontBodyMedium")]',
        '//button[@aria-label[starts-with(., "Address:")]]',
    ])
    # Strip leading icon text if any
    if place.address.lower().startswith("address:"):
        place.address = place.address.split(":", 1)[1].strip()

    # Website
    place.website = safe_text(page, [
        'a[data-item-id="authority"] >> div.fontBodyMedium',
        '//a[@data-item-id="authority"]//div[contains(@class,"fontBodyMedium")]',
        '//a[contains(@aria-label,"Website")]//div[contains(@class,"fontBodyMedium")]',
    ])

    # Phone
    place.phone_number = safe_text(page, [
        'button[data-item-id^="phone:tel:"] >> div.fontBodyMedium',
        '//button[starts-with(@data-item-id,"phone:tel:")]//div[contains(@class,"fontBodyMedium")]',
        '//button[contains(@aria-label,"Phone")]//div[contains(@class,"fontBodyMedium")]',
    ])
    if not place.phone_number:
        # fall back to data-item-id value itself
        attr = safe_attr(page, ['button[data-item-id^="phone:tel:"]'], 'data-item-id')
        if attr and attr.startswith("phone:tel:"):
            place.phone_number = attr.replace("phone:tel:", "").strip()

    # Plus code
    place.plus_code = safe_text(page, [
        'button[data-item-id="oloc"] >> div.fontBodyMedium',
        '//button[@data-item-id="oloc"]//div[contains(@class,"fontBodyMedium")]',
    ])

    # Place type / category
    place.place_type = safe_text(page, [
        'button.DkEaL',
        '//button[contains(@class,"DkEaL")]',
        '//div[contains(@class,"LBgpqf")]//button',
    ])

    # Introduction / description
    place.introduction = safe_text(page, [
        'div.PYvSYb',
        '//div[contains(@class,"PYvSYb")]',
        '//div[contains(@class,"WeS02d")]//div[contains(@class,"PYvSYb")]',
    ]) or "None Found"

    # Reviews — average and count are commonly displayed near the title.
    avg_raw = safe_text(page, [
        'div.F7nice >> span[aria-hidden="true"]',
        '//div[contains(@class,"F7nice")]//span[@aria-hidden="true"]',
        '//div[contains(@class,"fontDisplayLarge")]',
    ])
    if avg_raw:
        try:
            place.reviews_average = float(avg_raw.replace(',', '.').strip())
        except Exception:
            pass

    count_raw = safe_text(page, [
        'div.F7nice >> span[aria-label*="review" i]',
        '//div[contains(@class,"F7nice")]//span[contains(@aria-label,"review")]',
        '//button[contains(@aria-label,"review") and contains(@class,"HHrUdb")]',
        '//span[contains(@aria-label,"review") and contains(text(),"(")]',
    ])
    if not count_raw:
        # Fallback to aria-label of the parent
        count_raw = safe_attr(page, [
            'div.F7nice >> span[aria-label*="review" i]',
            '//div[contains(@class,"F7nice")]//span[contains(@aria-label,"review")]',
        ], 'aria-label')
    if count_raw:
        digits = re.sub(r'[^\d]', '', count_raw)
        if digits:
            try:
                place.reviews_count = int(digits)
            except Exception:
                pass

    # Store options (shopping / pickup / delivery) — sweep visible info chips
    try:
        chips = page.locator('//div[contains(@class,"LTs0Rc")]').all()
        for chip in chips:
            try:
                text = chip.inner_text(timeout=500).lower()
            except Exception:
                continue
            if 'shop' in text:
                place.store_shopping = "Yes"
            if 'pickup' in text:
                place.in_store_pickup = "Yes"
            if 'delivery' in text:
                place.store_delivery = "Yes"
    except Exception:
        pass

    # Opens at / hours
    opens_raw = safe_text(page, [
        'button[data-item-id="oh"] >> div.fontBodyMedium',
        '//button[@data-item-id="oh"]//div[contains(@class,"fontBodyMedium")]',
        '//div[contains(@class,"MkV9")]//span[contains(@class,"ZDu9vd")]',
    ])
    if opens_raw:
        opens = opens_raw.split('⋅')
        place.opens_at = (opens[1] if len(opens) > 1 else opens_raw).replace(' ', '').strip()

    # URL & coords
    url = page.url
    place.google_maps_url = url
    place.latitude, place.longitude = parse_coords_from_url(url)

    return place


def scroll_results(page: Page, total: int) -> int:
    """Scroll the results feed until at least `total` listings are loaded or end is reached."""
    feed_selectors = [
        'div[role="feed"]',
        '//div[@role="feed"]',
    ]
    feed = None
    for sel in feed_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                feed = loc
                break
        except Exception:
            continue

    previously_counted = 0
    stale_rounds = 0
    while True:
        if feed:
            try:
                feed.evaluate('(el) => el.scrollBy(0, 2000)')
            except Exception:
                page.mouse.wheel(0, 4000)
        else:
            page.mouse.wheel(0, 4000)

        page.wait_for_timeout(1200)

        found = page.locator('//a[contains(@href,"/maps/place/")]').count()
        logging.info(f"Currently found: {found}")

        if found >= total:
            return found

        # Detect end-of-list marker
        end_markers = page.locator('//span[contains(text(),"You\'ve reached the end of the list")] | //p[contains(@class,"fontBodyMedium") and contains(.,"end of the list")]').count()
        if end_markers > 0:
            logging.info("Reached end of list (marker detected)")
            return found

        if found == previously_counted:
            stale_rounds += 1
            if stale_rounds >= 4:
                logging.info("No new results after several scrolls; stopping.")
                return found
        else:
            stale_rounds = 0
        previously_counted = found


def scrape_places(search_for: str, total: int, headless: bool = False) -> List[Place]:
    setup_logging()
    places: List[Place] = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        # Pre-set the CONSENT cookie to skip the GDPR splash entirely.
        context = browser.new_context(
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
        )
        try:
            context.add_cookies([
                {"name": "CONSENT", "value": "YES+cb", "domain": ".google.com", "path": "/"},
                {"name": "SOCS", "value": "CAESHAgBEhJnd3NfMjAyNDA0MDktMF9SQzIaAmVuIAEaBgiAlPmpBg",
                 "domain": ".google.com", "path": "/"},
            ])
        except Exception as e:
            logging.warning(f"Failed to add consent cookie: {e}")

        page = context.new_page()
        try:
            # Go straight to the search URL so we never touch the search input.
            from urllib.parse import quote
            search_url = f"https://www.google.com/maps/search/{quote(search_for)}/?hl=en"
            page.goto(search_url, timeout=120000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=30000)
            except PlaywrightTimeoutError:
                pass

            # If consent still gets in the way, handle it.
            if "consent." in page.url:
                dismiss_consent(page)
                page.goto(search_url, timeout=120000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=30000)
                except PlaywrightTimeoutError:
                    pass

            page.wait_for_timeout(1200)

            # Wait for either a results feed OR a single-place panel.
            try:
                page.wait_for_selector(
                    '//a[contains(@href,"/maps/place/")] | //h1[contains(@class,"DUwDvf")]',
                    timeout=45000,
                )
            except PlaywrightTimeoutError:
                logging.error("No results returned for the search query.")
                return places

            # Single-place direct hit: extract once and return.
            if (
                page.locator('//a[contains(@href,"/maps/place/")]').count() == 0
                and page.locator('//h1[contains(@class,"DUwDvf")]').count() > 0
            ):
                logging.info("Single result detected; extracting directly.")
                place = extract_place(page)
                if place.name:
                    places.append(place)
                return places

            scroll_results(page, total)

            # Collect anchors → deduplicated, capped at total.
            anchors = page.locator('//a[contains(@href,"/maps/place/")]').all()
            unique_hrefs = []
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                except Exception:
                    continue
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)
                unique_hrefs.append(href)
                if len(unique_hrefs) >= total:
                    break

            logging.info(f"Processing {len(unique_hrefs)} unique listings (requested {total})")

            for i, href in enumerate(unique_hrefs, start=1):
                logging.info(f"[{i}/{len(unique_hrefs)}] opening listing")
                anchor = page.locator(f'//a[@href="{href}"]').first
                try:
                    anchor.scroll_into_view_if_needed(timeout=5000)
                    anchor.click(timeout=10000)
                except Exception as e:
                    logging.warning(f"Click failed, navigating directly: {e}")
                    try:
                        page.goto(href, timeout=30000)
                    except Exception as ee:
                        logging.warning(f"Navigate failed too: {ee}")
                        continue

                try:
                    page.wait_for_selector(
                        '//h1[contains(@class,"DUwDvf")]',
                        timeout=15000,
                    )
                except PlaywrightTimeoutError:
                    logging.warning("Detail panel didn't load in time; skipping.")
                    continue

                page.wait_for_timeout(1200)
                try:
                    place = extract_place(page)
                except Exception as e:
                    logging.warning(f"Extraction error: {e}")
                    continue

                if place.name:
                    places.append(place)
                else:
                    logging.warning("No name extracted; skipping listing.")
        finally:
            context.close()
            browser.close()
    return places


def save_places_to_csv(places: List[Place], output_path: str = "result.csv", append: bool = False):
    if not places:
        logging.warning("No data to save.")
        return
    df = pd.DataFrame([asdict(p) for p in places])
    # Drop exact duplicate rows but KEEP columns even if all values are identical.
    df.drop_duplicates(inplace=True)
    file_exists = os.path.isfile(output_path)
    mode = "a" if append else "w"
    header = not (append and file_exists)
    df.to_csv(output_path, index=False, mode=mode, header=header, encoding="utf-8-sig")
    logging.info(f"Saved {len(df)} places to {output_path} (append={append})")


def main():
    parser = argparse.ArgumentParser(description="Google Maps business scraper")
    parser.add_argument("-s", "--search", type=str, required=True, help="Search query for Google Maps")
    parser.add_argument("-t", "--total", type=int, default=20, help="Total number of results to scrape")
    parser.add_argument("-o", "--output", type=str, default="result.csv", help="Output CSV file path")
    parser.add_argument("--append", action="store_true", help="Append results to the output file instead of overwriting")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    places = scrape_places(args.search, args.total, headless=args.headless)
    save_places_to_csv(places, args.output, append=args.append)


if __name__ == "__main__":
    main()
