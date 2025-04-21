import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime
import textwrap
import re
import os
from urllib.parse import urlparse

# Constants for layout and styling
CANVAS_SIZE = (1080, 1080)
BRICK_RED = "#9E2A2F"  # Main color
NAVY_BLUE = "#003366"  # Complementary color for bottom section
MUSTARD_YELLOW = "#FFB300"  # Border color for image and divider
IMAGE_SIZE = (840, 600)
IMAGE_POSITION = (120, 150)  # Adjusted for centering
DATE_BOX_SIZE = (300, 60)
DATE_POSITION = (390, 50)  # (1080 - 300) // 2 = 390
DATE_GAP = 40  # Gap between date box and image
HEADLINE_MAX_WIDTH = 900
HEADLINE_Y_START = 780  # Image at y=150, height=600, gap=30
HEADLINE_LINE_SPACING = 60
HEADLINE_BOTTOM_PADDING = 20  # Padding below headline before divider
DIVIDER_THICKNESS = 5  # Thickness of the divider (matches image border)
PADDING = 60  # Padding for left (logo), right (source), and bottom
LOGO_SOURCE_TOP_PADDING = 20  # Padding above logo/source section
LOGO_MAX_SIZE = (225, 113)  # Max size of logo

# Function to validate URL
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
        r'(/[^?\s]*)?$'  # optional path
    )
    return re.match(regex, url) is not None

