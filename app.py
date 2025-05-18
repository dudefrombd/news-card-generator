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

# Constants
CANVAS_SIZE = (1080, 1080)
BRICK_RED = "#9E2A2F"
IMAGE_SIZE = (1080, 660)
SOURCE_BOX_HEIGHT = 50
SOURCE_BOX_Y = 620
DIVIDER_Y = 670
DIVIDER_THICKNESS = 5
MUSTARD_YELLOW = "#fed500"
HEADLINE_Y_START = 710
PADDING = 20
HEADLINE_WIDTH = 1040
HEADLINE_MAX_HEIGHT = 220
DATE_SOURCE_Y = 930
AD_AREA_Y = 990
AD_AREA_SIZE = (1080, 90)
LOGO_MAX_SIZE = (158, 79)
AD_LOGO_MAX_SIZE = (225, 90)
LOGO_POSITION = (882, 50)

# Validate URL
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
        r'(/[^?\s]*)?$'
    )
    return re.match(regex, url) is not None

# Extract main domain from URL
def extract_main_domain(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        parts = domain.split(".")
        if len(parts) >= 3 and parts[-2] in ["co", "org", "gov", "edu"]:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    except Exception:
        return "Unknown"

# Extract news data
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

# Process image (from URL or uploaded)
def process_image(image_source, is_uploaded=False):
    try:
        if is_uploaded:
            image = Image.open(image_source)
        else:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(image_source, headers=headers, timeout=10)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            image = Image.open(image_data)

        # Crop bottom 15%
        width, height = image.size
        crop_height = int(height * 0.15)
        new_height = height - crop_height
        image = image.crop((0, 0, width, new_height))

        # Resize to fill the image area while preserving aspect ratio
        target_width, target_height = IMAGE_SIZE
        aspect_ratio = width / new_height
        target_aspect = target_width / target_height

        if aspect_ratio > target_aspect:
            new_height = target_height
            new_width = int(new_height * aspect_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - target_width) // 2
            image = image.crop((left, 0, left + target_width, target_height))
        else:
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - target_height) // 2
            image = image.crop((0, top, target_width, top + target_height))

        return image
    except Exception as e:
        raise Exception(f"Failed to process image: {str(e)}")

# Load fonts
def load_fonts(language="Bengali", font_size=48):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bangla_font_small = bangla_font_large = regular_font = None

    if language == "Bengali":
        try:
            font_path_bold = os.path.join(script_dir, "fonts", "NotoSerifBengali-Bold.ttf")
            bangla_font_large = ImageFont.truetype(font_path_bold, font_size)
        except IOError:
            bangla_font_large = ImageFont.load_default()

        try:
            font_path_regular = os.path.join(script_dir, "fonts", "NotoSerifBengali-Regular.ttf")
            bangla_font_small = ImageFont.truetype(font_path_regular, 30)
            regular_font = ImageFont.truetype(font_path_regular, 24)
        except IOError:
            bangla_font_small = regular_font = ImageFont.load_default()
    else:
        try:
            font_path_bold = os.path.join(script_dir, "fonts", "NotoSerifBengali-Bold.ttf")
            bangla_font_large = ImageFont.truetype(font_path_bold, font_size)
        except IOError:
            bangla_font_large = ImageFont.load_default()

        try:
            font_path_regular = os.path.join(script_dir, "fonts", "NotoSerifBengali-Regular.ttf")
            bangla_font_small = ImageFont.truetype(font_path_regular, 24)
            regular_font = ImageFont.truetype(font_path_regular, 24)
        except IOError:
            bangla_font_small = regular_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font

# Adjust headline layout
def adjust_headline(headline, language, draw, max_width, max_height, start_y):
    font_sizes = [72, 68, 64, 60, 56, 52, 48, 44, 40]
    line_spacing_factor = 1.2
    best_font_size = font_sizes[0]
    best_lines = []
    best_spacing = 0

    for size in font_sizes:
        bangla_font_small, bangla_font_large, _ = load_fonts(language, size)
        wrapped_text = textwrap.wrap(headline, width=int(max_width / (size * 0.5)))
        total_height = 0
        lines = []

        for line in wrapped_text:
            bbox = bangla_font_large.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            if line_width > max_width:
                break
            lines.append(line)
            total_height += line_height

        spacing = int(size * line_spacing_factor)
        total_height += (len(lines) - 1) * spacing

        if total_height <= max_height and len(lines) > 0:
            best_font_size = size
            best_lines = lines
            best_spacing = spacing
            break

    bangla_font_small, bangla_font_large, _ = load_fonts(language, best_font_size)
    headline_y = start_y
    for line in best_lines:
        bbox = bangla_font_large.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2
        draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
        headline_y += best_spacing

    return headline_y

# Convert date to Bengali or English format
def convert_to_date(pub_date, language="Bengali"):
    if language == "Bengali":
        bengali_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
        bengali_months = {
            "January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ",
            "April": "এপ্রিল", "May": "মে", "June": "জুন",
            "July": "জুলাই", "August": "আগস্ট", "September": "সেপ্টেম্বর",
            "October": "অক্টোবর", "November": "নভেম্বর", "December": "ডিসেম্বর"
        }
        date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")
        day, month, year = date_str.split()
        return f"{day.translate(bengali_digits)} {bengali_months.get(month, month)} {year.translate(bengali_digits)}"
    else:
        return pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")

