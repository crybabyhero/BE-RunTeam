import requests
import pandas as pd
from app import insert_gold_price  # Import from app.py

def scrape_gold_price():
    try:
        url = "https://pluang.com/api/asset/gold/pricing?daysLimit=1"
        response = requests.get(url)
        data = response.json()

        # Extract and process data
        hargaemas = pd.DataFrame(data['data']['history'])
        hargaemas['Tanggal'] = pd.to_datetime(hargaemas['updated_at']).dt.date
        hargaemas = hargaemas[['Harga Emas (IDR)', 'Tanggal']]
        
        date = hargaemas['Tanggal'][0]
        price = int(hargaemas['Harga Emas (IDR)'][0])  # Ensure price is an integer
        

        insert_gold_price(price=price, date=date)  # Pass extracted date and price
    except Exception as e:
        print(f"Error: {e}") 

# Run the scraper
scrape_gold_price()
