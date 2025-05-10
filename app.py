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
BRICK_RED = "#9E2A2F"  # Background color
IMAGE_SIZE = (1080, 660)  # Default image area from top
SOURCE_BOX_HEIGHT = 50
SOURCE_BOX_Y = 620  # Position of source text background box
DIVIDER_Y = 670  # 620 + 50 (source box height)
DIVIDER_THICKNESS = 5  # Thickness of the divider
MUSTARD_YELLOW = "#FFB300"  # Divider color
HEADLINE_Y_START = 710  # 670 (divider) + 40 (top padding)
HEADLINE_WIDTH = 980  # 1080 - 50 (left padding) - 50 (right padding)
HEADLINE_LINE_SPACING = 60
DATE_SOURCE_Y = 930  # Date and source text position
PADDING = 50  # Padding for left, right, and top
BOTTOM_PADDING = 20  # Bottom padding for date/source area
AD_AREA_Y = 990  # Ad area position
AD_AREA_SIZE = (1080, 90)  # Ad area dimensions
LOGO_MAX_SIZE = (225, 113)  # Max size of logo
LOGO_POSITION = (1080 - 40 - 225, 50)  # 40 px from right, 50 px from top

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
        if domain.startswith("www."):
            domain = domain[4:]
        parts = domain.split(".")
        if len(parts) >= 3:
            common_suffixes = ["co", "org", "gov", "edu"]
            if parts[-2] in common_suffixes:
                return ".".join(parts[-3:])
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

        date_tag = soup.find('meta', {'property': 'article:published_time'})
        date_str = date_tag['content'] if date_tag else None
        pub_date = None
        if date_str:
            try:
                pub_date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                pub_date = None

        headline_tag = soup.find('meta', {'property': 'og:title'})
        headline = headline_tag['content'] if headline_tag else 'Headline not found'

        image_tag = soup.find('meta', {'property': 'og:image'})
        image_url = image_tag['content'] if image_tag else None

        source_tag = soup.find('meta', {'property': 'og:site_name'})
        source = source_tag['content'] if source_tag else 'Source not found'

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
    bangla_font_small = bangla_font_large = regular_font = None

    # Load Bangla font for headline (NotoSerifBengali-Bold.ttf, reduced size)
    try:
        bangla_font_large = ImageFont.truetype("NotoSerifBengali-Bold.ttf", 45)
    except IOError:
        bangla_font_large = ImageFont.load_default()

    # Load Bangla font for date and comment text (NotoSerifBengali-Regular.ttf)
    try:
        bangla_font_small = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 30)
    except IOError:
        bangla_font_small = ImageFont.load_default()

    # Load regular font for source text (NotoSerifBengali-Regular.ttf)
    try:
        regular_font = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 24)
    except IOError:
        regular_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font

# Function to resize image while preserving aspect ratio
def resize_with_aspect_ratio(image, max_size):
    original_width, original_height = image.size
    max_width, max_height = max_size
    aspect_ratio = original_width / original_height

    if original_width > original_height:
        new_width = min(original_width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(original_height, max_height)
        new_width = int(new_height * aspect_ratio)

    if new_width > max_width:
        new_width = max_width
        new_height = int(new_width / aspect_ratio)
    if new_height > max_height:
        new_height = max_height
        new_width = int(new_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

# Function to convert date to Bengali
def convert_to_bengali_date(pub_date):
    bengali_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
    bengali_months = {
        "January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ",
        "April": "এপ্রিল", "May": "মে", "June": "জুন",
        "July": "জুলাই", "August": "আগস্ট", "September": "সেপ্টেম্বর",
        "October": "অক্টোবর", "November": "নভেম্বর", "December": "ডিসেম্বর"
    }
    date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")
    day, month, year = date_str.split()
    day_bengali = day.translate(bengali_digits)
    year_bengali = year.translate(bengali_digits)
    month_bengali = bengali_months.get(month, month)
    return f"{day_bengali} {month_bengali} {year_bengali}"

# Function to create the news card
def create_photo_card(headline, image, pub_date, main_domain, logo_path="logo.png", ad_path=None, output_path="photo_card.png"):
    try:
        canvas_color = BRICK_RED if BRICK_RED else "#000000"
        canvas = Image.new("RGB", CANVAS_SIZE, canvas_color)
        draw = ImageDraw.Draw(canvas)

        # Load fonts
        bangla_font_small, bangla_font_large, regular_font = load_fonts()

        # Add the news image (top, full width, 660 px height)
        if image:
            # Resize the image based on its original dimensions, respecting max size
            resized_image = resize_with_aspect_ratio(image, (image.width, image.height))
            # If user-provided dimensions exceed canvas, cap at canvas size
            if resized_image.width > IMAGE_SIZE[0] or resized_image.height > IMAGE_SIZE[1]:
                resized_image = resize_with_aspect_ratio(image, IMAGE_SIZE)
            canvas.paste(resized_image, (0, 0))
        else:
            draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
            draw.text((400, 300), "No Image Available", fill="white", font=regular_font)

        # Add the logo (50 px from top, 40 px from right)
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = resize_with_aspect_ratio(logo, LOGO_MAX_SIZE)
            logo_width, logo_height = logo.size
            canvas.paste(logo, LOGO_POSITION, logo)
        except FileNotFoundError:
            draw.text((LOGO_POSITION[0], LOGO_POSITION[1]), "Logo Missing", fill="red", font=regular_font)

        # Draw the source text background box (white background)
        draw.rectangle((0, SOURCE_BOX_Y, CANVAS_SIZE[0], SOURCE_BOX_Y + SOURCE_BOX_HEIGHT), 
                      fill="white")

        # Add the source text on top of the box (black text, slightly upper)
        source_text = f"Source: {main_domain}"
        text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (CANVAS_SIZE[0] - text_width) // 2  # Center the source text
        text_y = SOURCE_BOX_Y + (SOURCE_BOX_HEIGHT - text_height) // 2 - 5  # Shift 5 px above center
        draw.text((text_x, text_y), source_text, fill="black", font=regular_font)

        # Draw the mustard yellow divider
        draw.rectangle((0, DIVIDER_Y, CANVAS_SIZE[0], DIVIDER_Y + DIVIDER_THICKNESS), 
                      fill=MUSTARD_YELLOW)

        # Add the headline (below the divider, with padding)
        if "not found" in headline.lower():
            headline = "কোন শিরোনাম পাওয়া যায়নি"
        headline = headline.encode('utf-8').decode('utf-8')
        wrapped_text = textwrap.wrap(headline, width=40)
        headline_y = HEADLINE_Y_START
        if not wrapped_text:
            draw.text((CANVAS_SIZE[0] // 2, headline_y), "Headline Missing", fill="white", font=regular_font, anchor="mm")
        for line in wrapped_text:
            text_bbox = draw.textbbox((0, 0), line, font=bangla_font_large)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2  # Center within padded area
            draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
            headline_y += HEADLINE_LINE_SPACING

        # Add the date and source area at y=930 (date in Bengali)
        date_str = convert_to_bengali_date(pub_date)
        draw.text((PADDING, DATE_SOURCE_Y), date_str, fill="white", font=bangla_font_small)

        comment_text = "বিস্তারিত কমেন্টে"
        text_bbox = draw.textbbox((0, 0), comment_text, font=bangla_font_small)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = CANVAS_SIZE[0] - PADDING - text_width  # Right-aligned
        draw.text((text_x, DATE_SOURCE_Y), comment_text, fill="white", font=bangla_font_small)

        # Add the ad area at y=990 (black background, white text, centered)
        if ad_path:
            try:
                ad_image = Image.open(ad_path)
                ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
                canvas.paste(ad_image, (0, AD_AREA_Y))
            except FileNotFoundError:
                draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
                draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 45), "Ad Image Missing", fill="white", font=regular_font, anchor="mm")
        else:
            draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
            draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 45), "Ad Placeholder", fill="white", font=regular_font, anchor="mm")

        # Save the photo card
        canvas.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to create photo card: {str(e)}")

