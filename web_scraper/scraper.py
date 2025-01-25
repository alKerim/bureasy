# scraper.py

import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberMatcher

# Function to fetch a web page
def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Function to extract PDF links
def extract_pdf_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.lower().endswith('.pdf'):  # Check if it's a PDF link (case-insensitive)
            pdf_links.append(urljoin(base_url, href))
    return pdf_links

# Function to extract text content
def extract_text_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

# Function to check if a string matches a common date format
def is_date_format(text):
    """
    Checks if the given text matches a common date format.

    Parameters:
        text (str): The text to check.

    Returns:
        bool: True if text matches a date pattern, False otherwise.
    """
    date_regex = re.compile(
        r'''(?x)
        \b(0?[1-9]|[12][0-9]|3[01])        # Day: 1-31
        [\s./-]                             # Separator
        (0?[1-9]|1[012])                    # Month: 1-12
        [\s./-]                             # Separator
        (\d{4}|\d{2})\b                      # Year: 2 or 4 digits
        '''
    )
    return bool(date_regex.search(text))

# Function to extract phone numbers with context using PhoneNumberMatcher
def extract_phone_numbers_with_context(text, default_region='DE', context_length=200):
    """
    Extracts phone numbers from the given text along with their surrounding context.

    Parameters:
        text (str): The text content from which to extract phone numbers.
        default_region (str): The default region code (e.g., 'DE' for Germany).
        context_length (int): Number of characters to extract on each side of the phone number.

    Returns:
        list: A list of dictionaries containing the phone number and its context.
    """
    phone_entries = []

    # Use PhoneNumberMatcher to find phone numbers in the text
    matcher = PhoneNumberMatcher(text, default_region)

    for match in matcher:
        try:
            parsed_number = match.number
            # Validate the phone number
            if phonenumbers.is_possible_number(parsed_number) and phonenumbers.is_valid_number(parsed_number):
                # Format the number in E.164 format
                formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)

                # Extract context
                start_idx = max(match.start - context_length, 0)
                end_idx = min(match.end + context_length, len(text))
                left_context = text[start_idx:match.start].strip()
                right_context = text[match.end:end_idx].strip()

                # Original matched text (for date exclusion)
                original_phone = match.raw_string

                # Exclude if the number matches a date pattern
                if not is_date_format(original_phone):
                    phone_entries.append({
                        "number": formatted_number,
                        "left_context": left_context,
                        "right_context": right_context
                    })
        except NumberParseException:
            continue  # Skip numbers that can't be parsed

    return phone_entries

# Function to extract all links
def extract_all_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    all_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Convert relative links to absolute links
        absolute_link = urljoin(base_url, href)
        # Optional: Remove fragments and query parameters
        absolute_link = absolute_link.split('#')[0].split('?')[0]
        all_links.append(absolute_link)
    return all_links

# Main function to scrape and process data
def scrape_and_process_data(url, save_path):
    print(f"Scraping {url}...")
    try:
        html_content = fetch_page(url)
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return

    # Extract PDFs
    pdf_links = extract_pdf_links(url, html_content)

    # Extract text
    page_text = extract_text_content(html_content)

    # Extract phone numbers with context
    phone_numbers = extract_phone_numbers_with_context(page_text)

    # Extract links
    all_listed_links = extract_all_links(url, html_content)

    # Create JSON object
    data = {
        "url": url,
        "text": page_text,
        "pdf_links": pdf_links,
        "phone_numbers": phone_numbers,  # Now a list of dicts with number and context
        "all_links": all_listed_links
    }

    # Save JSON to file
    with open(save_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print(f"Data saved to {save_path}")
