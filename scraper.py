import requests
import pandas as pd
from app import insert_gold_price, get_prediction_until, delete_gold_prices_from_today  # Import from app.py

def scrape_gold_price():
    try:
        delete_gold_prices_from_today()

        url = "https://pluang.com/api/asset/gold/pricing?daysLimit=1"
        response = requests.get(url)
        data = response.json()

        # Extract and process data
        hargaemas = pd.DataFrame(data['data']['history'])
        hargaemas['Tanggal'] = pd.to_datetime(hargaemas['updated_at']).dt.date
        hargaemas['Harga Emas (IDR)'] = hargaemas['sell']
        hargaemas = hargaemas[['Harga Emas (IDR)', 'Tanggal']]


        for _, row in hargaemas.iterrows():
            insert_gold_price(price=row['Harga Emas (IDR)'], date=row['Tanggal'])

        get_prediction_until()
    except Exception as e:
        print(f"Error: {e}")

# Run the scraper
scrape_gold_price()
