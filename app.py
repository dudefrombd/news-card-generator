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

# Theme Colors
PRIMARY_ACCENT_COLOR = "#9f2d32"  # Brick red
SECONDARY_ACCENT_COLOR = "#3c3c3c"  # Dark grey
SUCCESS_COLOR = "#28A745"  # Green
ERROR_COLOR = "#DC3545"  # Red
NEUTRAL_LIGHT = "#E9ECEF"  # Light grey for borders
NEUTRAL_MEDIUM = "#CED4DA"  # Medium grey for disabled
TEXT_LIGHT = "#f54149"  # Reddish color
TEXT_DARK = "#3c3c3c"  # Dark grey for secondary text
BACKGROUND_LIGHT = "#F8F9FA"  # Very light grey
CONTENT_BG = "#FFFFFF"  # Pure white

# Functions
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)'  # Scheme
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # Domain
        r'(/[^?\s]*)?'  # Path (optional)
        r'(\?[^?\s]*)?'  # Query parameters (optional)
        r'(\#.*)?$'  # Fragment (optional)
    )
    return re.match(regex, url) is not None

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

def process_image(image_source, is_uploaded=False, is_base64=False):
    try:
        if is_uploaded:
            image = Image.open(image_source)
        elif is_base64:
            if "," in image_source:
                image_source = image_source.split(",")[1]
            image_data = base64.b64decode(image_source)
            image = Image.open(BytesIO(image_data))
        else:
            image_source = url_to_base64(image_source)
            if "," in image_source:
                image_source = image_source.split(",")[1]
            image_data = base64.b64decode(image_source)
            image = Image.open(BytesIO(image_data))

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

def process_world_map(map_path):
    try:
        map_image = Image.open(map_path).convert("RGBA")
        width, height = map_image.size

        aspect_ratio = width / height
        target_width, target_height = MAP_BOX_WIDTH, MAP_BOX_HEIGHT
        target_aspect = target_width / target_height

        new_width = target_width
        new_height = int(new_width / aspect_ratio)
        map_image = map_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        if new_height > target_height:
            top = (new_height - target_height) // 2
            map_image = map_image.crop((0, top, target_width, top + target_height))
        else:
            new_map = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
            y_offset = (target_height - new_height) // 2
            new_map.paste(map_image, (0, y_offset))
            map_image = new_map

        map_data = map_image.getdata()
        new_data = [(item[0], item[1], item[2], int(item[3] * MAP_OPACITY)) for item in map_data]
        map_image.putdata(new_data)

        return map_image
    except Exception as e:
        raise Exception(f"Failed to process world map: {str(e)}")

def process_logo_box_bg(bg_path):
    try:
        bg_image = Image.open(bg_path).convert("RGBA")
        target_width, target_height = CANVAS_SIZE[0], LOGO_BOX_HEIGHT
        bg_image = bg_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        bg_data = bg_image.getdata()
        new_data = [(item[0], item[1], item[2], int(item[3] * SOURCE_BOX_OPACITY)) for item in bg_data]
        bg_image.putdata(new_data)

        return bg_image
    except Exception as e:
        raise Exception(f"Failed to process logo box background: {str(e)}")

def load_fonts(language="Bengali", font_size=48):
    bangla_font_small = bangla_font_large = regular_font = None

    try:
        bangla_font_large = ImageFont.truetype("NotoSerifBengali-Bold.ttf", font_size)
    except Exception as e:
        try:
            bangla_font_large = ImageFont.truetype("Arial Unicode MS.ttf", font_size)
        except Exception as e2:
            bangla_font_large = ImageFont.load_default()

    try:
        bangla_font_small = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 26)
        regular_font = ImageFont.truetype("NotoSerifBengali-Regular.ttf", 24)
    except Exception as e:
        try:
            bangla_font_small = ImageFont.truetype("Arial Unicode MS.ttf", 26)
            regular_font = ImageFont.truetype("Arial Unicode MS.ttf", 24)
        except Exception as e2:
            bangla_font_small = regular_font = ImageFont.load_default()

    return bangla_font_small, bangla_font_large, regular_font

