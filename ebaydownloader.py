import os
sys.stdout = open(os.devnull, 'w')

import requests
from bs4 import BeautifulSoup
import string
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import PhotoImage
import pygame  # For playing sound

# Initialize pygame mixer for sound
pygame.mixer.init()

def sanitize_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)

def play_sound(sound_on):
    if sound_on:
        try:
            # Specify the path to your sound file
            sound_file = "ebay.mp3"
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")

def download_images_from_url(url, download_folder, sound_on):
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

        # Play sound after all images have been downloaded
        play_sound(sound_on)
    except Exception as e:
        print(f"Failed to process URL {url}: {e}")

def download_images_from_list(txt_file, download_folder, sound_on):
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
            download_images_from_url(url, download_folder, sound_on)

def browse_txt_file():
    return filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])

def browse_folder():
    return filedialog.askdirectory()

def start_download(single_url, txt_file, download_folder, sound_on):
    if not download_folder:
        messagebox.showerror("Error", "Please select a download folder.")
        return

    if single_url:
        download_images_from_url(single_url, download_folder, sound_on)
    elif txt_file:
        download_images_from_list(txt_file, download_folder, sound_on)
    else:
        messagebox.showerror("Error", "Please provide either a URL or a TXT file.")
        return

    # messagebox.showinfo("Success", "Download complete.")

def main():
    # Create the main window
    root = tk.Tk()
    root.title("eBay Image Downloader")
    root.geometry("600x400")
    
    # Window icon
    root.iconbitmap("ebay_downloader.ico")

    # Load an image for the header
    try:
        header_image = PhotoImage(file="ebayimagedownloader.png")  # Replace 'header.png' with your image file
    except Exception as e:
        header_image = None
        print("Failed to load header image:", e)

    # Styling
    style = ttk.Style()
    style.configure("TLabel", font=("Arial", 10))  # Use Arial or any other simple font
    style.configure("TButton", font=("Arial", 10), background="#F0F0F0", foreground="black")
    style.configure("Header.TLabel", font=("Arial", 14, "bold"))

    # Header
    header_frame = ttk.Frame(root, padding="10")
    header_frame.pack(fill=tk.X)
    if header_image:
        header_label = tk.Label(header_frame, image=header_image)
        header_label.pack(pady=5)
    else:
        header_label = ttk.Label(header_frame, text="eBay Image Downloader", style="Header.TLabel", anchor=tk.CENTER)
        header_label.pack(pady=10)

    # Content Frame
    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    # Grid layout adjustments
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=2)
    frame.grid_columnconfigure(2, weight=1)

    ttk.Label(frame, text="Single URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    url_entry = ttk.Entry(frame, width=50)
    url_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame, text="TXT File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    txt_file_entry = ttk.Entry(frame, width=50)
    txt_file_entry.grid(row=1, column=1, padx=5, pady=5)
    txt_file_button = ttk.Button(frame, text="Browse", command=lambda: txt_file_entry.insert(0, browse_txt_file()))
    txt_file_button.grid(row=1, column=2, padx=5, pady=5)

    ttk.Label(frame, text="Download Folder:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    folder_entry = ttk.Entry(frame, width=50)
    folder_entry.grid(row=2, column=1, padx=5, pady=5)
    folder_button = ttk.Button(frame, text="Browse", command=lambda: folder_entry.insert(0, browse_folder()))
    folder_button.grid(row=2, column=2, padx=5, pady=5)

    # Sound option
    sound_var = tk.BooleanVar(value=True)
    sound_checkbox = ttk.Checkbutton(frame, text="Play sound when done", variable=sound_var)
    sound_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

    # Download button
    download_button = ttk.Button(frame, text="Start Download", 
                                 command=lambda: start_download(url_entry.get().strip(),
                                                                txt_file_entry.get().strip(),
                                                                folder_entry.get().strip(),
                                                                sound_var.get()))
    download_button.grid(row=4, column=0, columnspan=3, pady=20)

    # Footer
    footer_frame = ttk.Frame(root, padding="10")
    footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
    footer_label = ttk.Label(footer_frame, text="eBay Image Downloader v1.0 by Ziggy", font=("Arial", 8), anchor=tk.CENTER)
    footer_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
