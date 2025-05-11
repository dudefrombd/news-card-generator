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
IMAGE_SIZE = (1080, 660)  # Image area from top
SOURCE_BOX_HEIGHT = 50
SOURCE_BOX_Y = 620  # Position of source text background box
DIVIDER_Y = 670  # 620 + 50 (source box height)
DIVIDER_THICKNESS = 5  # Thickness of the divider
MUSTARD_YELLOW = "#fed500"  # Divider color
HEADLINE_Y_START = 710  # 670 (divider) + 40 (top padding)
HEADLINE_WIDTH = 980  # 1080 - 50 (left padding) - 50 (right padding)
HEADLINE_MAX_HEIGHT = 220  # Max height from 710 to 930
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
def load_fonts(language="Bengali", font_size=48):
    bangla_font_small = bangla_font_large = regular_font = None
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if language == "Bengali":
        # Load Bangla font for headline
        try:
            font_path_bold = os.path.join(script_dir, "fonts", "NotoSerifBengali-Bold.ttf")
            bangla_font_large = ImageFont.truetype(font_path_bold, font_size)
            print(f"Bold font loaded from: {font_path_bold}")
            bbox = bangla_font_large.getbbox('ক')
            text_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            print(f"Font size for bangla_font_large: {text_size}")
        except IOError as e:
            print(f"Failed to load bold font: {e}")
            bangla_font_large = ImageFont.load_default()

        # Load Bangla font for date and comment text
        try:
            font_path_regular = os.path.join(script_dir, "fonts", "NotoSerifBengali-Regular.ttf")
            bangla_font_small = ImageFont.truetype(font_path_regular, 30)
            print(f"Regular font loaded from: {font_path_regular}")
        except IOError as e:
            print(f"Failed to load regular font: {e}")
            bangla_font_small = ImageFont.load_default()

        # Load regular font for source text
        try:
            regular_font = ImageFont.truetype(font_path_regular, 24)
            print(f"Regular font loaded for source from: {font_path_regular}")
        except IOError as e:
            print(f"Failed to load regular font: {e}")
            regular_font = ImageFont.load_default()
    else:
        # Load English font for headline using NotoSerifBengali-Bold.ttf
        try:
            font_path_bold = os.path.join(script_dir, "fonts", "NotoSerifBengali-Bold.ttf")
            bangla_font_large = ImageFont.truetype(font_path_bold, font_size)
            print(f"English headline font loaded from: {font_path_bold}")
            bbox = bangla_font_large.getbbox('A')
            text_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            print(f"Font size for bangla_font_large: {text_size}")
        except IOError as e:
            print(f"Failed to load English headline font: {e}")
            bangla_font_large = ImageFont.load_default()

        # Load English font for date and comment text using NotoSerifBengali-Regular.ttf
        try:
            font_path_regular = os.path.join(script_dir, "fonts", "NotoSerifBengali-Regular.ttf")
            bangla_font_small = ImageFont.truetype(font_path_regular, 24)  # Changed from 30 to 24
            print(f"English regular font loaded from: {font_path_regular}")
        except IOError as e:
            print(f"Failed to load English regular font: {e}")
            bangla_font_small = ImageFont.load_default()

        # Load regular font for source text using NotoSerifBengali-Regular.ttf
        try:
            regular_font = ImageFont.truetype(font_path_regular, 24)
            print(f"English source font loaded from: {font_path_regular}")
        except IOError as e:
            print(f"Failed to load English source font: {e}")
            regular_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font

# Function to adjust headline layout
def adjust_headline(headline, language, draw, max_width, max_height, start_y):
    font_sizes = [48, 44, 40, 36, 32]  # Possible font sizes to try
    line_spacing_factor = 1.2  # Line spacing at 120% of font size
    best_font_size = font_sizes[0]
    best_lines = []
    best_spacing = 0

    for size in font_sizes:
        bangla_font_small, bangla_font_large, _ = load_fonts(language, size)
        wrapped_text = textwrap.wrap(headline, width=int(max_width / (size * 0.5)))  # Approx char width
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

    # Use the best configuration
    bangla_font_small, bangla_font_large, _ = load_fonts(language, best_font_size)
    headline_y = start_y
    for line in best_lines:
        bbox = bangla_font_large.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2
        draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
        headline_y += best_spacing

    return headline_y

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

# Function to convert date to Bengali or English format
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
        day_bengali = day.translate(bengali_digits)
        year_bengali = year.translate(bengali_digits)
        month_bengali = bengali_months.get(month, month)
        return f"{day_bengali} {month_bengali} {year_bengali}"
    else:
        # English format
        return pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")

