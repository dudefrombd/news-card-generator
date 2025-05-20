import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime
import textwrap
import re
from urllib.parse import urlparse
import logging

# Initialize logging
logging.basicConfig(level=logging.ERROR)  # Change to INFO for less verbose, DEBUG for more

# Constants (moved to a separate block for better organization)
CANVAS_SIZE = (1080, 1200)
BRICK_RED = "#9E2A2F"
IMAGE_SIZE = (1080, 650)
SOURCE_BOX_HEIGHT = 50
SOURCE_BOX_Y = 650
DIVIDER_Y = 700
DIVIDER_THICKNESS = 5
MUSTARD_YELLOW = "#fed500"
PADDING = 20
HEADLINE_WIDTH = 1040
HEADLINE_MAX_HEIGHT = 220
DATE_SOURCE_Y = 1050
AD_AREA_Y = 1100
AD_AREA_SIZE = (1080, 100)
LOGO_MAX_SIZE = (158, 79)
AD_LOGO_MAX_SIZE = (225, 90)
LOGO_POSITION = (882, 50)
MAP_OPACITY = 0.3
SOURCE_BOX_OPACITY = 0.7
MAP_BOX_WIDTH = 1080
MAP_BOX_HEIGHT = 400
MAP_BOX_X = 0
MAP_BOX_Y = 700
DEFAULT_DATE = "20 May 2025"  # Added a constant for the default date

# Validate URL (Improved regex for better accuracy)
def is_valid_url(url):
    """
    Checks if a given string is a valid URL.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    regex = re.compile(
        r'^(https?://)'  # Scheme (http or https)
        r'([a-zA-Z0-9.-]+(\.[a-zA-Z]{2,}))'  # Domain
        r'(:[0-9]+)?'  # Optional port number
        r'(/([\w.-]+/?)*)?$',  # Optional path
        re.IGNORECASE
    )
    return bool(regex.match(url))

# Extract main domain from URL
def extract_main_domain(url):
    """
    Extracts the main domain from a URL.

    Args:
        url (str): The URL to extract from.

    Returns:
        str: The main domain, or "Unknown" if extraction fails.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        parts = domain.split(".")
        if len(parts) >= 3 and parts[-2] in ["co", "org", "gov", "edu"]:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    except Exception as e:
        logging.error(f"Error extracting domain from {url}: {e}")
        return "Unknown"

