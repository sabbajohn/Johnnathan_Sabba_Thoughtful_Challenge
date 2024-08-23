import os
import re
import logging
from datetime import datetime, timedelta
from RPA.Browser.Selenium import Selenium
from RPA.Robocorp.WorkItems import WorkItems
import pandas as pd

# Initialize the Selenium and WorkItems libraries
browser = Selenium()
work_items = WorkItems()


def configure_logging():
    """Set up logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def open_website(url):
    """Open the news website."""
    logging.info(f"Opening website: {url}")
    browser.open_available_browser(url)


def search_news(search_phrase):
    """Search for news articles."""
    logging.info(f"Searching for news with phrase: {search_phrase}")
    search_box_xpath = '//input[@type="search"]'
    browser.input_text_when_element_is_visible(search_box_xpath, search_phrase)
    browser.press_keys(search_box_xpath, "ENTER")
    browser.wait_until_page_contains_element(
        '//div[contains(@class, "search-results")]'
    )


def filter_news_by_category(category):
    """Filter news articles by category, if applicable."""
    logging.info(f"Filtering news by category: {category}")
    category_xpath = f'//a[contains(text(), "{category}")]'
    if browser.does_page_contain_element(category_xpath):
        browser.click_element(category_xpath)
    else:
        logging.warning(
            f"Category '{category}' not found. Proceeding without category filter."
        )


def gather_news_data(search_phrase, months):
    """Gather news data based on search criteria."""
    news_data = []
    current_date = datetime.now()
    past_date = current_date - timedelta(days=30 * months)

    logging.info(f"Gathering news data from the past {months} months.")
    news_items = browser.find_elements('//article[contains(@class, "story")]')
    for item in news_items:
        try:
            title = browser.get_text(item.find_element_by_xpath(".//h2"))
            date_text = browser.get_text(item.find_element_by_xpath(".//time"))
            date = datetime.strptime(date_text, "%b %d, %Y")
            if date < past_date:
                continue
            description = browser.get_text(item.find_element_by_xpath(".//p"))
            image_element = item.find_element_by_xpath(".//img")
            image_url = image_element.get_attribute("src")
            image_filename = download_image(image_url)
            search_phrase_count = count_occurrences(
                search_phrase, title + " " + description
            )
            contains_money = check_for_money(title + " " + description)
            news_data.append(
                [
                    title,
                    date_text,
                    description,
                    image_filename,
                    search_phrase_count,
                    contains_money,
                ]
            )
        except Exception as e:
            logging.warning(f"Error processing a news item: {e}")

    return news_data


def count_occurrences(search_phrase, text):
    """Count occurrences of the search phrase in text."""
    return text.lower().count(search_phrase.lower())


def check_for_money(text):
    """Check if text contains any monetary amounts."""
    money_patterns = [r"\$\d+(\.\d{2})?", r"\d+ dollars", r"\d+ USD"]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in money_patterns)


def download_image(url):
    """Download the image from the given URL."""
    logging.info(f"Downloading image from {url}")
    image_filename = os.path.join("output", "images", os.path.basename(url))
    browser.download_file(url, image_filename)
    return image_filename


def save_to_excel(news_data):
    """Save news data to an Excel file."""
    logging.info("Saving news data to Excel file.")
    df = pd.DataFrame(
        news_data,
        columns=[
            "Title",
            "Date",
            "Description",
            "Image Filename",
            "Search Phrase Count",
            "Contains Money",
        ],
    )
    output_path = os.path.join("output", "news_data.xlsx")
    df.to_excel(output_path, index=False)
    logging.info(f"Data saved to {output_path}")


def main():
    """Main function to run the news scraper."""
    configure_logging()
    work_items.get_input_work_item()

    search_phrase = work_items.get_work_item_variable("search_phrase")
    news_category = work_items.get_work_item_variable("news_category")
    months = int(work_items.get_work_item_variable("months"))
    news_url = work_items.get_work_item_variable(
        "news_url", default="https://www.reuters.com/"
    )

    try:
        open_website(news_url)
        search_news(search_phrase)
        filter_news_by_category(news_category)
        news_data = gather_news_data(search_phrase, months)
        save_to_excel(news_data)
        work_items.complete_output_work_item()
    finally:
        browser.close_browser()


if __name__ == "__main__":
    main()
