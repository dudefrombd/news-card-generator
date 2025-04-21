import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime
import textwrap
import re
import os

# Constants for layout and styling
CANVAS_SIZE = (1080, 1080)
CANVAS_COLOR = "#003087"  # Blue background
IMAGE_SIZE = (840, 600)
IMAGE_POSITION = (120, 150)  # Adjusted for centering
DATE_BOX_SIZE = (300, 60)
DATE_POSITION = (390, 50)  # (1080 - 300) // 2 = 390
DATE_GAP = 40  # Gap between date box and image
HEADLINE_MAX_WIDTH = 900
HEADLINE_Y_START = 780  # Image at y=150, height=600, gap=30
HEADLINE_LINE_SPACING = 60
LOGO_POSITION = (40, 950)
WEBSITE_TEXT_POSITION = (200, 970)
WEBSITE_URL_POSITION = (850, 970)

# Function to validate URL
def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
        r'(/[^?\s]*)?$'  # optional path
    )
    return re.match(regex, url) is not None

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

# Function to load fonts with fallbacks and error handling
def load_fonts():
    bangla_font_small = bangla_font_large = regular_font = None
    font_warnings = []

    # Load Bangla fonts with fallbacks
    bangla_fonts = ["SolaimanLipi.ttf", "NotoSerifBengali-Regular.ttf", "Kalpurush.ttf"]
    for font_file in bangla_fonts:
        try:
            if not os.path.exists(font_file):
                font_warnings.append(f"Font file not found: {font_file}")
                continue
            bangla_font_small = ImageFont.truetype(font_file, 30)
            bangla_font_large = ImageFont.truetype(font_file, 50)
            st.write(f"Debug: Successfully loaded Bangla font: {font_file}")
            break
        except IOError as e:
            font_warnings.append(f"Error loading {font_file}: {str(e)}")
    if bangla_font_small is None:
        font_warnings.append("All Bangla fonts failed to load, using default font (Bangla may not render correctly).")
        bangla_font_small = bangla_font_large = ImageFont.load_default()

    # Load regular font for non-Bangla text
    try:
        regular_font = ImageFont.truetype("Arial.ttf", 30)
        st.write("Debug: Successfully loaded regular font: Arial.ttf")
    except IOError:
        font_warnings.append("Arial.ttf not found, using default font.")
        regular_font = ImageFont.load_default()

    if font_warnings:
        st.warning("Font Loading Issues:\n" + "\n".join(font_warnings))
    
    return bangla_font_small, bangla_font_large, regular_font

# Function to create the news card
def create_photo_card(headline, image_url, pub_date, logo_path="logo.png", output_path="photo_card.png"):
    try:
        # Create a blank canvas
        canvas = Image.new("RGB", CANVAS_SIZE, CANVAS_COLOR)
        draw = ImageDraw.Draw(canvas)

        # Load fonts
        bangla_font_small, bangla_font_large, regular_font = load_fonts()

        # Add the date (top center)
        date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")
        draw.rectangle((DATE_POSITION[0], DATE_POSITION[1], 
                        DATE_POSITION[0] + DATE_BOX_SIZE[0], DATE_POSITION[1] + DATE_BOX_SIZE[1]), fill="white")
        draw.text((DATE_POSITION[0] + 40, DATE_POSITION[1] + 15), date_str, fill="black", font=regular_font)

        # Download and add the news image
        image_y = DATE_POSITION[1] + DATE_BOX_SIZE[1] + DATE_GAP
        if image_url:
            news_image = download_image(image_url)
            news_image = news_image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
            canvas.paste(news_image, IMAGE_POSITION)
        else:
            draw.rectangle((IMAGE_POSITION[0], image_y, 
                           IMAGE_POSITION[0] + IMAGE_SIZE[0], image_y + IMAGE_SIZE[1]), fill="gray")
            draw.text((400, image_y + 300), "No Image Available", fill="white", font=regular_font)

        # Add a yellow border around the image
        draw.rectangle((IMAGE_POSITION[0], image_y, 
                       IMAGE_POSITION[0] + IMAGE_SIZE[0], image_y + IMAGE_SIZE[1]), outline="yellow", width=5)

        # Add the headline (below the image, centered)
        if "not found" in headline.lower():
            headline = "পরিবারে অশান্তি বিশ্ববিদ্যালয়ের পড়াশোনা হত্যার গ্রেপ্তার"
        headline = headline.encode('utf-8').decode('utf-8')
        st.write(f"Debug: Headline text: {headline}")
        wrapped_text = textwrap.wrap(headline, width=40)
        st.write(f"Debug: Wrapped headline: {wrapped_text}")
        headline_y = HEADLINE_Y_START
        if not wrapped_text:
            st.warning("No wrapped text to render for headline!")
            draw.text((CANVAS_SIZE[0] // 2, headline_y), "Headline Missing", fill="white", font=regular_font, anchor="mm")
        for line in wrapped_text:
            text_bbox = draw.textbbox((0, 0), line, font=bangla_font_large)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (CANVAS_SIZE[0] - text_width) // 2
            draw.text((text_x, headline_y), line, fill="white", font=bangla_font_large)
            headline_y += HEADLINE_LINE_SPACING

        # Add the logo (bottom left)
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((150, 75), Image.Resampling.LANCZOS)
            canvas.paste(logo, LOGO_POSITION, logo)
        except FileNotFoundError:
            draw.text(LOGO_POSITION, "Logo Missing", fill="red", font=regular_font)

        # Add website text and URL
        draw.text(WEBSITE_TEXT_POSITION, "Visit our site", fill="yellow", font=regular_font)
        draw.text(WEBSITE_URL_POSITION, "facebook/leadne", fill="white", font=regular_font)

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
                pub_date, headline, image_url, source = extract_news_data(url)
                output_path = create_photo_card(headline, image_url, pub_date, logo_path=logo_path)
                st.image(output_path, caption="Generated Photo Card")
                with open(output_path, "rb") as file:
                    st.download_button("Download Photo Card", file, file_name="photo_card.png")
            except Exception as e:
                st.error(f"Error: {str(e)}")