# Extract news data
def extract_news_data(url):
    """
    Extracts news data (publication date, headline, image URL, source) from a given URL.

    Args:
        url (str): The URL of the news article.

    Returns:
        tuple: (publication date (datetime object), headline (str), image URL (str),
                 source (str), main domain(str)).  Returns None for any failed extraction.
    Raises:
        Exception: If the request or parsing fails.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)  # Increased timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        date_tag = soup.find('meta', {'property': 'article:published_time'})
        date_str = date_tag['content'] if date_tag else None
        pub_date = None
        if date_str:
            try:
                pub_date = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                logging.warning(f"Invalid date format: {date_str} for URL: {url}")
                pub_date = None

        headline_tag = soup.find('meta', {'property': 'og:title'})
        headline = headline_tag['content'] if headline_tag else 'Headline not found'

        image_tag = soup.find('meta', {'property': 'og:image'})
        image_url = image_tag['content'] if image_tag else None

        source_tag = soup.find('meta', {'property': 'og:site_name'})
        source = source_tag['content'] if source_tag else 'Source not found'

        main_domain = extract_main_domain(url)
        return pub_date, headline, image_url, source, main_domain

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
        raise Exception(f"Error fetching URL: {e}")
    except Exception as e:
        logging.error(f"Error parsing data from {url}: {e}")
        raise Exception(f"Failed to extract news data: {e}")

# Process image (from URL or uploaded)
def process_image(image_source, is_uploaded=False):
    """
    Processes an image from a URL or an uploaded file, cropping and resizing it.

    Args:
        image_source (str or BytesIO): The URL of the image or the uploaded file.
        is_uploaded (bool, optional): True if the image source is an uploaded file,
                                     False if it's a URL. Defaults to False.

    Returns:
        Image: The processed PIL Image object.

    Raises:
        Exception: If there's an error loading or processing the image.
    """
    try:
        if is_uploaded:
            image = Image.open(image_source)
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_source, headers=headers, timeout=10)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            image = Image.open(image_data)

        width, height = image.size
        crop_height = int(height * 0.15)
        new_height = height - crop_height

        image = image.crop((0, 0, width, new_height))
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
        logging.error(f"Error processing image {image_source}: {e}")
        raise Exception(f"Failed to process image: {e}")

# Process the world map for overlay
def process_world_map(map_path):
    """
    Processes the world map image for overlay, resizing and adjusting opacity.

    Args:
        map_path (str): The file path to the world map image.

    Returns:
        Image: The processed PIL Image object.

    Raises:
        Exception: If there's an error loading or processing the image.
    """
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
        logging.error(f"Error processing world map from {map_path}: {e}")
        raise Exception(f"Failed to process world map: {e}")

# Load fonts with simplified logic and fallback
def load_fonts(language="Bengali", font_size=48):
    """
    Loads fonts based on the specified language and font size, with fallback mechanisms.

    Args:
        language (str, optional): The language for which to load fonts ("Bengali" or "English").
            Defaults to "Bengali".
        font_size (int, optional): The font size. Defaults to 48.

    Returns:
        tuple: (small font (ImageFont), large font (ImageFont), regular font (ImageFont)).
                 Returns default fonts if loading fails.
    """
    base_font_path = "NotoSerif"
    if language == "Bengali":
        large_font_path = f"{base_font_path}Bengali-Bold.ttf"
        small_font_path = f"{base_font_path}Bengali-Regular.ttf"
    else:
        large_font_path = f"{base_font_path}-Bold.ttf"
        small_font_path = f"{base_font_path}-Regular.ttf"

    default_font = ImageFont.load_default()
    large_font = None
    small_font = None
    regular_font = None

    try:
        large_font = ImageFont.truetype(large_font_path, font_size)
    except Exception as e:
        logging.error(f"Failed to load {large_font_path} for size {font_size}: {e}")
        try:
            large_font = ImageFont.truetype("Arial Unicode MS.ttf", font_size)  # Broader fallback
            logging.warning(f"Fallback: Loaded Arial Unicode MS.ttf for size {font_size}")
        except Exception as e2:
            logging.error(f"Fallback failed: {e2}. Using default font for large font.")
            large_font = default_font

    try:
        small_font = ImageFont.truetype(small_font_path, 26)
        regular_font = ImageFont.truetype(small_font_path, 24)
    except Exception as e:
        logging.error(f"Failed to load {small_font_path}: {e}")
        try:
            small_font = ImageFont.truetype("Arial Unicode MS.ttf", 26)
            regular_font = ImageFont.truetype("Arial Unicode MS.ttf", 24)
            logging.warning(f"Fallback: Loaded Arial Unicode MS.ttf for small/regular font")
        except Exception as e2:
            logging.error(f"Fallback failed: {e2}. Using default font for small/regular fonts.")
            small_font = default_font
            regular_font = default_font

    return small_font, large_font, regular_font

# Adjust headline layout
def adjust_headline(headline, language, draw, max_width, max_height):
    """
    Adjusts the headline to fit within the given constraints, including font size adjustment
    and text wrapping.

    Args:
        headline (str): The headline text.
        language (str): The language ("Bengali" or "English").
        draw (ImageDraw.Draw): The ImageDraw object to draw on.
        max_width (int): The maximum width of the headline area.
        max_height (int): The maximum height of the headline area.

    Returns:
        int: The final y-position of the headline text.
    """
    font_sizes = [72, 68, 64, 60, 56, 52, 48]
    best_font_size = font_sizes[0]
    best_headline_lines = []
    best_spacing = 0
    headline_y_start = 830

    logging.debug(f"Processing headline: {headline}")

    for size in font_sizes:
        small_font, large_font, _ = load_fonts(language, size)
        wrap_width = int(max_width / (size * 0.5))
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        logging.debug(f"Wrapped headline into {len(headline_wrapped)} lines with wrap_width={wrap_width}")
        total_height = 0
        headline_lines = []

        if not headline_wrapped:
            logging.warning("Headline wrapping produced no lines. Using original headline.")
            headline_wrapped = [headline]

        for line in headline_wrapped:
            bbox = large_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            logging.debug(f"Line '{line}' width: {line_width}, max allowed: {max_width}")
            if line_width > max_width:
                logging.debug(
                    f"Line '{line}' exceeds max width {max_width} at font size {size}. Skipping this size."
                )
                headline_lines = []
                break
            headline_lines.append(line)
            total_height += line_height

        spacing = int(size * 1.2)
        total_height += (len(headline_lines) - 1) * spacing

        logging.debug(f"Font size {size}: {len(headline_lines)} lines, total height {total_height}")

        if total_height <= max_height and len(headline_lines) > 0:
            best_font_size = size
            best_headline_lines = headline_lines
            best_spacing = spacing
            break

    if not best_headline_lines:
        logging.warning("No suitable font size found. Forcing headline to fit with smallest font size.")
        small_font, large_font, _ = load_fonts(language, font_sizes[-1])
        wrap_width = int(max_width / (font_sizes[-1] * 0.5))
        headline_wrapped = textwrap.wrap(headline, width=wrap_width)
        best_headline_lines = []
        for line in headline_wrapped[:3]:
            bbox = large_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_width:
                best_headline_lines.append(line)
        if not best_headline_lines:
            best_headline_lines = [headline[: int(max_width / 10)].strip()]
        best_spacing = int(font_sizes[-1] * 1.2)
        best_font_size = font_sizes[-1]
        logging.debug(f"Forced rendering with font size {best_font_size}, {len(best_headline_lines)} lines")

    small_font, large_font, _ = load_fonts(language, best_font_size)
    headline_y = headline_y_start

    logging.debug(f"Rendering headline with font size {best_font_size}, lines: {best_headline_lines}")

    for line in best_headline_lines:
        try:
            bbox = large_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_x = PADDING + (HEADLINE_WIDTH - text_width) // 2
            draw.text((text_x, headline_y), line, fill="white", font=large_font)
            logging.debug(f"Rendered line '{line}' at y={headline_y}, width={text_width}")
            headline_y += best_spacing
        except Exception as e:
            logging.error(f"Failed to render line '{line}': {e}")
            fallback_font = ImageFont.load_default()
            draw.text((text_x, headline_y), "Headline Rendering Failed", fill="red", font=fallback_font)
            headline_y += best_spacing

    logging.debug(f"Headline rendered, final y-position: {headline_y}")
    return headline_y

# Convert date to Bengali or English format (only date, no time)
def convert_to_date(pub_date, language="Bengali"):
    """
    Converts a datetime object to a formatted date string, either in Bengali or English.

    Args:
        pub_date (datetime.datetime): The datetime object representing the publication date.
        language (str, optional): The target language ("Bengali" or "English"). Defaults to "Bengali".

    Returns:
        str: The formatted date string.
    """
    if not pub_date:
        return DEFAULT_DATE
    if language == "Bengali":
        bengali_digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
        bengali_months = {
            "January": "জানুয়ারি",
            "February": "ফেব্রুয়ারি",
            "March": "মার্চ",
            "April": "এপ্রিল",
            "May": "মে",
            "June": "জুন",
            "July": "জুলাই",
            "August": "আগস্ট",
            "September": "সেপ্টেম্বর",
            "October": "অক্টোবর",
            "November": "নভেম্বর",
            "December": "ডিসেম্বর",
        }
        date_str = pub_date.strftime("%d %B %Y")
        day, month, year = date_str.split()
        return f"{day.translate(bengali_digits)} {bengali_months.get(month, month)} {year.translate(bengali_digits)}"
    else:
        return pub_date.strftime("%d %B %Y")
# Create the news card
def create_photo_card(headline, image_source, pub_date, main_domain, language="Bengali", output_path="photo_card.png"):
    """
    Creates the news photo card image with the given data and saves it to a file.

    Args:
        headline (str): The headline text.
        image_source (str or BytesIO): The URL of the image or the uploaded image file.
        pub_date (datetime.datetime): The publication date.
        main_domain (str): The source of the news.
        language (str, optional): The language ("Bengali" or "English"). Defaults to "Bengali".
        output_path (str, optional): The path to save the generated image. Defaults to "photo_card.png".

    Returns:
        str: The path to the saved image.
    """
    canvas = Image.new("RGB", CANVAS_SIZE, BRICK_RED)
    draw = ImageDraw.Draw(canvas)
    small_font, large_font, regular_font = load_fonts(language)

    # Re-enable map overlay
    try:
        world_map = process_world_map("world-map.png")
        canvas = Image.new("RGBA", CANVAS_SIZE, BRICK_RED)
        canvas.paste(world_map, (MAP_BOX_X, MAP_BOX_Y), world_map)
        canvas = canvas.convert("RGB")
        draw = ImageDraw.Draw(canvas)
    except Exception as e:
        logging.error(f"Could not load world map: {e}")

    # Add news image
    if image_source:
        try:
            news_image = process_image(image_source, is_uploaded=(not isinstance(image_source, str)))
            canvas.paste(news_image, (0, 0))
        except Exception as e:
            logging.error(f"Error processing image: {e}")
            draw.rectangle((0, 0, IMAGE_SIZE[0], IMAGE_SIZE[1]), fill="gray")
            draw.text(
                (400, 300), f"Image Error: {e}", fill="white", font=regular_font
            )  # Use f-string
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
        logging.error("Logo file not found.")
        draw.text(
            (LOGO_POSITION[0], LOGO_POSITION[1]), "Logo Missing", fill="red", font=regular_font
        )

    # Source text background
    mustard_rgba = tuple(int(MUSTARD_YELLOW[i: i + 2], 16) for i in (1, 3, 5)) + (
        int(255 * SOURCE_BOX_OPACITY),
    )
    draw.rectangle(
        (0, SOURCE_BOX_Y, CANVAS_SIZE[0], SOURCE_BOX_Y + SOURCE_BOX_HEIGHT), fill=mustard_rgba
    )
    source_text = f"Source: {main_domain}"
    text_bbox = draw.textbbox((0, 0), source_text, font=regular_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (CANVAS_SIZE[0] - text_width) // 2
    text_y = SOURCE_BOX_Y + (SOURCE_BOX_HEIGHT - text_height) // 2 - 5
    draw.text((text_x, text_y), source_text, fill="black", font=regular_font)

    # Divider
    draw.rectangle(
        (0, DIVIDER_Y, CANVAS_SIZE[0], DIVIDER_Y + DIVIDER_THICKNESS), fill=MUSTARD_YELLOW
    )

    # Headline
    if "not found" in headline.lower():
        headline = "কোন শিরোনাম পাওয়া যায়নি" if language == "Bengali" else "No Headline Found"
    headline = headline.encode("utf-8").decode("utf-8")
    adjust_headline(headline, language, draw, HEADLINE_WIDTH, HEADLINE_MAX_HEIGHT)

    # Date and comment
    date_str = convert_to_date(pub_date, language)
    draw.text((PADDING, DATE_SOURCE_Y), date_str, fill="white", font=small_font)

    comment_text = "বিস্তারিত কমেন্টে" if language == "Bengali" else "More in comments"
    text_bbox = draw.textbbox((0, 0), comment_text, font=small_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = CANVAS_SIZE[0] - PADDING - text_width
    draw.text((text_x, DATE_SOURCE_Y), comment_text, fill="white", font=small_font)

    # Ad area
    try:
        ad_image = Image.open("cp-ad.png")
        ad_image = ad_image.resize(AD_AREA_SIZE, Image.Resampling.LANCZOS)
        canvas.paste(ad_image, (0, AD_AREA_Y))
    except FileNotFoundError:
        logging.error("Ad image file not found.")
        draw.rectangle(
            (0, AD_AREA_Y, AD_AREA_SIZE[0], AD_AREA_Y + AD_AREA_SIZE[1]), fill="black"
        )
        draw.text(
            (CANVAS_SIZE[0] // 2, AD_AREA_Y + 50),
            "Default Ad Image Missing",
            fill="white",
            font=regular_font,
            anchor="mm",
        )

    canvas.save(output_path)
    return output_path
# Streamlit app
def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Automated News Photo Card Generator")

    # Initialize session state
    if "headline_key" not in st.session_state:
        st.session_state.headline_key = 0
    if "language" not in st.session_state:
        st.session_state.language = "Bengali"
    if "generate_key" not in st.session_state:
        st.session_state.generate_key = 0

    # Reset button
    if st.button("Reset"):
        st.session_state.generate_key += 1

    # 1. URL input
    url = st.text_input(
        "Enter the news article URL:",
        placeholder="https://example.com/news-article",
        key=f"url_input_{st.session_state.generate_key}",
    )
    if url and not is_valid_url(url):
        st.error("Please enter a valid URL (e.g., https://example.com).")
        url = None

    # 2. Headline input
    placeholder_text = (
        "কোন শিরোনাম পাওয়া যায়নি"
        if st.session_state.language == "Bengali"
        else "No Headline Found"
    )
    custom_headline = st.text_input(
        f"Enter a custom headline (optional, in {st.session_state.language}):",
        placeholder=placeholder_text,
        key=f"headline_input_{st.session_state.headline_key}_{st.session_state.generate_key}",
    )

    # 3. Custom image upload
    uploaded_image = st.file_uploader(
        "Upload a custom image (optional, overrides image from URL):",
        type=["png", "jpg", "jpeg"],
        key=f"image_upload_{st.session_state.generate_key}",
    )
    image_source = None
    if uploaded_image:
        image_source = uploaded_image
        st.success("Custom image uploaded!")

    # 4. Language selection dropdown
    st.markdown("**Select Language**")
    selected_language = st.selectbox(
        "Choose a language:",
        options=["Bengali", "English"],
        index=0 if st.session_state.language == "Bengali" else 1,
        key=f"language_select_{st.session_state.generate_key}",
    )

    # Update session state when language changes
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
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
                    if not image_source and image_url:
                        image_source = image_url
                    output_path = create_photo_card(
                        final_headline, image_source, pub_date, main_domain, language=st.session_state.language
                    )
                    st.image(
                        output_path, caption=f"Generated Photo Card ({st.session_state.language})"
                    )
                    with open(output_path, "rb") as file:
                        st.download_button(
                            "Download Photo Card", file, file_name="photo_card.png"
                        )
                    st.session_state.generate_key += 1
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.generate_key += 1
if __name__ == "__main__":
    main()
