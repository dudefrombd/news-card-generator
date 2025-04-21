import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from bs4 import BeautifulSoup
import datetime

# Function to extract news details from the URL
def extract_news_data(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extracting date with error handling for missing tag
    date_tag = soup.find('meta', {'property': 'article:published_time'})
    date = date_tag['content'] if date_tag else 'Date not found'

    # Extracting headline with error handling for missing tag
    headline_tag = soup.find('meta', {'property': 'og:title'})
    headline = headline_tag['content'] if headline_tag else 'Headline not found'

    # Extracting image URL with error handling for missing tag
    image_tag = soup.find('meta', {'property': 'og:image'})
    image_url = image_tag['content'] if image_tag else 'Image not found'

    # Extracting source with error handling for missing tag
    source_tag = soup.find('meta', {'property': 'og:site_name'})
    source = source_tag['content'] if source_tag else 'Source not found'

    return date, headline, image_url, source

# Function to create the news card
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def create_photo_card(headline, image_path, pub_date, logo_path="logo.png", output_path="photo_card.png"):
    # Create a blank canvas (800x600, blue background)
    canvas = Image.new("RGB", (800, 600), "#003087")  # Blue background
    draw = ImageDraw.Draw(canvas)

    # Add the news image (resize to fit within a frame)
    news_image = Image.open(image_path)
    news_image = news_image.resize((700, 300), Image.LANCZOS)
    canvas.paste(news_image, (50, 50))

    # Add a yellow border around the image
    draw.rectangle((50, 50, 750, 350), outline="yellow", width=5)

    # Add the date (top center)
    if pub_date:
        date_str = pub_date.strftime("%d %B %Y")
    else:
        date_str = datetime.datetime.now().strftime("%d %B %Y")
    draw.rectangle((300, 10, 500, 40), fill="white")
    draw.text((350, 15), date_str, fill="black", font=ImageFont.truetype("arial.ttf", 20))

    # Add the headline (below the image)
    draw.text((50, 370), headline, fill="white", font=ImageFont.truetype("arial.ttf", 30))

    # Add the logo (bottom left)
    logo = Image.open(logo_path)
    logo = logo.resize((100, 50), Image.LANCZOS)
    canvas.paste(logo, (50, 500))

    # Add call to action (bottom right) - QR code
    import qrcode
    qr = qrcode.QRCode(box_size=5)
    qr.add_data("https://rtvonline.com")  # Replace with your site
    qr.make(fit=True)
    qr_img = qr.make_image(fill="black", back_color="white")
    qr_img = qr_img.resize((100, 100), Image.LANCZOS)
    canvas.paste(qr_img, (650, 450))

    # Add website text below the logo
    draw.text((160, 520), "Visit our site", fill="yellow", font=ImageFont.truetype("arial.ttf", 20))

    # Save the photo card
    canvas.save(output_path)
    return output_path

# Streamlit app
import streamlit as st

st.title("Automated News Photo Card Generator")
url = st.text_input("Enter the news article URL:")

if st.button("Generate Photo Card"):
    if url:
        try:
            # Extract data
            headline, image_path, pub_date = extract_news_data(url)
            # Create photo card
            output_path = create_photo_card(headline, image_path, pub_date)
            # Display the result
            st.image(output_path, caption="Generated Photo Card")
            with open(output_path, "rb") as file:
                st.download_button("Download Photo Card", file, file_name="photo_card.png")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter a valid URL.")