# Function to extract main domain from URL
def extract_main_domain(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove "www." if present
        if domain.startswith("www."):
            domain = domain[4:]
        # Split by dots
        parts = domain.split(".")
        if len(parts) >= 3:
            # Check if the second-to-last part is a common suffix (e.g., "co" in "co.uk")
            common_suffixes = ["co", "org", "gov", "edu"]
            if parts[-2] in common_suffixes:
                # Take the last three parts (e.g., bbc.co.uk)
                return ".".join(parts[-3:])
        # Otherwise, take the last two parts (e.g., ntvbd.com -> ntvbd)
        return ".".join(parts[-2:])
    except Exception:
        return "Unknown"

# Function to extract news details from the URL
def extract_news_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract date
        date_tag = soup.find('meta', {'property': 'article:published_time'})
        date_str = date_tag['content'] if date_tag else None
        pub_date = None
        if date_str:
            try:
                pub_date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                pub_date = None

        # Extract headline
        headline_tag = soup.find('meta', {'property': 'og:title'})
        headline = headline_tag['content'] if headline_tag else 'Headline not found'

        # Extract image URL
        image_tag = soup.find('meta', {'property': 'og:image'})
        image_url = image_tag['content'] if image_tag else None

        # Extract source
        source_tag = soup.find('meta', {'property': 'og:site_name'})
        source = source_tag['content'] if source_tag else 'Source not found'

        # Extract main domain from URL
        main_domain = extract_main_domain(url)

        return pub_date, headline, image_url, source, main_domain
    except Exception as e:
        raise Exception(f"Failed to extract news data: {str(e)}")

# Function to download, crop, and load an image from a URL
def download_image(image_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        image = Image.open(image_data)

        # Crop the bottom 15% of the image
        width, height = image.size
        crop_height = int(height * 0.15)  # 15% of the height
        new_height = height - crop_height
        box = (0, 0, width, new_height)  # Crop from bottom
        image = image.crop(box)

        return image
    except Exception as e:
        raise Exception(f"Failed to download or crop image: {str(e)}")

# Function to load fonts with fallbacks and error handling
def load_fonts():
    bangla_font_small = bangla_font_large = regular_font = bold_font = None

    # Load Bangla fonts with fallbacks
    bangla_fonts = ["SolaimanLipi.ttf", "NotoSerifBengali-Regular.ttf", "Kalpurush.ttf"]
    for font_file in bangla_fonts:
        try:
            if not os.path.exists(font_file):
                continue
            bangla_font_small = ImageFont.truetype(font_file, 30)
            bangla_font_large = ImageFont.truetype(font_file, 50)
            break
        except IOError:
            pass
    if bangla_font_small is None:
        bangla_font_small = bangla_font_large = ImageFont.load_default()

    # Load regular font for non-Bangla text
    try:
        regular_font = ImageFont.truetype("Arial.ttf", 30)
    except IOError:
        regular_font = ImageFont.load_default()

    # Load bold font for date text
    try:
        bold_font = ImageFont.truetype("Arial-Bold.ttf", 30)
    except IOError:
        # Fallback to a bold variant or default if Arial Bold is not available
        try:
            bold_font = ImageFont.truetype("Arial Bold.ttf", 30)
        except IOError:
            bold_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font, bold_font

# Function to resize image while preserving aspect ratio
def resize_with_aspect_ratio(image, max_size):
    original_width, original_height = image.size
    max_width, max_height = max_size
    aspect_ratio = original_width / original_height

    # Calculate new dimensions while preserving aspect ratio
    if original_width > original_height:
        # Width is the limiting factor
        new_width = min(original_width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        # Height is the limiting factor
        new_height = min(original_height, max_height)
        new_width = int(new_height * aspect_ratio)

    # Ensure dimensions don't exceed max_size
    if new_width > max_width:
        new_width = max_width
        new_height = int(new_width / aspect_ratio)
    if new_height > max_height:
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Function to make the logo white while preserving transparency
def make_logo_white(logo):
    # Convert logo to RGBA if not already
    logo = logo.convert("RGBA")
    
    # Split into R, G, B, A channels
    r, g, b, a = logo.split()
    
    # Convert to grayscale to get intensity (ignoring color)
    grayscale = logo.convert("L")
    
    # Create a white image of the same size
    white_image = Image.new("RGB", logo.size, (255, 255, 255))
    
    # Convert white image to RGBA
    white_image = white_image.convert("RGBA")
    
    # Split white image into channels
    wr, wg, wb, _ = white_image.split()
    
    # Use the grayscale image as the alpha channel to blend white with transparency
    white_logo = Image.merge("RGBA", (wr, wg, wb, grayscale))
    
    # Combine with the original alpha channel to preserve transparency
    final_r, final_g, final_b, _ = white_logo.split()
    final_logo = Image.merge("RGBA", (final_r, final_g, final_b, a))
    
    return final_logo

# Function to create the news card
def create_photo_card(headline, image_url, pub_date, main_domain, logo_path="logo.png", output_path="photo_card.png"):
    try:
        # Validate BRICK_RED color
        canvas_color = BRICK_RED if BRICK_RED else "#000000"  # Fallback to black if empty

        # Create a blank canvas with error handling
        try:
            canvas = Image.new("RGB", CANVAS_SIZE, canvas_color)
        except ValueError as e:
            raise Exception(f"Invalid canvas color '{canvas_color}': {str(e)}")

        draw = ImageDraw.Draw(canvas)

        # Load fonts
        bangla_font_small, bangla_font_large, regular_font, bold_font = load_fonts()

        # Add the date (top center, no background, white text, bold)
        date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")
        draw.text((DATE_POSITION[0] + 40, DATE_POSITION[1] + 15), date_str, fill="white", font=bold_font)

        # Download, crop, and add the news image
        image_y = DATE_POSITION[1] + DATE_BOX_SIZE[1] + DATE_GAP
        if image_url:
            news_image = download_image(image_url)
            news_image = news_image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            canvas.paste(news_image, IMAGE_POSITION)
        else:
            draw.rectangle((IMAGE_POSITION[0], image_y, 
                           IMAGE_POSITION[0] + IMAGE_SIZE[0], image_y + IMAGE_SIZE[1]), fill="gray")
            draw.text((400, image_y + 300), "No Image Available", fill="white", font=regular_font)

        # Add a mustard yellow border around the image
        draw.rectangle((IMAGE_POSITION[0], image_y, 
                       IMAGE_POSITION[0] + IMAGE_SIZE[0], image_y + IMAGE_SIZE[1]), outline=MUSTARD_YELLOW, width=5)

        # Add the headline (below the image, centered)
        if "not found" in headline.lower():
            headline = "পরিবারে অশান্তি বিশ্ববিদ্যালয়ের পড়াশোনা হত্যার গ্রেপ্তার"
        headline = headline.encode('utf-8').decode('utf-8')
        wrapped_text = textwrap.wrap(headline, width=40)
        headline_y = HEADLINE_Y_START
        if not wrapped_text:
            draw.text((CANVAS_SIZE[0] // 2, headline_y), "Headline Missing", fill="white", font=regular_font, anchor="mm")
        for line in wrapped_text:
            text_bbox = draw.textbbox((0, 0), line, font=bangla_font_large)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (CANVAS_SIZE[0] - text_width) // 2
            draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
            headline_y += HEADLINE_LINE_SPACING

        # Calculate the bottom of the headline and add padding
        num_lines = len(wrapped_text) if wrapped_text else 1
        headline_bottom = HEADLINE_Y_START + (num_lines * HEADLINE_LINE_SPACING)
        divider_y = headline_bottom + HEADLINE_BOTTOM_PADDING

        # Draw the mustard yellow divider between brick_red and navy_blue sections
        draw.rectangle((0, divider_y, CANVAS_SIZE[0], divider_y + DIVIDER_THICKNESS), fill=MUSTARD_YELLOW)

        # Draw the complementary color section (navy_blue) from just below the divider to canvas bottom
        navy_blue_start_y = divider_y + DIVIDER_THICKNESS
        draw.rectangle((0, navy_blue_start_y, CANVAS_SIZE[0], CANVAS_SIZE[1]), fill=NAVY_BLUE)

        # Position the logo and source in the navy_blue section with updated top padding
        logo_source_y = divider_y + LOGO_SOURCE_TOP_PADDING

        # Add the logo (bottom left in navy_blue section) with aspect ratio preserved and make it white
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Make the logo white while preserving transparency
            logo = make_logo_white(logo)
            logo = resize_with_aspect_ratio(logo, LOGO_MAX_SIZE)
            # Center the logo vertically within the max height space
            logo_width, logo_height = logo.size
            logo_y = logo_source_y + (LOGO_MAX_SIZE[1] - logo_height) // 2
            canvas.paste(logo, (PADDING, logo_y), logo)
        except FileNotFoundError:
            draw.text((PADDING, logo_source_y), "Logo Missing", fill="red", font=regular_font)

        # Add the source (bottom right in navy_blue section), adjust x to ensure right padding
        source_text = f"Source: {main_domain}"
        text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
        text_width = text_bbox[2] - text_bbox[0]
        # Right edge should be at x=1020 (1080 - 60 padding)
        text_x = (CANVAS_SIZE[0] - PADDING) - text_width
        source_y = logo_source_y + (LOGO_MAX_SIZE[1] - (text_bbox[3] - text_bbox[1])) // 2  # Align vertically with logo
        draw.text((text_x, source_y), source_text, fill="white", font=regular_font)

        # Save the photo card
        canvas.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to create photo card: {str(e)}")

# Streamlit app
st.title("Automated News Photo Card Generator")

# URL input with validation
url = st.text_input("Enter the news article URL:", placeholder="https://example.com/news-article")
if url and not is_valid_url(url):
    st.error("Please enter a valid URL (e.g., https://example.com).")
    url = None

# Logo upload
uploaded_logo = st.file_uploader("Upload a custom logo (optional, PNG with transparency recommended):", type=["png", "jpg", "jpeg"])
logo_path = "logo.png"
if uploaded_logo:
    logo_path = "custom_logo.png"
    with open(logo_path, "wb") as f:
        f.write(uploaded_logo.getbuffer())
    st.success("Custom logo uploaded successfully!")

# Generate button
if st.button("Generate Photo Card"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        with st.spinner("Generating photo card..."):
            try:
                pub_date, headline, image_url, source, main_domain = extract_news_data(url)
                output_path = create_photo_card(headline, image_url, pub_date, main_domain, logo_path=logo_path)
                st.image(output_path, caption="Generated Photo Card")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png")
            except Exception as e:
                st.error(f"Error: {str(e)}")
