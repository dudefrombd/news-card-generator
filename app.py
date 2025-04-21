import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime
import textwrap  # For text wrapping
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import matplotlib
matplotlib.use('Agg')

# Function to extract news details from the URL
def extract_news_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad HTTP status
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extracting date with error handling for missing tag
        date_tag = soup.find('meta', {'property': 'article:published_time'})
        date_str = date_tag['content'] if date_tag else None
        # Convert date string to datetime object
        pub_date = None
        if date_str:
            try:
                pub_date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                pub_date = None

        # Extracting headline with error handling for missing tag
        headline_tag = soup.find('meta', {'property': 'og:title'})
        headline = headline_tag['content'] if headline_tag else 'Headline not found'

        # Extracting image URL with error handling for missing tag
        image_tag = soup.find('meta', {'property': 'og:image'})
        image_url = image_tag['content'] if image_tag else None

        # Extracting source with error handling for missing tag (optional)
        source_tag = soup.find('meta', {'property': 'og:site_name'})
        source = source_tag['content'] if source_tag else 'Source not found'

        return pub_date, headline, image_url, source
    except Exception as e:
        raise Exception(f"Failed to extract news data: {str(e)}")

# Function to download and load an image from a URL
def download_image(image_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        return Image.open(image_data)
    except Exception as e:
        raise Exception(f"Failed to download image: {str(e)}")

# Function to render text with matplotlib and return as a PIL image
def render_text_with_matplotlib(text, font_path, font_size, text_color, max_width_pixels):
    font = FontProperties(fname=font_path, size=font_size)
    fig, ax = plt.subplots(figsize=(max_width_pixels / 100, 1), facecolor='none')  # Convert pixels to inches (approx)
    ax.axis('off')
    ax.text(0.5, 0.5, text, ha='center', va='center', fontproperties=font, color=text_color)
    fig.canvas.draw()
    # Convert matplotlib figure to numpy array
    image_data = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    image_data = image_data.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    # Convert ARGB to RGBA
    image_data = np.roll(image_data, -1, axis=2)
    # Create PIL image
    image = Image.frombytes("RGBA", image_data.shape[:2], image_data)
    plt.close(fig)
    # Trim transparent borders
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    return image

# Function to create the news card
def create_photo_card(headline, image_url, pub_date, logo_path="logo.png", output_path="photo_card.png"):
    try:
        # Create a blank canvas (1080x1080, blue background)
        canvas = Image.new("RGB", (1080, 1080), "#003087")  # Blue background
        draw = ImageDraw.Draw(canvas)

        # Load fonts for non-Bangla text (Pillow)
        try:
            regular_font = ImageFont.truetype("Arial.ttf", 30)
        except IOError:
            print("Warning: Arial.ttf not found, using default font.")
            regular_font = ImageFont.load_default()

        # Add the date (top center, with padding from top)
        date_str = pub_date.strftime("%d April %Y") if pub_date else datetime.datetime.now().strftime("%d April %Y")
        date_box_width = 300
        date_box_height = 60
        date_box_x = (1080 - date_box_width) // 2
        date_box_y = 50  # Padding from top
        draw.rectangle((date_box_x, date_box_y, date_box_x + date_box_width, date_box_y + date_box_height), fill="white")
        draw.text((date_box_x + 40, date_box_y + 15), date_str, fill="black", font=regular_font)

        # Download and add the news image (resize to 840x600)
        image_y = date_box_y + date_box_height + 40  # Gap between date and image (40 pixels)
        if image_url:
            news_image = download_image(image_url)
            news_image = news_image.resize((840, 600), Image.Resampling.LANCZOS)
            # Center the image horizontally
            image_x = (1080 - 840) // 2  # 120
            canvas.paste(news_image, (image_x, image_y))
        else:
            # Draw a placeholder if no image is available
            draw.rectangle((120, image_y, 960, image_y + 600), fill="gray")
            draw.text((400, image_y + 300), "No Image Available", fill="white", font=regular_font)

        # Add a yellow border around the image
        draw.rectangle((120, image_y, 960, image_y + 600), outline="yellow", width=5)

        # Debug: Draw a simple Bangla string to test font rendering (using matplotlib)
        test_bangla = "টেস্ট বাংলা টেক্সট"
        test_image = render_text_with_matplotlib(test_bangla, "SolaimanLipi.ttf", 50, "red", 900)
        test_x = 50
        test_y = 750
        canvas.paste(test_image, (test_x, test_y), test_image)

        # Add the headline (below the image, centered, within a fixed area, using matplotlib)
        max_width = 900  # Fixed width for the headline area
        # Test with a hardcoded Bangla string if the extracted headline fails
        if "not found" in headline.lower():
            headline = "পরিবারে অশান্তি বিশ্ববিদ্যালয়ের পড়াশোনা হত্যার গ্রেপ্তার"
        headline = headline.encode('utf-8').decode('utf-8')  # Ensure UTF-8 encoding for Bangla
        # Wrap the text to fit within max_width
        wrapped_text = textwrap.wrap(headline, width=40)
        headline_y = image_y + 600 + 30  # Start 30 pixels below the image (y=780)
        for line in wrapped_text:
            # Render each line with matplotlib
            headline_image = render_text_with_matplotlib(line, "SolaimanLipi.ttf", 50, "white", 900)
            # Center the rendered image
            headline_width = headline_image.width
            text_x = (1080 - headline_width) // 2
            canvas.paste(headline_image, (text_x, headline_y), headline_image)
            headline_y += 60  # Move down for the next line (line spacing)

        headline = "টেস্ট হেডলাইন"

        # Add the logo (bottom left) with transparency
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((150, 75), Image.Resampling.LANCZOS)
            canvas.paste(logo, (40, 950), logo)
        except FileNotFoundError:
            draw.text((40, 950), "Logo Missing", fill="red", font=regular_font)

        # Add website text below the logo
        draw.text((200, 970), "Visit our site", fill="yellow", font=regular_font)

        # Add website URL (bottom right)
        draw.text((850, 970), "facebook/leadne", fill="white", font=regular_font)

        # Save the photo card
        canvas.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to create photo card: {str(e)}")

# Streamlit app
st.title("Automated News Photo Card Generator")
url = st.text_input("Enter the news article URL:")

if st.button("Generate Photo Card"):
    if url:
        try:
            # Extract data (unpack all four values)
            pub_date, headline, image_url, source = extract_news_data(url)
            # Create photo card
            output_path = create_photo_card(headline, image_url, pub_date)
            # Display the result
            st.image(output_path, caption="Generated Photo Card")
            with open(output_path, "rb") as file:
                st.download_button("Download Photo Card", file, file_name="photo_card.png")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid URL.")