# Function to create the news card
def create_photo_card(headline, image_url, pub_date, main_domain, language="Bengali", logo_path="logo.png", ad_path=None, output_path="photo_card.png"):
    try:
        canvas_color = BRICK_RED if BRICK_RED else "#000000"
        canvas = Image.new("RGB", CANVAS_SIZE, canvas_color)
        draw = ImageDraw.Draw(canvas)

        # Load fonts based on language
        bangla_font_small, bangla_font_large, regular_font = load_fonts(language)

        # Add the news image (top, full width, 660 px height)
        if image_url:
            news_image = download_image(image_url)
            news_image = news_image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            canvas.paste(news_image, (0, 0))
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

        # Add the headline with dynamic adjustment
        if "not found" in headline.lower():
            headline = "কোন শিরোনাম পাওয়া যায়নি" if language == "Bengali" else "No Headline Found"
        headline = headline.encode('utf-8').decode('utf-8')
        adjust_headline(headline, language, draw, HEADLINE_WIDTH, HEADLINE_MAX_HEIGHT, HEADLINE_Y_START)

        # Add the date and source area at y=930 (date in appropriate format, updated padding)
        date_str = convert_to_date(pub_date, language)
        draw.text((PADDING, DATE_SOURCE_Y), date_str, fill="white", font=bangla_font_small)

        comment_text = "বিস্তারিত কমেন্টে" if language == "Bengali" else "More in comments"
        text_bbox = draw.textbbox((0, 0), comment_text, font=bangla_font_small)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = CANVAS_SIZE[0] - PADDING - text_width  # Right-aligned with 50 px padding
        draw.text((text_x, DATE_SOURCE_Y), comment_text, fill="white", font=bangla_font_small)

        # Add the ad area at y=990
        if ad_path:
            try:
                ad_image = Image.open(ad_path)
                ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
                canvas.paste(ad_image, (0, AD_AREA_Y))
            except FileNotFoundError:
                draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
                draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 45), "Ad Image Missing", fill="white", font=regular_font, anchor="mm")
        else:
            draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill=MUSTARD_YELLOW)
            # Add second logo in the middle of ad area
            try:
                second_logo = Image.open(logo_path).convert("RGBA")
                second_logo = resize_with_aspect_ratio(second_logo, AD_AREA_SIZE)
                second_logo_width, second_logo_height = second_logo.size
                second_logo_x = (CANVAS_SIZE[0] - second_logo_width) // 2  # Center horizontally
                second_logo_y = AD_AREA_Y + (AD_AREA_SIZE[1] - second_logo_height) // 2  # Center vertically in ad area
                canvas.paste(second_logo, (second_logo_x, second_logo_y), second_logo)
            except FileNotFoundError:
                pass  # No action if second logo fails to load, just keep the mustard yellow background

        # Save the photo card
        canvas.save(output_path)
        return output_path
    except Exception as e:
        raise Exception(f"Failed to create photo card: {str(e)}")

# Streamlit app
st.title("Automated News Photo Card Generator")

# Initialize session state for URL tracking and language selection
if 'previous_url' not in st.session_state:
    st.session_state.previous_url = ""
if 'headline_key' not in st.session_state:
    st.session_state.headline_key = 0
if 'language' not in st.session_state:
    st.session_state.language = "Bengali"

# Language selection with card-like buttons
st.markdown("**Select Language**")
col1, col2 = st.columns(2)

with col1:
    if st.button("Bengali", key="bengali_btn", help="Generate card in Bengali"):
        st.session_state.language = "Bengali"
        st.session_state.headline_key += 1  # Reset headline input

with col2:
    if st.button("English", key="english_btn", help="Generate card in English"):
        st.session_state.language = "English"
        st.session_state.headline_key += 1  # Reset headline input

# URL input with validation
url = st.text_input("Enter the news article URL:", placeholder="https://example.com/news-article")
if url and not is_valid_url(url):
    st.error("Please enter a valid URL (e.g., https://example.com).")
    url = None

# Reset custom headline if URL or language changes
if url != st.session_state.previous_url and url is not None:
    st.session_state.headline_key += 1  # Increment key to reset the text input
    st.session_state.previous_url = url

# Headline input (editable, reset on URL or language change)
placeholder_text = "কোন শিরোনাম পাওয়া যায়নি" if st.session_state.language == "Bengali" else "No Headline Found"
custom_headline = st.text_input(
    f"Enter a custom headline (optional, in {st.session_state.language}):",
    placeholder=placeholder_text,
    key=f"headline_input_{st.session_state.headline_key}"
)

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
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        with st.spinner("Generating photo card..."):
            try:
                pub_date, headline, image_url, source, main_domain = extract_news_data(url)
                # Use custom headline if provided, otherwise use extracted or default
                final_headline = custom_headline if custom_headline else headline
                output_path = create_photo_card(final_headline, image_url, pub_date, main_domain, language=st.session_state.language, logo_path=logo_path, ad_path=ad_path)
                st.image(output_path, caption=f"Generated Photo Card ({st.session_state.language})")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png")
            except Exception as e:
                st.error(f"Error: {str(e)}")
