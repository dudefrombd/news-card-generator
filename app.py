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
import base64
import time

# Constants
CANVAS_SIZE = (1080, 1200)
IMAGE_SIZE = (1080, 700)
LOGO_BOX_HEIGHT = 120
LOGO_BOX_Y = 580
PADDING = 20
HEADLINE_WIDTH = 1040
HEADLINE_MAX_HEIGHT = 220  # 830px to 1050px
DATE_SOURCE_Y = 1050
AD_AREA_Y = 1100
AD_AREA_SIZE = (1080, 100)
LOGO_MAX_SIZE = (142, 71)  # Scaled down 10% from original (158, 79)
AD_LOGO_MAX_SIZE = (225, 90)
MAP_OPACITY = 0.3
SOURCE_BOX_OPACITY = 0.7
MAP_BOX_WIDTH = 1080
MAP_BOX_HEIGHT = 400
MAP_BOX_X = 0
MAP_BOX_Y = 700
DIVIDER_Y = 780  # 10px below comment_text at y=720
DIVIDER_THICKNESS = 2

# Primary, secondary, and text default colors
PRIMARY_DEFAULT_COLOR = "#9E2A2F"
SECONDARY_DEFAULT_COLOR = "#fed500"
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_SECONDARY_TEXT_COLOR = SECONDARY_DEFAULT_COLOR

# Initialize session state for colors
if 'primary_color' not in st.session_state:
    st.session_state.primary_color = PRIMARY_DEFAULT_COLOR
if 'secondary_color' not in st.session_state:
    st.session_state.secondary_color = SECONDARY_DEFAULT_COLOR
if 'text_color' not in st.session_state:
    st.session_state.text_color = DEFAULT_TEXT_COLOR
if 'secondary_text_color' not in st.session_state:
    st.session_state.secondary_text_color = DEFAULT_SECONDARY_TEXT_COLOR

# Use session state colors
PRIMARY_COLOR = st.session_state.primary_color
SECONDARY_COLOR = st.session_state.secondary_color
TEXT_COLOR = st.session_state.text_color
SECONDARY_TEXT_COLOR = st.session_state.secondary_text_color