def adjust_headline(headline, language, draw, max_width, max_height):
    font_sizes = [72, 68, 64, 60, 56, 52, 48]
    best_font_size = font_sizes[0]
    best_headline_lines = []
    best_spacing = 0
    headline_y_start = 830

    for size in font_sizes:
        bangla_font_small, bangla_font_large, _ = load_fonts(language, size)
        wrap_width = int(max_width / (size * 0.5))
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        total_height = 0
        headline_lines = []

        if not headline_wrapped:
            headline_wrapped = [headline]

        for line in headline_wrapped:
            bbox = bangla_font_large.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            if line_width > max_width:
                headline_lines = []
                break
            headline_lines.append(line)
            total_height += line_height

        spacing = int(size * 1.2)
        total_height += (len(headline_lines) - 1) * spacing

        if total_height <= max_height and len(headline_lines) > 0:
            best_font_size = size
            best_headline_lines = headline_lines
            best_spacing = spacing
            break

    if not best_headline_lines:
        bangla_font_small, bangla_font_large, _ = load_fonts(language, font_sizes[-1])
        wrap_width = int(max_width / (font_sizes[-1] * 0.5))
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        best_headline_lines = [line for line in headline_wrapped[:3] if bangla_font_large.getbbox(line)[2] - bangla_font_large.getbbox(line)[0] <= max_width]
        if not best_headline_lines:
            best_headline_lines = [headline[:int(max_width / 10)].strip()]
        best_spacing = int(font_sizes[-1] * 1.2)
        best_font_size = font_sizes[-1]

    bangla_font_small, bangla_font_large, _ = load_fonts(language, best_font_size)
    headline_y = headline_y_start

    for line in best_headline_lines:
        bbox = bangla_font_large.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2
        draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
        headline_y += best_spacing

    return headline_y

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

