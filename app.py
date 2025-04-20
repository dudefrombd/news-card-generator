import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from io import BytesIO

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

    if news_url:  # Ensure the URL is provided
        try:
            # Call the function to extract data
            date, headline, image_url, source = extract_news_data(news_url)
            news_card = create_news_card(date, headline, image_url, source)  # Create the news card
            st.image(news_card)  # Display the card
        except Exception as e:
            st.error(f"An error occurred: {e}")  # Show the error to the user

if __name__ == '__main__':
    main()
