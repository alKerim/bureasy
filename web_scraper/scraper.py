# scraper.py
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

# Function to extract phone numbers
def extract_phone_numbers(text):
    """
    Extracts phone numbers from the given text using an improved regex pattern.

    Parameters:
        text (str): The text content from which to extract phone numbers.

    Returns:
        list: A list of extracted phone numbers in standardized format.
    """
    # Enhanced regex for phone numbers
    phone_regex = re.compile(
        r'''(?x)                  # Verbose mode
        (?:(?:\+|00)\d{1,3}[\s.-]?)?  # Optional country code
        (?:\(?\d{1,4}\)?[\s.-]?)?    # Optional area code with or without parentheses
        \d{2,4}                       # First part of the number
        [\s.-]?                       # Separator
        \d{2,4}                       # Second part of the number
        [\s.-]?                       # Separator
        \d{2,4}                       # Third part of the number
        '''
    )

    # Find all matches in the text
    raw_phone_numbers = phone_regex.findall(text)

    # Process and clean the extracted phone numbers
    phone_numbers = []
    for match in phone_regex.finditer(text):
        phone = match.group()
        # Remove any surrounding whitespace
        phone = phone.strip()
        # Optional: Further clean the phone number (e.g., remove multiple separators)
        phone = re.sub(r'[\s.-]+', ' ', phone)
        # Validate the length (e.g., total digits between 7 and 15)
        digits = re.sub(r'\D', '', phone)  # Remove non-digit characters
        if 7 <= len(digits) <= 15:
            phone_numbers.append(phone)

    return phone_numbers

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

    # Extract phone numbers
    phone_numbers = extract_phone_numbers(page_text)

    # Extract links
    all_listed_links = extract_all_links(url, html_content)

    # Create JSON object
    data = {
        "url": url,
        "text": page_text,
        "pdf_links": pdf_links,
        "phone_numbers": phone_numbers,
        "all_links": all_listed_links
    }

    # Save JSON to file
    with open(save_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print(f"Data saved to {save_path}")