# Create the news card
def create_photo_card(headline, image_source, pub_date, main_domain, language="Bengali", output_path="photo_card.png"):
    canvas = Image.new("RGB", CANVAS_SIZE, BRICK_RED)
    draw = ImageDraw.Draw(canvas)
    bangla_font_small, bangla_font_large, regular_font = load_fonts(language)

    # Add news image
    if image_source:
        try:
            news_image = process_image(image_source, is_uploaded=(not isinstance(image_source, str)))
            canvas.paste(news_image, (0, 0))
        except Exception as e:
            draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
            draw.text((400, 300), f"Image Error: {str(e)}", fill="white", font=regular_font)
    else:
        draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
        draw.text((400, 300), "No Image Available", fill="white", font=regular_font)

    # Add top logo
    try:
        logo = Image.open("logo.png").convert("RGBA")
        logo_width, logo_height = logo.size
        aspect = logo_width / logo_height
        if logo_width > logo_height:
            logo_width = min(logo_width, LOGO_MAX_SIZE[0])
            logo_height = int(logo_width / aspect)
        else:
            logo_height = min(logo_height, LOGO_MAX_SIZE[1])
            logo_width = int(logo_height * aspect)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        canvas.paste(logo, LOGO_POSITION, logo)
    except FileNotFoundError:
        draw.text((LOGO_POSITION[0], LOGO_POSITION[1]), "Logo Missing", fill="red", font=regular_font)

    # Source text background
    draw.rectangle((0, SOURCE_BOX_Y, CANVAS_SIZE[0], SOURCE_BOX_Y + SOURCE_BOX_HEIGHT), fill=MUSTARD_YELLOW)
    source_text = f"Source: {main_domain}"
    text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (CANVAS_SIZE[0] - text_width) // 2
    text_y = SOURCE_BOX_Y + (SOURCE_BOX_HEIGHT - text_height) // 2 - 5
    draw.text((text_x, text_y), source_text, fill="black", font=regular_font)

    # Divider
    draw.rectangle((0, DIVIDER_Y, CANVAS_SIZE[0], DIVIDER_Y + DIVIDER_THICKNESS), fill=MUSTARD_YELLOW)

    # Headline
    if "not found" in headline.lower():
        headline = "কোন শিরোনাম পাওয়া যায়নি" if language == "Bengali" else "No Headline Found"
    headline = headline.encode('utf-8').decode('utf-8')
    adjust_headline(headline, language, draw, HEADLINE_WIDTH, HEADLINE_MAX_HEIGHT, HEADLINE_Y_START)

    # Date and comment
    date_str = convert_to_date(pub_date, language)
    draw.text((PADDING, DATE_SOURCE_Y), date_str, fill="white", font=bangla_font_small)

    comment_text = "বিস্তারিত কমেন্টে" if language == "Bengali" else "More in comments"
    text_bbox = draw.textbbox((0, 0), comment_text, font=bangla_font_small)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = CANVAS_SIZE[0] - PADDING - text_width
    draw.text((text_x, DATE_SOURCE_Y), comment_text, fill="white", font=bangla_font_small)

    # Ad area
    try:
        ad_image = Image.open("cp-ad.png")
        ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
        canvas.paste(ad_image, (0, AD_AREA_Y))
    except FileNotFoundError:
        draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
        draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 45), "Default Ad Image Missing", fill="white", font=regular_font, anchor="mm")

    canvas.save(output_path)
    return output_path

# Streamlit app
st.title("Automated News Photo Card Generator")

# Initialize session state
if 'headline_key' not in st.session_state:
    st.session_state.headline_key = 0
if 'language' not in st.session_state:
    st.session_state.language = "Bengali"

# 1. URL input
url = st.text_input("Enter the news article URL:", placeholder="https://example.com/news-article")
if url and not is_valid_url(url):
    st.error("Please enter a valid URL (e.g., https://example.com).")
    url = None

# 2. Headline input
placeholder_text = "কোন শিরোনাম পাওয়া যায়নি" if st.session_state.language == "Bengali" else "No Headline Found"
custom_headline = st.text_input(
    f"Enter a custom headline (optional, in {st.session_state.language}):",
    placeholder=placeholder_text,
    key=f"headline_input_{st.session_state.headline_key}"
)

# 3. Custom image upload
uploaded_image = st.file_uploader("Upload a custom image (optional, overrides image from URL):", type=["png", "jpg", "jpeg"])
image_source = None
if uploaded_image:
    image_source = uploaded_image
    st.success("Custom image uploaded!")

# 4. Language selection
st.markdown("**Select Language**")
col1, col2 = st.columns(2)
with col1:
    if st.button("Bengali"):
        st.session_state.language = "Bengali"
        st.session_state.headline_key += 1
with col2:
    if st.button("English"):
        st.session_state.language = "English"
        st.session_state.headline_key += 1

# Generate button
if st.button("Generate Photo Card"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        with st.spinner("Generating photo card..."):
            try:
                pub_date, headline, image_url, source, main_domain = extract_news_data(url)
                final_headline = custom_headline if custom_headline else headline
                # Use uploaded image if provided, otherwise use image_url
                if not image_source and image_url:
                    image_source = image_url
                output_path = create_photo_card(final_headline, image_source, pub_date, main_domain, language=st.session_state.language)
                st.image(output_path, caption=f"Generated Photo Card ({st.session_state.language})")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png")
            except Exception as e:
                st.error(f"Error: {str(e)}")
