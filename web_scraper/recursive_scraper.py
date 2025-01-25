# recursive_scraper.py
import os
import json
from scraper import scrape_and_process_data  # Assuming scraper.py contains scrape_and_process_data

def recursive_scrape(url, save_dir, level=0, current_level=0, file_counter=None, mappings=None):
    """
    Recursively scrape a URL and its links up to the specified depth level.

    Parameters:
        url (str): The URL to scrape.
        save_dir (str): Directory to save the scraped data.
        level (int): Depth level to scrape. Level 0 is only the initial URL, level 1 includes its direct links.
        current_level (int): Current depth level of the recursion (used internally).
        file_counter (dict): A dictionary to keep track of file numbering per level.
        mappings (dict): A dictionary to store mappings for the current level.
    """
    if file_counter is None:
        file_counter = {}

    if mappings is None:
        mappings = {}

    if current_level > level:
        return

    # Initialize the counter for the current level if not present
    if current_level not in file_counter:
        file_counter[current_level] = 1

    level_dir = os.path.join(save_dir, f"level_{current_level}")
    os.makedirs(level_dir, exist_ok=True)

    # Define file name as level_X_fileY.json
    file_name = f"level_{current_level}_file{file_counter[current_level]}.json"
    save_path = os.path.join(level_dir, file_name)
    file_counter[current_level] += 1  # Increment the counter for the current level

    # Scrape and save data
    scrape_and_process_data(url, save_path)

    # Add mapping of file name to URL
    mappings[file_name] = url


    # Save mappings to a mapping.json file at the current level directory
    mapping_path = os.path.join(level_dir, "mapping.json")
    with open(mapping_path, 'w', encoding='utf-8') as mapping_file:
        json.dump(mappings, mapping_file, ensure_ascii=False, indent=4)

    # If not at the maximum level, recursively scrape all links
    if current_level < level:
        with open(save_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        for link in data.get("all_links", []):
            # Recursively scrape links
            recursive_scrape(link, save_dir, level, current_level + 1, file_counter, mappings)

    # Clear mappings for next level
    if current_level == 0:
        mappings.clear()

# Example Usage
if __name__ == "__main__":
    website_url = "https://stadt.muenchen.de/en/info/entry-visa.html"  # Replace with the target URL
    output_directory = "web_scraper/recursive_scraped_data"  # Output directory
    os.makedirs(output_directory, exist_ok=True)

    recursive_scrape(website_url, output_directory, level=1)
