import os
import requests
from bs4 import BeautifulSoup
import string
import re
import sys

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)

def download_images_from_url(url, download_folder):
    try:
        # Get the page content
        response = requests.get(url)
        response.raise_for_status()
        page_content = response.content

        # Parse the page content
        soup = BeautifulSoup(page_content, 'html.parser')

        # Extract the page title
        page_title = soup.title.string.strip() if soup.title else "Unnamed_Page"
        sanitized_title = sanitize_filename(page_title)

        # Extract item number
        item_number_match = re.search(r'/itm/(\d+)', url)
        item_number = item_number_match.group(1) if item_number_match else "Unknown"

        # Create a subfolder named after the listing title and item number
        folder_name = f"{sanitized_title}_{item_number}"
        listing_folder = os.path.join(download_folder, folder_name)
        os.makedirs(listing_folder, exist_ok=True)
        print(f"Created folder: {listing_folder}")

        # Find all image tags that are NOT within the specified div classes
        img_tags = [img for img in soup.find_all('img')
                    if not img.find_parent('div', class_='x-sellercard-atf__image') and
                       not img.find_parent('div', class_='x-store-information__logo-wrapper')]
        print(f"Found {len(img_tags)} valid image tags on {url}")

        # Filter and transform image URLs to end with 's-l1600.jpg'
        img_urls = []
        unique_ids = set()
        for img in img_tags:
            image_src = img.get('src') or img.get('data-src')
            if image_src and image_src.startswith('https://i.ebayimg.com/images/g/'):
                id_match = re.search(r'g/([^/]+)/', image_src)
                if id_match:
                    image_id = id_match.group(1)
                    if image_id not in unique_ids:
                        unique_ids.add(image_id)
                        high_res_url = image_src.rsplit('/', 1)[0] + '/s-l1600.jpg'
                        img_urls.append(high_res_url)
        print(f"Filtered {len(img_urls)} image URLs on {url}")

        # Download the images
        for index, img_url in enumerate(img_urls):
            try:
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                # Save the image with a name based on the index
                img_name = f"image_{index + 1}.jpg"
                img_path = os.path.join(listing_folder, img_name)
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                print(f"Downloaded {img_name}")
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")
    except Exception as e:
        print(f"Failed to process URL {url}: {e}")

def download_images_from_list(txt_file, download_folder):
    # Create a directory for the images if it doesn't exist
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        print(f"Created directory: {download_folder}")

    # Read URLs from the text file
    with open(txt_file, 'r') as file:
        urls = file.readlines()

    # Download images from each URL
    for url in urls:
        url = url.strip()
        if url:
            download_images_from_url(url, download_folder)

def main():
    if len(sys.argv) < 3:
        print("Usage: python ebaydl.py <url or txt_file> <download_folder>")
        sys.exit(1)

    input_file_or_url = sys.argv[1]
    download_folder = sys.argv[2]

    if os.path.isfile(input_file_or_url):  # If it's a text file
        download_images_from_list(input_file_or_url, download_folder)
    elif input_file_or_url.startswith('http'):  # If it's a single URL
        download_images_from_url(input_file_or_url, download_folder)
    else:
        print("Error: The first argument must be a valid URL or text file containing URLs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
