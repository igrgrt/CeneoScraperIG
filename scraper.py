import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from collections import Counter
from fractions import Fraction
import re
import matplotlib.pyplot as plt
import csv
import time

def extract_reviews_main(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extract product name
    product_name_element = soup.find("h1", class_="product-top__product-info__name")  # Adjust this selector based on actual HTML structure
    product_name = product_name_element.text.strip() if product_name_element else "Unknown_Product"

    review_elements = soup.find_all("div", class_="user-post__card")
    reviews = []

    for review in review_elements:
        review_id = review['data-entry-id'] if 'data-entry-id' in review.attrs else "Brak ID"
        author = review.select_one('.user-post__author-name').text.strip() if review.select_one('.user-post__author-name') else "Brak autora"
        recommendation = review.select_one('.user-post__author-recomendation > em').text.strip() if review.select_one('.user-post__author-recomendation > em') else "Brak rekomendacji"
        stars = review.select_one('.user-post__score-count').text.strip() if review.select_one('.user-post__score-count') else "Brak oceny"
        confirmed = 'Tak' if review.select_one('.review-pz') else 'Nie'
        date = review.select_one('.user-post__published > time')['datetime'] if review.select_one('.user-post__published > time') else "Brak daty"
        content = review.select_one('.user-post__text').text.strip() if review.select_one('.user-post__text') else "Brak treści"
        advantages = [adv.text.strip() for adv in review.select('.review-feature__section:has(.review-feature__item--positive) .review-feature__item.review-feature__item--positive')]
        disadvantages = [dis.text.strip() for dis in review.select('.review-feature__section:has(.review-feature__item--negative) .review-feature__item.review-feature__item--negative')]

        reviews.append({
            'review_id': review_id,
            'author': author,
            'recommendation': recommendation,
            'stars': stars,
            'confirmed': confirmed,
            'date': date,
            'content': content,
            'advantages': advantages,
            'disadvantages': disadvantages,
        })
    
    return reviews, product_name


def extract_reviews(product_id):
    all_reviews = []
    page_number = 1
    base_url = f"https://www.ceneo.pl/{product_id}"
    
    # Extract the product name from the first page
    url = f"{base_url}/opinie-{page_number}"
    reviews, product_name = extract_reviews_main(url)
    
    # Check if product name is extracted
    if product_name == "Unknown_Product":
        print("Warning: Product name extraction failed.")
    
    all_reviews.extend(reviews)
    
    while True:
        # Build the URL for the current page of reviews
        url = f"{base_url}/opinie-{page_number}"
        
        # Extract reviews from the current page
        new_reviews = extract_reviews_main(url)
        
        # If no new reviews are found, break the loop (end of pagination)
        if not new_reviews[0]:
            break
        
        # Add new reviews to the list of all reviews
        all_reviews.extend(new_reviews[0])
        
        # Increment the page number to move to the next page
        page_number += 1

    return all_reviews, product_name

def extract_reviews_main(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extract product name (assuming the same structure for all pages)
    if url.endswith('opinie-1'):  # Extract only if it's the first page
        product_name_element = soup.find("h1", class_="product-top__product-info__name")  # Adjust the selector if needed
        product_name = product_name_element.text.strip() if product_name_element else "Unknown_Product"
        print(f"Extracted Product Name: {product_name}")  # Debug: Print the extracted product name
    else:
        product_name = "Unknown_Product"
    
    review_elements = soup.find_all("div", class_="user-post__card")
    reviews = []

    for review in review_elements:
        review_id = review['data-entry-id'] if 'data-entry-id' in review.attrs else "Brak ID"
        author = review.select_one('.user-post__author-name').text.strip() if review.select_one('.user-post__author-name') else "Brak autora"
        recommendation = review.select_one('.user-post__author-recomendation > em').text.strip() if review.select_one('.user-post__author-recomendation > em') else "Brak rekomendacji"
        stars = review.select_one('.user-post__score-count').text.strip() if review.select_one('.user-post__score-count') else "Brak oceny"
        confirmed = 'Tak' if review.select_one('.review-pz') else 'Nie'
        date = review.select_one('.user-post__published > time')['datetime'] if review.select_one('.user-post__published > time') else "Brak daty"
        content = review.select_one('.user-post__text').text.strip() if review.select_one('.user-post__text') else "Brak treści"
        advantages = [adv.text.strip() for adv in review.select('.review-feature__section:has(.review-feature__item--positive) .review-feature__item.review-feature__item--positive')]
        disadvantages = [dis.text.strip() for dis in review.select('.review-feature__section:has(.review-feature__item--negative) .review-feature__item.review-feature__item--negative')]

        reviews.append({
            'review_id': review_id,
            'author': author,
            'recommendation': recommendation,
            'stars': stars,
            'confirmed': confirmed,
            'date': date,
            'content': content,
            'advantages': advantages,
            'disadvantages': disadvantages,
        })
    
    return reviews, product_name

    
def save_reviews_to_json(reviews, product_id):
    with open(product_id, "w",  encoding="utf-8") as f:
        json.dump([convert_to_json (review) for review in reviews], indent=4)
        
    

def save_reviews_to_csv(reviews, product_id, product_name):
    df = pd.DataFrame(reviews)
    # Sanitize product_name for safe file naming
    sanitized_product_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', product_name).replace(' ', '_')
    file_name = f'data/reviews_{sanitized_product_name}_{product_id}.csv'
    df.to_csv(file_name, index=False)

def convert_to_json(review):
    reviews = []
    review_id_element = review.get['data-entry-id']
    review_id = review_id_element if review_id_element else "Brak ID"
    author_element = review.select_one('.user-post__author-name').text.strip()
    author = author_element if author_element else "Brak autora"
    recommendation = review.select_one('.user-post__author-recomendation > em').text.strip() if review.select_one('.user-post__author-recomendation > em') else ""
    stars = review.select_one('.user-post__score-count').text.strip()
    confirmed = 'Tak' if review.select_one('.review-pz') else 'Nie'
    date = review.select_one('.user-post__published > time')['datetime']
    content = review.select_one('.user-post__text').text.strip()
    advantages = [adv.text.strip() for adv in review.select('.review-feature__col:has(> div:contains("Zalety")) .review-feature__item.review-feature__item--positive')]
    disadvantages = [dis.text.strip() for dis in review.select('.review-feature__col:has(> div:contains("Wady")) .review-feature__item.review-feature__item--negative')]
    
    reviews.append({
        'review_id': review_id,
        'author': author,
        'recommendation': recommendation,
        'stars': stars,
        'confirmed': confirmed,
        'date': date,
        'content': content,
        'advantages': advantages,
        'disadvantages': disadvantages,
    })

    return reviews
def analysis(reviews):
    #Średnia ocen
    ratings = [float(Fraction(re.search(r'\d+(?:[.,]\d+)?', review.find("span", class_="user-post__score-count").text.replace(",", ".")).group())) for review in reviews]
    if len(ratings) > 0:
        avarage_rating = sum(ratings) / len(ratings)
    else:
        return "Brak ocen do analizy"
    #Dystrybucja ocen
    ratings_distribution = Counter(ratings)
    
    return{
        "avarage_rating":avarage_rating,
        "ratings_distribution":ratings_distribution,
    }
class Product:
    def __init__(self,product_id):
        self.product_id  = product_id
        self.reviews = []
        
    def add_reviews(self,reviews):
        self.reviews.extend(reviews)
        
class Reviews:
    def __init__(self) -> None:
        pass