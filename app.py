import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime

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

# Function to create the news card
def create_photo_card(headline, image_url, pub_date, logo_path="logo.png", output_path="photo_card.png"):
    try:
        # Create a blank canvas (800x600, blue background)
        canvas = Image.new("RGB", (800, 600), "#003087")  # Blue background
        draw = ImageDraw.Draw(canvas)

        # Download and add the news image (resize to fit within a frame)
        if image_url:
            news_image = download_image(image_url)
            news_image = news_image.resize((700, 300), Image.Resampling.LANCZOS)
            canvas.paste(news_image, (50, 50))
        else:
            # Draw a placeholder if no image is available
            draw.rectangle((50, 50, 750, 350), fill="gray")
            draw.text((300, 150), "No Image Available", fill="white", font=ImageFont.truetype("arial.ttf", 20))

        # Add a yellow border around the image
        draw.rectangle((50, 50, 750, 350), outline="yellow", width=5)

        # Add the date (top center)
        date_str = pub_date.strftime("%d %B %Y") if pub_date else datetime.datetime.now().strftime("%d %B %Y")
        draw.rectangle((300, 10, 500, 40), fill="white")
        draw.text((350, 15), date_str, fill="black", font=ImageFont.truetype("TiroBangla.ttf", 20))

        # Add the headline (below the image)
        headline = (headline[:50] + "...") if len(headline) > 50 else headline
        draw.text((50, 370), headline, fill="white", font=ImageFont.truetype("TiroBangla.ttf", 30))

        # Add the logo (bottom left)
        logo = Image.open(logo_path)
        logo = logo.resize((100, 50), Image.Resampling.LANCZOS)
        canvas.paste(logo, (50, 500))

        # Add website text below the logo
        draw.text((160, 520), "Visit our site", fill="yellow", font=ImageFont.truetype("arial.ttf", 20))

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