# Custom CSS for progress bar and Reset button
st.markdown(
    f"""
    <style>
    /* Style the progress bar */
    .stProgress > div > div > div > div {{
        background-color: {PRIMARY_COLOR};
    }}
    /* Style the Reset button */
    div.stButton > button[kind="primary"][key="reset_button_{st.session_state.get('generate_key', 0)}"] {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
    }}
    div.stButton > button[kind="primary"][key="reset_button_{st.session_state.get('generate_key', 0)}"]:hover {{
        background-color: #7A2326; /* Slightly darker shade for hover */
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Validate URL (Handles query parameters)
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)'  # Scheme
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # Domain
        r'(/[^?\s]*)?'  # Path (optional)
        r'(\?[^#\s]*)?'  # Query parameters (optional)
        r'(\#.*)?$'  # Fragment (optional)
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

        # Extract publication date
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

        # Extract source name
        source_tag = soup.find('meta', {'property': 'og:site_name'})
        source = source_tag['content'] if source_tag else 'Source not found'

        main_domain = extract_main_domain(url)
        return pub_date, headline, image_url, source, main_domain
    except Exception as e:
        raise Exception(f"Failed to extract news data: {str(e)}")

# Convert URL to base64
def url_to_base64(image_url, max_retries=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.ittefaq.com.bd'
    }
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to fetch {image_url}")
            response = requests.get(image_url, headers=headers, timeout=15, allow_redirects=True)
            print(f"Response status code: {response.status_code}")
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            if not content_type.startswith('image/'):
                raise Exception("The URL does not point to a valid image file.")
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            print("Image fetched and converted to base64 successfully.")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1 and (e.response is None or e.response.status_code in [429, 503]):
                print(f"Retryable error: {str(e)}. Retrying...")
                continue
            print(f"Failed request details: {str(e)}, Status: {getattr(e.response, 'status_code', 'N/A')}, Text: {getattr(e.response, 'text', 'N/A')}")
            raise Exception(f"Failed to fetch image from URL: {str(e)}. The server may be blocking the request, or the URL may not be publicly accessible.")
    raise Exception("Failed to fetch image after maximum retries. The server may be unavailable or blocking the request.")

# Process image (from URL, uploaded, or base64)
def process_image(image_source, is_uploaded=False, is_base64=False):
    try:
        if is_uploaded:
            image = Image.open(image_source)
        elif is_base64:
            # Remove the base64 prefix if present (e.g., "data:image/png;base64,")
            if "," in image_source:
                image_source = image_source.split(",")[1]
            image_data = base64.b64decode(image_source)
            image = Image.open(BytesIO(image_data))
        else:
            # Assume it's a URL and convert to base64 first
            image_source = url_to_base64(image_source)
            if "," in image_source:
                image_source = image_source.split(",")[1]
            image_data = base64.b64decode(image_source)
            image = Image.open(BytesIO(image_data))

        # Resize to fill the image area while preserving aspect ratio
        width, height = image.size
        target_width, target_height = IMAGE_SIZE
        aspect_ratio = width / height
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

# Process the world map for overlay
def process_world_map(map_path):
    try:
        map_image = Image.open(map_path).convert("RGBA")
        width, height = map_image.size  # 1080x512

        # Calculate aspect ratio
        aspect_ratio = width / height  # 1080/512 ≈ 2.11
        target_width, target_height = MAP_BOX_WIDTH, MAP_BOX_HEIGHT  # 1080x400
        target_aspect = target_width / target_height  # 1080/400 = 2.7

        # Scale the map to fit the box width, preserving aspect ratio
        new_width = target_width  # 1080px
        new_height = int(new_width / aspect_ratio)  # 1080 * 512 / 1080 = 512px
        map_image = map_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop to fit the target height (400px), centering vertically
        if new_height > target_height:
            top = (new_height - target_height) // 2
            map_image = map_image.crop((0, top, target_width, top + target_height))
        else:
            # If the height is less than 400px, center the map
            new_map = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
            y_offset = (target_height - new_height) // 2
            new_map.paste(map_image, (0, y_offset))
            map_image = new_map

        # Adjust opacity (30% transparency)
        map_data = map_image.getdata()
        new_data = []
        for item in map_data:
            new_data.append((item[0], item[1], item[2], int(item[3] * MAP_OPACITY)))
        map_image.putdata(new_data)

        return map_image
    except Exception as e:
        raise Exception(f"Failed to process world map: {str(e)}")

# Process the logo box background
def process_logo_box_bg(bg_path):
    try:
        bg_image = Image.open(bg_path).convert("RGBA")
        target_width, target_height = CANVAS_SIZE[0], LOGO_BOX_HEIGHT  # 1080x120

        # Resize to match logo box dimensions
        bg_image = bg_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Adjust opacity (70% transparency)
        bg_data = bg_image.getdata()
        new_data = []
        for item in bg_data:
            new_data.append((item[0], item[1], item[2], int(item[3] * SOURCE_BOX_OPACITY)))
        bg_image.putdata(new_data)

        return bg_image
    except Exception as e:
        raise Exception(f"Failed to process logo box background: {str(e)}")

# Load fonts with simplified logic and fallback
def load_fonts(language="Bengali", font_size=48):
    bangla_font_small = bangla_font_large = regular_font = None

    # Attempt to load Noto Serif Bengali Bold
    try:
        bangla_font_large = ImageFont.truetype("NotoSerifBengali-Bold.ttf", font_size)
        print(f"Successfully loaded NotoSerifBengali-Bold.ttf for size {font_size}")
    except Exception as e:
        print(f"Failed to load NotoSerifBengali-Bold.ttf: {str(e)}")
        try:
            # Fallback to a system font that supports Unicode
            bangla_font_large = ImageFont.truetype("Arial Unicode MS.ttf", font_size)
            print(f"Fallback: Successfully loaded Arial Unicode MS.ttf for size {font_size}")
        except Exception as e2:
            print(f"Fallback failed: {str(e2)}. Using default font.")
            bangla_font_large = ImageFont.load_default()

    # Load regular font for other text
    try:
        bangla_font_small = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 26)
        regular_font = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 24)
        print("Successfully loaded NotoSerifBengali-Regular.ttf")
    except Exception as e:
        print(f"Failed to load NotoSerifBengali-Regular.ttf: {str(e)}")
        try:
            bangla_font_small = ImageFont.truetype("Arial Unicode MS.ttf", 26)
            regular_font = ImageFont.truetype("Arial Unicode MS.ttf", 24)
            print("Fallback: Successfully loaded Arial Unicode MS.ttf for regular font")
        except Exception as e2:
            print(f"Fallback failed: {str(e2)}. Using default font.")
            bangla_font_small = regular_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font

# Adjust headline layout with improved wrapping and debugging
def adjust_headline(headline, language, draw, max_width, max_height):
    font_sizes = [72, 68, 64, 60, 56, 52, 48]
    best_font_size = font_sizes[0]
    best_headline_lines = []
    best_spacing = 0
    headline_y_start = 830

    print(f"Processing headline: {headline}")

    for size in font_sizes:
        bangla_font_small, bangla_font_large, _ = load_fonts(language, size)
        # Adjust wrapping width to be stricter
        wrap_width = int(max_width / (size * 0.5))  # Using 0.5 divisor
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        print(f"Wrapped headline into {len(headline_wrapped)} lines with wrap_width={wrap_width}")
        total_height = 0
        headline_lines = []

        if not headline_wrapped:
            print("Warning: Headline wrapping produced no lines. Using original headline.")
            headline_wrapped = [headline]

        for line in headline_wrapped:
            bbox = bangla_font_large.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            print(f"Line '{line}' width: {line_width}, max allowed: {max_width}")
            if line_width > max_width:
                print(f"Line '{line}' exceeds max width {max_width} at font size {size}. Skipping this size.")
                headline_lines = []  # Reset to force a smaller font size
                break
            headline_lines.append(line)
            total_height += line_height

        spacing = int(size * 1.2)
        total_height += (len(headline_lines) - 1) * spacing

        print(f"Font size {size}: {len(headline_lines)} lines, total height {total_height}")

        if total_height <= max_height and len(headline_lines) > 0:
            best_font_size = size
            best_headline_lines = headline_lines
            best_spacing = spacing
            break

    # Fallback if no suitable font size is found
    if not best_headline_lines:
        print("No suitable font size found. Forcing headline to fit with smallest font size.")
        bangla_font_small, bangla_font_large, _ = load_fonts(language, font_sizes[-1])
        wrap_width = int(max_width / (font_sizes[-1] * 0.5))
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        best_headline_lines = []
        for line in headline_wrapped[:3]:  # Limit to 3 lines max
            bbox = bangla_font_large.getbbox(line)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width:
                best_headline_lines.append(line)
        if not best_headline_lines:
            best_headline_lines = [headline[:int(max_width / 10)].strip()]  # Fallback to a short portion
        best_spacing = int(font_sizes[-1] * 1.2)
        best_font_size = font_sizes[-1]
        print(f"Forced rendering with font size {best_font_size}, {len(best_headline_lines)} lines")

    bangla_font_small, bangla_font_large, _ = load_fonts(language, best_font_size)
    headline_y = headline_y_start

    print(f"Rendering headline with font size {best_font_size}, lines: {best_headline_lines}")

    for line in best_headline_lines:
        try:
            bbox = bangla_font_large.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2
            draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
            print(f"Successfully rendered line '{line}' at y={headline_y}, width={text_width}")
            headline_y += best_spacing
        except Exception as e:
            print(f"Failed to render line '{line}': {str(e)}")
            # Fallback: Render with default font in English
            fallback_font = ImageFont.load_default()
            draw.text((text_x, headline_y), "Headline Rendering Failed", fill="red", font=fallback_font)
            headline_y += best_spacing

    print(f"Headline rendered, final y-position: {headline_y}")

    return headline_y

# Convert date to Bengali or English format (only date, no time)
def convert_to_date(pub_date, language="Bengali"):
    if language == "Bengali":
        bengali_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
        bengali_months = {
            "January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ",
            "April": "এপ্রিল", "May": "মে", "June": "জুন",
            "July": "জুলাই", "August": "আগস্ট", "September": "সেপ্টেম্বর",
            "October": "অক্টোবর", "November": "নভেম্বর", "December": "ডিসেম্বর"
        }
        date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.date.today().strftime("%d %B %Y")
        day, month, year = date_str.split()
        return f"{day.translate(bengali_digits)} {bengali_months.get(month, month)} {year.translate(bengali_digits)}"
    else:
        return pub_date.strftime("%d %B %Y") if pub_date else datetime.date.today().strftime("%d %B %Y")

# Create the news card
def create_photo_card(headline, image_source, pub_date, main_domain, language="Bengali", output_path="photo_card.png"):
    canvas = Image.new("RGB", CANVAS_SIZE, PRIMARY_COLOR)
    draw = ImageDraw.Draw(canvas)
    bangla_font_small, bangla_font_large, regular_font = load_fonts(language)

    # Add map overlay
    try:
        world_map = process_world_map("world-map.png")
        canvas = Image.new("RGBA", CANVAS_SIZE, PRIMARY_COLOR)
        canvas.paste(world_map, (MAP_BOX_X, MAP_BOX_Y), world_map)
        canvas = canvas.convert("RGB")
        draw = ImageDraw.Draw(canvas)
    except Exception as e:
        print(f"Warning: Could not load world map: {str(e)}")

    # Add news image
    if image_source:
        try:
            news_image = process_image(image_source, is_uploaded=(not isinstance(image_source, str)), is_base64=(isinstance(image_source, str) and (image_source.startswith("data:image") or re.match(r'^[A-Za-z0-9+/=]+$', image_source))))
            canvas.paste(news_image, (0, 0))
        except Exception as e:
            draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
            draw.text((400, 300), f"Image Error: {str(e)}", fill="white", font=regular_font)
    else:
        draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
        draw.text((400, 300), "No Image Available", fill="white", font=regular_font)

    # Logo box background with semi-transparent color and overlay
    secondary_rgba = tuple(int(SECONDARY_COLOR[i:i+2], 16) for i in (1, 3, 5)) + (int(255 * SOURCE_BOX_OPACITY),)
    draw.rectangle((0, LOGO_BOX_Y, CANVAS_SIZE[0], LOGO_BOX_Y + LOGO_BOX_HEIGHT), fill=secondary_rgba)
    try:
        logo_box_bg = process_logo_box_bg("logo-box-bg.png")
        canvas.paste(logo_box_bg, (0, LOGO_BOX_Y), logo_box_bg)
    except Exception as e:
        print(f"Warning: Could not load logo box background: {str(e)}")

    # Add top logo (drawn after the logo box to appear on top)
    try:
        logo_path = "logo.png"
        print(f"Attempting to load logo from: {os.path.abspath(logo_path)}")
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found at {os.path.abspath(logo_path)}")
        logo = Image.open(logo_path).convert("RGBA")
        logo_width, logo_height = logo.size
        aspect = logo_width / logo_height
        if logo_width > logo_height:
            logo_width = min(logo_width, LOGO_MAX_SIZE[0])
            logo_height = int(logo_width / aspect)
        else:
            logo_height = min(logo_height, LOGO_MAX_SIZE[1])
            logo_width = int(logo_height * aspect)
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        # Center the logo on the x-axis and middle of LOGO_BOX on the y-axis
        logo_x = (CANVAS_SIZE[0] - logo_width) // 2
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2) - (logo_height // 2)
        logo_position = (logo_x, logo_y)
        canvas.paste(logo, logo_position, logo)
        print(f"Logo pasted at {logo_position} with size {logo_width}x{logo_height}")
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        logo_x = (CANVAS_SIZE[0] - 100) // 2  # Approximate width for error text
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2)  # Center y-position for error text
        draw.text((logo_x, logo_y), "Logo Missing", fill="red", font=regular_font)
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        logo_x = (CANVAS_SIZE[0] - 100) // 2  # Approximate width for error text
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2)  # Center y-position for error text
        draw.text((logo_x, logo_y), "Logo Load Error", fill="red", font=regular_font)

    # Source text at comment's original position with customizable text color
    source_text = f"Source: {main_domain}"
    text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = CANVAS_SIZE[0] - PADDING - text_width
    draw.text((text_x, DATE_SOURCE_Y), source_text, fill=TEXT_COLOR, font=regular_font)

    # Headline
    if "not found" in headline.lower():
        headline = "কোন শিরোনাম পাওয়া যায়নি" if language == "Bengali" else "No Headline Found"
    headline = headline.encode('utf-8').decode('utf-8')
    adjust_headline(headline, language, draw, HEADLINE_WIDTH, HEADLINE_MAX_HEIGHT)

    # Date with customizable text color
    date_str = convert_to_date(pub_date, language)
    draw.text((PADDING, DATE_SOURCE_Y), date_str, fill=TEXT_COLOR, font=bangla_font_small)

    # Comment text at y=720, centered, with bold font and larger size
    comment_text = "বিস্তারিত কমেন্টে" if language == "Bengali" else "More in comments"
    bold_font = ImageFont.truetype("NotoSerifBengali-Bold.ttf", 31)  # 20% larger than 26px
    text_bbox = draw.textbbox((0, 0), comment_text, font=bold_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (CANVAS_SIZE[0] - text_width) // 2  # Center horizontally
    draw.text((text_x, 720), comment_text, fill=SECONDARY_TEXT_COLOR, font=bold_font)

    # Add divider 60px below comment_text
    draw.rectangle((0, DIVIDER_Y, CANVAS_SIZE[0], DIVIDER_Y + DIVIDER_THICKNESS), fill=SECONDARY_COLOR)

    # Ad area
    try:
        ad_image = Image.open("cp-ad.png")
        ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
        canvas.paste(ad_image, (0, AD_AREA_Y))
    except FileNotFoundError:
        draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
        draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 50), "Default Ad Image Missing", fill="white", font=regular_font, anchor="mm")

    canvas.save(output_path)
    return output_path

# Streamlit app
st.title("Automated News Photo Card Generator")

# Initialize session state
if 'headline_key' not in st.session_state:
    st.session_state.headline_key = 0
if 'language' not in st.session_state:
    st.session_state.language = "Bengali"
if 'generate_key' not in st.session_state:
    st.session_state.generate_key = 0

# Reset button and No URL checkbox in columns
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Reset", key=f"reset_button_{st.session_state.generate_key}"):
        st.session_state.generate_key += 1
with col2:
    skip_url = st.checkbox("No URL", key=f"skip_url_{st.session_state.generate_key}")

# 1. URL input
url = st.text_input(
    "Enter the news article URL:",
    placeholder="https://example.com/news-article",
    key=f"url_input_{st.session_state.generate_key}",
    disabled=skip_url
)
if not skip_url and url and not is_valid_url(url):
    st.error("Please enter a valid URL (e.g., https://example.com).")
    url = None

# 2. Headline input
placeholder_text = "কোন শিরোনাম পাওয়া যায়নি" if st.session_state.language == "Bengali" else "No Headline Found"
custom_headline = st.text_input(
    f"Enter a custom headline (optional, in {st.session_state.language}):",
    placeholder=placeholder_text,
    key=f"headline_input_{st.session_state.headline_key}_{st.session_state.generate_key}"
)

# 3. Custom image upload
uploaded_image = st.file_uploader("Upload a custom image (optional, overrides image from URL):", type=["png", "jpg", "jpeg"], key=f"image_upload_{st.session_state.generate_key}")
image_source = None
if uploaded_image:
    image_source = uploaded_image
    st.success("Custom image uploaded!")

# 4. Color customization with reset option
with st.expander("Customize Colors", expanded=False):
    st.session_state.primary_color = st.color_picker("Primary Color (Brick Red)", st.session_state.primary_color, key=f"primary_color_{st.session_state.generate_key}")
    st.session_state.secondary_color = st.color_picker("Secondary Color (Mustard Yellow)", st.session_state.secondary_color, key=f"secondary_color_{st.session_state.generate_key}")
    st.session_state.text_color = st.color_picker("Text Color (Date, Source, Comment)", st.session_state.text_color, key=f"text_color_{st.session_state.generate_key}")
    st.session_state.secondary_text_color = st.color_picker("Secondary Text Color (Comment)", st.session_state.secondary_text_color, key=f"secondary_text_color_{st.session_state.generate_key}")
    if st.button("Reset Customizations"):
        st.session_state.primary_color = PRIMARY_DEFAULT_COLOR
        st.session_state.secondary_color = SECONDARY_DEFAULT_COLOR
        st.session_state.text_color = DEFAULT_TEXT_COLOR
        st.session_state.secondary_text_color = DEFAULT_SECONDARY_TEXT_COLOR
        st.experimental_rerun()

# 5. Option to override date
with st.expander("Override Publication Date", expanded=False):
    override_date = st.checkbox("Manually set the publication date", key=f"override_date_{st.session_state.generate_key}")
    if override_date:
        manual_date = st.date_input(
            "Select the publication date:",
            value=datetime.date(2025, 5, 28),  # Updated to today's date
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2025, 5, 28),  # Current date as max
            key=f"date_input_{st.session_state.generate_key}"
        )

# 6. Option to override source
with st.expander("Override Source", expanded=False):
    override_source = st.checkbox("Manually set the source", key=f"override_source_{st.session_state.generate_key}")
    if override_source:
        source_options = [
            "প্রথম আলো", "কালের কন্ঠ", "যুগান্তর", "বিডিনিউজ২৪", "দি ডেইলি স্টার",
            "দি বিজনেস স্ট্যান্ডার্ড", "বাংলা ট্রিবিউন", "দৈনিক পুর্বকোণ", "দৈনিক আজাদী",
            "চট্টগ্রাম প্রতিদিন", "কালবেলা", "আজকের পত্রিকা", "সমকাল", "জনকন্ঠ",
            "ঢাকা পোস্ট", "একাত্তর টিভি", "যমুনা টিভি", "বিবিসি বাংলা", "RTV", "NTV", "ইত্তেফাক"
        ]
        manual_source = st.selectbox(
            "Select the source:",
            options=source_options,
            index=0,  # Default to "প্রথম আলো"
            key=f"source_input_{st.session_state.generate_key}"
        )

# 7. Language selection in collapsible section
with st.expander("Language Settings", expanded=False):
    selected_language = st.selectbox(
        "Choose a language:",
        options=["Bengali", "English"],
        index=0 if st.session_state.language == "Bengali" else 1,
        key=f"language_select_{st.session_state.generate_key}"
    )

# Update session state when language changes
if selected_language != st.session_state.language:
    st.session_state.language = selected_language
    st.session_state.headline_key += 1

# Generate button
if st.button("Generate Photo Card"):
    if not skip_url and not url:
        st.warning("Please enter a valid URL or check 'No URL'.")
    else:
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02)  # Simulate progress
            progress_bar.progress(i + 1)
        try:
            if skip_url:
                # Set defaults when skipping URL
                pub_date = datetime.datetime(2025, 5, 28, 12, 47)  # Current date and time
                headline = "Headline not found"
                image_url = None
                source = "Source not found"
                main_domain = "Unknown"
            else:
                # Extract data from URL
                pub_date, headline, image_url, source, main_domain = extract_news_data(url)

            # Use manual date if override is enabled
            if override_date:
                pub_date = datetime.datetime.combine(manual_date, datetime.time(0, 0))

            # Use manual source if override is enabled
            if override_source:
                main_domain = manual_source

            # Use custom headline if provided, otherwise use extracted or default
            final_headline = custom_headline if custom_headline else headline

            # Use uploaded image if provided, otherwise try URL image
            if not image_source and image_url:
                image_source = image_url

            output_path = create_photo_card(final_headline, image_source, pub_date, main_domain, language=st.session_state.language)
            st.image(output_path, caption=f"Generated Photo Card ({st.session_state.language})")
            with open(output_path, "rb") as file:
                st.download_button("Download Photo Card", file, file_name="photo_card.png")
            st.session_state.generate_key += 1
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.generate_key += 1
