from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# Set up browser
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://www.myscheme.gov.in/search")
time.sleep(5)

csv_filename = "myscheme_full_data.csv"
header = [
    "Scheme Name",
    "Ministries/Departments",
    "Description & Benefits",
    "Tags"
]
data_rows = []
base_url = "https://www.myscheme.gov.in"

def scroll_to_bottom():
    for _ in range(30):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(0.2)

def get_scheme_cards():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return soup.select("div.p-4.lg\\:p-8.w-full")

def get_text_from_element(soup, selector):
    element = soup.select_one(selector)
    return element.text.strip() if element else "-"

page_num = 1

while page_num <= 360:
    print(f"\n🔄 Scraping page {page_num}...")

    # Scroll to the bottom to load more data
    scroll_to_bottom()
    time.sleep(1)

    # Get scheme cards from the page
    scheme_cards = get_scheme_cards()
    if not scheme_cards:
        print("⚠️ No schemes found on page. Ending.")
        break

    for i, card in enumerate(scheme_cards):
        try:
            # Extract data for each scheme directly from the summary
            scheme_name = get_text_from_element(card, "a.block span")
            ministries = get_text_from_element(card, "h2.mt-3")
            description = get_text_from_element(card, "span.line-clamp-2 span")
            tags = [tag.get("title") for tag in card.select("div[title]")]
            
            # Append the data
            data_rows.append([
                scheme_name,
                ministries,
                description,
                ", ".join(tags)
            ])
            
            print(f"✅ [{i+1}/{len(scheme_cards)}] {scheme_name}")

        except Exception as e:
            print(f"⚠️ Error scraping card {i}: {e}")

    # Go to next page
    try:
        print(f"➡️ Moving to page {page_num + 1}...")

        # Wait for pagination to be loaded
        wait = WebDriverWait(driver, 10)
        pagination_ul = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.flex.flex-wrap.items-center.justify-center")))
        li_elements = pagination_ul.find_elements(By.TAG_NAME, "li")

        next_li = None
        for idx, li in enumerate(li_elements):
            classes = li.get_attribute("class")
            if "!text-white" in classes and "bg-green-700" in classes:
                if idx + 1 < len(li_elements):
                    next_li = li_elements[idx + 1]
                    break

        if not next_li:
            print("🛑 No next page <li> found. Ending.")
            break

        # Scroll to the next page button and click it
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_li)
        time.sleep(0.5)
        next_li.click()

        # Ensure the next page is fully loaded before continuing
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.p-4.lg\\:p-8.w-full")))
        page_num += 1
        time.sleep(3)

    except Exception as e:
        print(f"🛑 Error clicking next page: {e}")
        break

# Save to CSV
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data_rows)

print(f"\n✅ Done. Scraped {len(data_rows)} records and saved to {csv_filename}")
driver.quit()
