import os
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
        if href.endswith('.pdf'):  # Check if it's a PDF link
            pdf_links.append(urljoin(base_url, href))
    return pdf_links

# Function to extract text content
def extract_text_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(strip=True)

# Function to extract phone numbers
def extract_phone_numbers(text):
    phone_numbers = re.findall(r'\b\d{9,15}\b', text)  # Matches 9-15 digit phone numbers


    return phone_numbers

# Function to extract all links
def extract_all_links(base_url, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    all_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Convert relative links to absolute links
        absolute_link = urljoin(base_url, href)
        all_links.append(absolute_link)
    return all_links



# Function to save phone numbers to a JSON file
def save_phone_numbers_to_json(phone_numbers, save_path):
    phone_data = {}
    for phone in phone_numbers:
        phone_data[phone] = "telefonnummer zu diesem und dem service"

    with open(save_path, 'w', encoding='utf-8') as json_file:
        json.dump(phone_data, json_file, ensure_ascii=False, indent=4)

# Function to save links to a text file
def save_links_to_file(links, save_path):
    with open(save_path, 'w', encoding='utf-8') as links_file:
        for link in links:
            links_file.write(link + '\n')

# Function to download PDFs
def download_pdfs(pdf_links, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    for pdf_url in pdf_links:
        pdf_name = pdf_url.split('/')[-1]
        pdf_path = os.path.join(save_dir, pdf_name)

        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        with open(pdf_path, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                pdf_file.write(chunk)

        print(f"Downloaded: {pdf_name}")

# Main function to scrape, process, and store data
def scrape_and_process_data(url, save_dir):
    print(f"Scraping {url}...")
    html_content = fetch_page(url)

    # Extract PDFs
    pdf_links = extract_pdf_links(url, html_content)
    if pdf_links:
        print(f"Found {len(pdf_links)} PDFs. Downloading...")
        download_pdfs(pdf_links, save_dir)
    else:
        print("No PDFs found on the page.")

    # Extract text
    page_text = extract_text_content(html_content)
    text_file = os.path.join(save_dir, "associated_text.txt")
    with open(text_file, 'w', encoding='utf-8') as text_out:
        text_out.write(page_text)
    print("Text content saved.")

    # Extract phone numbers
    phone_numbers = extract_phone_numbers(page_text)
    if phone_numbers:
        print(f"Found {len(phone_numbers)} phone numbers. Saving to JSON...")
        save_phone_numbers_to_json(phone_numbers, save_dir + "/phone_numbers.json")
    else:
        print("No phone numbers found.")

    # Extract links
    all_listed_links = extract_all_links(page_text, html_content)
    if all_listed_links:
        print(f"Found {len(all_listed_links)} outgoing links. Saving to JSON...")
        save_links_to_file(all_listed_links, save_dir + "/all_links.txt")
    else:
        print("No links found.")




# Example Usage
website_url = "https://stadt.muenchen.de/en/info/entry-visa.html"  # Replace with the target URL
output_directory = "web_scraper/scraped_data"


scrape_and_process_data(website_url, output_directory)
