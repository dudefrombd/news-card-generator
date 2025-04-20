import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from io import BytesIO

# Function to extract news details from the URL
def create_news_card(date, headline, image_url, source):
    # Load the background image
    background = Image.new('RGB', (800, 800), color='white')

    # Add headline
    draw = ImageDraw.Draw(background)
    font = ImageFont.load_default()
    draw.text((50, 50), headline, fill='black', font=font)

    # Add date
    draw.text((50, 150), date, fill='gray', font=font)

    # Add source name
    draw.text((50, 200), source, fill='blue', font=font)

    # Download the image from the URL
    img_response = requests.get(image_url)
    img = Image.open(BytesIO(img_response.content))
    img = img.resize((400, 400))  # Resize image to fit the card
    background.paste(img, (200, 250))

    # Add logo (this should be the news website's logo, here it's just a placeholder)
    try:
        logo = Image.open('logo.png')  # Replace with your actual logo path
    except FileNotFoundError:
        logo = None  # Handle missing logo (you can optionally add a default image or skip it)
    if logo:
        logo = logo.resize((100, 100))
        background.paste(logo, (650, 650))

    # Save or display the generated image
    background.save('news_card.png')
    return background


# Function to create the photo card
def create_news_card(date, headline, image_url, source):
    # Load the background image
    background = Image.new('RGB', (800, 800), color='white')

    # Add headline
    draw = ImageDraw.Draw(background)
    font = ImageFont.load_default()
    draw.text((50, 50), headline, fill='black', font=font)

    # Add date
    draw.text((50, 150), date, fill='gray', font=font)

    # Add source name
    draw.text((50, 200), source, fill='blue', font=font)

    # Download the image from the URL
    img_response = requests.get(image_url)
    img = Image.open(BytesIO(img_response.content))
    img = img.resize((400, 400))  # Resize image to fit the card
    background.paste(img, (200, 250))

    # Add logo (this should be the news website's logo, here it's just a placeholder)
    logo = Image.open('path_to_logo.png')  # Provide the path to the logo
    logo = logo.resize((100, 100))
    background.paste(logo, (650, 650))

    # Save or display the generated image
    background.save('news_card.png')
    return background

# Streamlit interface
def main():
    st.title("News Photo Card Generator")
    news_url = st.text_input("Enter the News URL")

    if news_url:
        date, headline, image_url, source = extract_news_data(news_url)
        news_card = create_news_card(date, headline, image_url, source)
        st.image(news_card)

if __name__ == '__main__':
    main()