def create_photo_card(headline, image_source, pub_date, main_domain, language="Bengali", output_path="photo_card.png"):
    canvas = Image.new("RGB", CANVAS_SIZE, PRIMARY_COLOR)
    draw = ImageDraw.Draw(canvas)
    bangla_font_small, bangla_font_large, regular_font = load_fonts(language)

    try:
        world_map = process_world_map("world-map.png")
        canvas = Image.new("RGBA", CANVAS_SIZE, PRIMARY_COLOR)
        canvas.paste(world_map, (MAP_BOX_X, MAP_BOX_Y), world_map)
        canvas = canvas.convert("RGB")
        draw = ImageDraw.Draw(canvas)
    except Exception as e:
        print(f"Warning: Could not load world map: {str(e)}")

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

    secondary_rgba = tuple(int(SECONDARY_COLOR[i:i+2], 16) for i in (1, 3, 5)) + (int(255 * SOURCE_BOX_OPACITY),)
    draw.rectangle((0, LOGO_BOX_Y, CANVAS_SIZE[0], LOGO_BOX_Y + LOGO_BOX_HEIGHT), fill=secondary_rgba)

    if st.session_state.show_logo_box_overlay:
        try:
            logo_box_bg = process_logo_box_bg("logo-box-bg.png")
            canvas.paste(logo_box_bg, (0, LOGO_BOX_Y), logo_box_bg)
        except Exception as e:
            print(f"Warning: Could not load logo box background: {str(e)}")

    try:
        if st.session_state.custom_logo:
            logo_data = base64.b64decode(st.session_state.custom_logo.split(",")[1])
            logo = Image.open(BytesIO(logo_data)).convert("RGBA")
        else:
            logo_path = "logo.png"
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
        logo_x = (CANVAS_SIZE[0] - logo_width) // 2
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2) - (logo_height // 2)
        canvas.paste(logo, (logo_x, logo_y), logo)
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        logo_x = (CANVAS_SIZE[0] - 100) // 2
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2)
        draw.text((logo_x, logo_y), "Logo Missing", fill="red", font=regular_font)
    except Exception as e:
        print(f"Error loading logo: {str(e)}")
        logo_x = (CANVAS_SIZE[0] - 100) // 2
        logo_y = LOGO_BOX_Y + (LOGO_BOX_HEIGHT // 2)
        draw.text((logo_x, logo_y), "Logo Load Error", fill="red", font=regular_font)

    source_text = f"Source: {main_domain}"
    text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = CANVAS_SIZE[0] - PADDING - text_width
    draw.text((text_x, DATE_SOURCE_Y), source_text, fill=TEXT_COLOR, font=regular_font)

    if "not found" in headline.lower():
        headline = "কোন শিরোনাম পাওয়া যায়নি" if language == "Bengali" else "No Headline Found"
    headline = headline.encode('utf-8').decode('utf-8')
    adjust_headline(headline, language, draw, HEADLINE_WIDTH, HEADLINE_MAX_HEIGHT)

    date_str = convert_to_date(pub_date, language)
    draw.text((PADDING, DATE_SOURCE_Y), date_str, fill=TEXT_COLOR, font=bangla_font_small)

    comment_text = "বিস্তারিত কমেন্টে" if language == "Bengali" else "More in comments"
    bold_font = ImageFont.truetype("NotoSerifBengali-Bold.ttf", 31)
    text_bbox = draw.textbbox((0, 0), comment_text, font=bold_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (CANVAS_SIZE[0] - text_width) // 2
    draw.text((text_x, 720), comment_text, fill=SECONDARY_TEXT_COLOR, font=bold_font)

    draw.rectangle((0, DIVIDER_Y, CANVAS_SIZE[0], DIVIDER_Y + DIVIDER_THICKNESS), fill=SECONDARY_COLOR)

    try:
        if st.session_state.custom_ad:
            ad_data = base64.b64decode(st.session_state.custom_ad.split(",")[1])
            ad_image = Image.open(BytesIO(ad_data))
        else:
            ad_image = Image.open("cp-ad.png")
        ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
        canvas.paste(ad_image, (0, AD_AREA_Y))
    except FileNotFoundError:
        draw.rectangle((0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black")
        draw.text((CANVAS_SIZE[0] // 2, AD_AREA_Y + 50), "Default Ad Image Missing", fill="white", font=regular_font, anchor="mm")

    canvas.save(output_path)
    return output_path

# Initialize session state for colors, custom images, and logo box overlay
if 'primary_color' not in st.session_state:
    st.session_state.primary_color = PRIMARY_ACCENT_COLOR
if 'secondary_color' not in st.session_state:
    st.session_state.secondary_color = "#fbd302"  # Default to mustard yellow
if 'text_color' not in st.session_state:
    st.session_state.text_color = "#ffffff"  # Default to white
if 'secondary_text_color' not in st.session_state:
    st.session_state.secondary_text_color = "#fbd302"  # Default to mustard yellow
if 'custom_logo' not in st.session_state:
    st.session_state.custom_logo = None
if 'custom_logo_name' not in st.session_state:
    st.session_state.custom_logo_name = None
if 'custom_ad' not in st.session_state:
    st.session_state.custom_ad = None
if 'custom_ad_name' not in st.session_state:
    st.session_state.custom_ad_name = None
if 'show_logo_box_overlay' not in st.session_state:
    st.session_state.show_logo_box_overlay = True
if 'generate_key' not in st.session_state:
    st.session_state.generate_key = 0
if 'language' not in st.session_state:
    st.session_state.language = "Bengali"
if 'headline_key' not in st.session_state:
    st.session_state.headline_key = 0

# Use session state colors
PRIMARY_COLOR = st.session_state.primary_color
SECONDARY_COLOR = st.session_state.secondary_color
TEXT_COLOR = st.session_state.text_color
SECONDARY_TEXT_COLOR = st.session_state.secondary_text_color

# Custom CSS for modern UI
st.markdown(
    f"""
    <style>
    /* App background and layout */
    .stApp {{
        background-color: {BACKGROUND_LIGHT};
        font-family: 'Inter', 'Roboto', 'Open Sans', 'Lato', sans-serif;
    }}
    /* Content area */
    .main .block-container {{
        background-color: {CONTENT_BG};
        padding: 2rem 3rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        max-width: 960px;
        margin: 0 auto;
    }}
    /* Header styling */
    .css-1d391kg {{ /* Title */
        font-size: 28px;
        font-weight: 600;
        color: {PRIMARY_ACCENT_COLOR};
        text-align: left;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }}
    .tagline {{
        font-size: 14px;
        color: {TEXT_DARK};
        text-align: left;
        margin-bottom: 1rem;
    }}
    /* Subheaders */
    h3 {{
        font-size: 18px !important;
        margin-bottom: 0.15rem !important;
        margin-top: 0.5rem !important;
    }}
    /* Containers for specific sections */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div {{
        margin-bottom: 0.15rem !important;
    }}
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        border: 1px solid {NEUTRAL_LIGHT};
        background-color: {CONTENT_BG};
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: {PRIMARY_ACCENT_COLOR};
        outline: none;
    }}
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {{
        font-size: 14px;
        color: {TEXT_LIGHT};
        margin-bottom: 0.3rem;
    }}
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {{
        color: {TEXT_DARK};
    }}
    /* File uploader */
    .stFileUploader > div {{
        border: 2px dashed {NEUTRAL_MEDIUM};
        border-radius: 8px;
        background-color: {BACKGROUND_LIGHT};
        padding: 1rem;
        text-align: center;
    }}
    .stFileUploader label {{
        color: {TEXT_LIGHT};
        font-size: 14px;
    }}
    .stFileUploader [data-testid="stFileUploadDropzone"] {{
        color: {PRIMARY_ACCENT_COLOR};
    }}
    .stFileUploader [data-testid="stFileUploadDropzone"] div {{
        margin-top: 0.3rem;
    }}
    /* Checkboxes and radio buttons */
    .stCheckbox > label > span,
    .stRadio > label > span {{
        color: {TEXT_LIGHT};
    }}
    .stCheckbox [type="checkbox"]:checked + span::before,
    .stRadio [type="radio"]:checked + span::before {{
        background-color: {PRIMARY_ACCENT_COLOR};
        border-color: {PRIMARY_ACCENT_COLOR};
    }}
    /* Expander */
    .stExpander {{
        border: 1px solid {NEUTRAL_LIGHT};
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }}
    .stExpander > div > div {{
        background-color: {BACKGROUND_LIGHT};
        padding: 0.5rem 1rem;
    }}
    .stExpander [data-testid="stExpanderHeader"] {{
        padding: 0.5rem 1rem;
        font-size: 16px;
        font-weight: 500;
        color: {TEXT_LIGHT};
    }}
    /* Buttons */
    .stButton > button {{
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 500;
    }}
    .stButton > button[kind="primary"] {{
        background-color: {PRIMARY_ACCENT_COLOR};
        color: {CONTENT_BG};
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #892729;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .stButton > button[kind="secondary"] {{
        background-color: {SECONDARY_ACCENT_COLOR};
        color: {CONTENT_BG};
        border: none;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background-color: #2d2d2d;
    }}
    /* Custom reset style for specific buttons */
    button[kind="secondary"][data-testid="reset-button"],
    button[kind="secondary"][data-testid="reset-customizations-button"],
    button[kind="secondary"][data-testid="download-button"] {{
        background-color: transparent !important;
        color: {TEXT_LIGHT} !important;
        border: 1px solid {NEUTRAL_LIGHT} !important;
    }}
    button[kind="secondary"][data-testid="reset-button"]:hover,
    button[kind="secondary"][data-testid="reset-customizations-button"]:hover,
    button[kind="secondary"][data-testid="download-button"]:hover {{
        background-color: {NEUTRAL_LIGHT} !important;
    }}
    /* Progress bar */
    .stProgress > div > div > div > div {{
        background-color: {PRIMARY_ACCENT_COLOR};
    }}
    /* Section spacing */
    .stSpinner, .stSuccess, .stError {{
        margin: 0.5rem 0;
    }}
    /* Adjust column spacing */
    [data-testid="column"] + [data-testid="column"] {{
        margin-left: 1.5rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Tagline
st.markdown(f"<h1 class='css-1d391kg'>Automated News Photo Card Generator</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='tagline'>Create engaging news visuals instantly.</p>", unsafe_allow_html=True)

# Main layout with one column
col1 = st.container()

with col1:
    # URL input and No URL checkbox
    with st.container():
        st.subheader("Put Your Link")
        col_url, col_checkbox = st.columns([3, 1])
        with col_url:
            url = st.text_input(
                "Enter the news article URL",
                placeholder="https://example.com/news-article",
                key=f"url_input_{st.session_state.generate_key}",
                disabled=st.session_state.get(f"skip_url_{st.session_state.generate_key}", False)
            )
        with col_checkbox:
            skip_url = st.checkbox("Skip URL", key=f"skip_url_{st.session_state.generate_key}")
            if st.button("Reset", key=f"reset_button_{st.session_state.get('generate_key', 0)}", type="secondary", help="Reset the form"):
                st.session_state.generate_key += 1
        if not skip_url and url and not is_valid_url(url):
            st.error("Please enter a valid URL (e.g., https://example.com).")
            url = None

    # Headline
    with st.container():
        st.subheader("Headline")
        placeholder_text = "কোন শিরোনাম পাওয়া যায়নি" if st.session_state.language == "Bengali" else "No Headline Found"
        custom_headline = st.text_input(
            "Enter a custom headline",
            placeholder=placeholder_text,
            key=f"headline_input_{st.session_state.headline_key}_{st.session_state.generate_key}"
        )

    # Image (moved below Headline)
    with st.container():
        st.subheader("Image")
        uploaded_image = st.file_uploader(
            "Upload a custom image",
            type=["png", "jpg", "jpeg"],
            key=f"image_upload_{st.session_state.generate_key}"
        )
        image_source = uploaded_image if uploaded_image else None
        if uploaded_image:
            st.success(f"Custom image '{uploaded_image.name}' uploaded!")

    # Override Settings
    with st.expander("Override Settings"):
        override_date = st.checkbox(
            "Manually set the publication date",
            key=f"override_date_{st.session_state.generate_key}"
        )
        if override_date:
            manual_date = st.date_input(
                "Select the publication date",
                value=datetime.date.today(),
                min_value=datetime.date(1900, 1, 1),
                max_value=datetime.date.today(),
                key=f"date_input_{st.session_state.generate_key}"
            )

        override_source = st.checkbox(
            "Manually set the source",
            key=f"override_source_{st.session_state.generate_key}"
        )
        if override_source:
            source_options = [
                "প্রথম আলো", "কালের কণ্ঠ", "যুগান্তর", "বিডিনিউজ২৪", "দি ডেইলি স্টার",
                "দি বিজনেস স্ট্যান্ডার্ড", "বাংলা ট্রিবিউন", "দৈনিক পূর্বকোণ", "দৈনিক আজাদী",
                "চট্টগ্রাম প্রতিদিন", "কালবেলা", "আজকের পত্রিকা", "সমকাল", "জনকণ্ঠ",
                "ঢাকা পোস্ট", "একাত্তর টিভি", "যমুনা টিভি", "বিবিসি বাংলা", "RTV", "NTV", "ইত্তেফাক"
            ]
            manual_source = st.selectbox(
                "Select the source",
                options=source_options,
                index=0,
                key=f"source_input_{st.session_state.generate_key}"
            )

    # Additional Customisation
    with st.expander("Additional Customisation"):
        st.session_state.show_logo_box_overlay = st.checkbox(
            "Show Logo Box Overlay",
            value=st.session_state.show_logo_box_overlay,
            key=f"show_logo_box_overlay_{st.session_state.generate_key}"
        )

        # Custom logo and ad upload sections
        st.subheader("Logo & Ad")
        custom_logo_upload = st.file_uploader(
            "Upload a custom logo",
            type=["png", "jpg", "jpeg"],
            key=f"custom_logo_upload_{st.session_state.generate_key}"
        )
        if custom_logo_upload:
            logo_bytes = custom_logo_upload.read()
            logo_base64 = f"data:image/png;base64,{base64.b64encode(logo_bytes).decode('utf-8')}"
            st.session_state.custom_logo = logo_base64
            st.session_state.custom_logo_name = custom_logo_upload.name
            st.success(f"Custom logo '{custom_logo_upload.name}' uploaded!")

        custom_ad_upload = st.file_uploader(
            "Upload a custom ad",
            type=["png", "jpg", "jpeg"],
            key=f"custom_ad_upload_{st.session_state.generate_key}"
        )
        if custom_ad_upload:
            ad_bytes = custom_ad_upload.read()
            ad_base64 = f"data:image/png;base64,{base64.b64encode(ad_bytes).decode('utf-8')}"
            st.session_state.custom_ad = ad_base64
            st.session_state.custom_ad_name = custom_ad_upload.name
            st.success(f"Custom ad '{custom_ad_upload.name}' uploaded!")

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.primary_color = st.color_picker(
                "Primary Color",
                st.session_state.primary_color,
                key=f"primary_color_{st.session_state.generate_key}"
            )
        with col2:
            st.session_state.secondary_color = st.color_picker(
                "Secondary Color",
                st.session_state.secondary_color,
                key=f"secondary_color_{st.session_state.generate_key}"
            )

        col3, col4 = st.columns(2)
        with col3:
            st.session_state.text_color = st.color_picker(
                "Primary Text Color",
                st.session_state.text_color,
                key=f"text_color_{st.session_state.generate_key}"
            )
        with col4:
            st.session_state.secondary_text_color = st.color_picker(
                "Secondary Text Color",
                st.session_state.secondary_text_color,
                key=f"secondary_text_color_{st.session_state.generate_key}"
            )

        st.subheader("Language Selection")
        previous_language = st.session_state.language
        language_options = ["Bengali", "English"]
        st.session_state.language = st.radio(
            "Select Language",
            options=language_options,
            index=language_options.index(st.session_state.language),
            key=f"language_radio_{st.session_state.generate_key}"
        )
        if st.session_state.language != previous_language:
            st.session_state.headline_key += 1

        if st.button("Reset Customizations", key="reset_customizations_button", type="secondary"):
            st.session_state.generate_key += 1
            st.session_state.primary_color = PRIMARY_ACCENT_COLOR
            st.session_state.secondary_color = "#fbd302"
            st.session_state.text_color = "#ffffff"
            st.session_state.secondary_text_color = "#fbd302"
            st.session_state.custom_logo = None
            st.session_state.custom_logo_name = None
            st.session_state.custom_ad = None
            st.session_state.custom_ad_name = None
            st.session_state.show_logo_box_overlay = True
            st.session_state.language = "Bengali"
            st.session_state.headline_key += 1

    # Generate Button
    if st.button("Generate Photo Card", type="primary"):
        if not skip_url and not url:
            st.warning("Please enter a valid URL or check 'Skip URL'.")
        else:
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            try:
                if skip_url:
                    pub_date = datetime.datetime(2025, 6, 3, 13, 54)
                    headline = "Headline not found"
                    image_url = None
                    source = "Source not found"
                    main_domain = "Unknown"
                else:
                    pub_date, headline, image_url, source, main_domain = extract_news_data(url)

                if override_date:
                    pub_date = datetime.datetime.combine(manual_date, datetime.time(0, 0))

                if override_source:
                    main_domain = manual_source

                final_headline = custom_headline if custom_headline else headline

                if not image_source and image_url:
                    image_source = image_url

                output_path = create_photo_card(final_headline, image_source, pub_date, main_domain, language=st.session_state.language)
                st.image(output_path, caption=f"Generated Photo Card ({st.session_state.language})")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png", type="secondary", key="download_button")
                st.session_state.generate_key += 1
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.generate_key += 1