# Streamlit app
st.title("Automated News Photo Card Generator")

# Initialize session state for URL tracking
if 'previous_url' not in st.session_state:
    st.session_state.previous_url = ""
if 'headline_key' not in st.session_state:
    st.session_state.headline_key = 0

# URL input with validation
url = st.text_input("Enter the news article URL:", placeholder="https://example.com/news-article")
if url and not is_valid_url(url):
    st.error("Please enter a valid URL (e.g., https://example.com).")
    url = None

# Reset custom headline if URL changes
if url != st.session_state.previous_url and url is not None:
    st.session_state.headline_key += 1  # Increment key to reset the text input
    st.session_state.previous_url = url

# Headline input (editable, reset on URL change)
custom_headline = st.text_input(
    "Enter a custom headline (optional, in Bengali):",
    placeholder="কোন শিরোনাম পাওয়া যায়নি",
    key=f"headline_input_{st.session_state.headline_key}"
)

# Image upload and resize
uploaded_image = st.file_uploader("Upload a custom image (optional):", type=["png", "jpg", "jpeg"])
custom_width = st.number_input("Image width (optional, max 1080):", min_value=1, max_value=1080, value=1080, step=10)
custom_height = st.number_input("Image height (optional, max 660):", min_value=1, max_value=660, value=660, step=10)
image = None
if uploaded_image:
    image = Image.open(uploaded_image)
    # Cap dimensions to canvas size if exceeded
    if custom_width > 1080 or custom_height > 660:
        custom_width = min(custom_width, 1080)
        custom_height = min(custom_height, 660)
    image = resize_with_aspect_ratio(image, (custom_width, custom_height))

# Logo upload
uploaded_logo = st.file_uploader("Upload a custom logo (optional, PNG with transparency recommended):", type=["png", "jpg", "jpeg"])
logo_path = "logo.png"
if uploaded_logo:
    logo_path = "custom_logo.png"
    with open(logo_path, "wb") as f:
        f.write(uploaded_logo.getbuffer())
    st.success("Custom logo uploaded successfully!")

# Ad image upload
uploaded_ad = st.file_uploader("Upload an ad image (optional):", type=["png", "jpg", "jpeg"])
ad_path = None
if uploaded_ad:
    ad_path = "custom_ad.png"
    with open(ad_path, "wb") as f:
        f.write(uploaded_ad.getbuffer())
    st.success("Ad image uploaded successfully!")

# Generate button
if st.button("Generate Photo Card"):
    if not url and not uploaded_image:
        st.warning("Please enter a valid URL or upload an image.")
    else:
        with st.spinner("Generating photo card..."):
            try:
                pub_date, headline, image_url, source, main_domain = extract_news_data(url) if url else (None, None, None, None, None)
                if not image and url:
                    image = download_image(image_url) if image_url else None
                final_headline = custom_headline if custom_headline else headline
                output_path = create_photo_card(final_headline, image, pub_date, main_domain, logo_path=logo_path, ad_path=ad_path)
                st.image(output_path, caption="Generated Photo Card")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png")
            except Exception as e:
                st.error(f"Error: {str(e)}")
