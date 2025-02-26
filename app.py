from flask import Flask, request, jsonify
from models.model import predict, predict_until
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import date as dt, timedelta

app = Flask(__name__)
CORS(app)  # CORS sudah diaktifkan secara global
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:32768/runteam'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Article(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.Text)

class GoldPriceHistory(db.Model):
    __tablename__ = 'gold_price_history'
    date = db.Column(db.Date, primary_key=True)
    price_in_rp = db.Column(db.BigInteger, nullable=False)

def insert_gold_price(price, date=None):
    """Insert a new gold price entry into the database."""
    with app.app_context():
        try:
            if date is None:
                date = dt.today()
            new_entry = GoldPriceHistory(date=date, price_in_rp=price)
            db.session.add(new_entry)
            db.session.commit()
            print(f"Gold price for {date} inserted successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting gold price: {e}")

# Membuat tabel jika belum ada
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Hello, World!"

@app.route('/articles', methods=['GET'])
def get_articles():
    articles = Article.query.all()
    results = [
        {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "image": article.image
        } for article in articles
    ]
    return jsonify(results)

@app.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.get(id)
    if not article:
        return jsonify({"message": "Article not found"}), 404
    
    result = {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "image": article.image
    }
    return jsonify(result)


@app.route('/prices', methods=['GET'])
def get_data():
    prices = GoldPriceHistory.query.all()
    
    # Menyusun daftar tanggal dan harga
    dates = [price.date.strftime("%Y-%m-%d") for price in prices]  # Konversi ke string
    price_values = [int(price.price_in_rp) for price in prices]  # Konversi ke integer

    # Asumsi: prediksi diambil dari 24 hari terakhir
    prediction_values = price_values[-24:]

    # Menentukan tanggal referensi (hari ini)
    today = dt.today()  # Format date
    
    # Menentukan prediksi berdasarkan hari ke depan
    predictionByDay = {}
    prediction_days = [6, 12, 18, 24]  # Hari ke depan dari hari ini
    for idx, day in enumerate(prediction_days):
        future_date = today + timedelta(days=day)  # Menentukan tanggal ke depan
        future_date_str = future_date.strftime("%Y-%m-%d")  # Konversi ke string
        
        if len(prediction_values) >= day:
            predictionByDay[future_date_str] = prediction_values[day - 1]  # Ambil data dari prediksi
    
    # Membentuk output JSON
    result = {
        "date": dates,
        "price": price_values,
        "prediction": prediction_values,
        "predictionByDay": predictionByDay
    }
    
    return jsonify(result)

# get all data 
@app.route('/prices-data', methods=['GET'])
def get_data_data():
    prices = GoldPriceHistory.query.all()
    results = [
        {
            "date": price.date,
            "price": price.price_in_rp,
        } for price in prices
    ]
    return jsonify(results)

# opsional
@app.route('/prediction', methods=['GET'])
def get_prediction():
    days = 12
    if days is None or days <= 0:
        return jsonify({"error": "Parameter 'days' harus berupa angka positif"}), 400

    today = dt.today()
    end_date = today + timedelta(days=days - 1)

    # Query data berdasarkan rentang tanggal
    prices = GoldPriceHistory.query.filter(GoldPriceHistory.date.between(today, end_date)).all()


    results = [
        {
            "date": price.date.strftime('%Y-%m-%d'),
            "price": price.price_in_rp,
        } for price in prices
    ]

    return jsonify(results)


def get_prediction_until(): 
    with app.app_context():
        data = 24

        prices = GoldPriceHistory.query.order_by(GoldPriceHistory.date.asc()).all()

        # Konversi data SQLAlchemy ke bentuk yang bisa digunakan oleh predict_until
        prices_list = [{"date": p.date.strftime("%Y-%m-%d"), "price_in_rp": p.price_in_rp} for p in prices]

        prediction_results = predict_until(n_days=data, prices=prices_list)

        for date, value in prediction_results.items():
            insert_gold_price(value, date)

def delete_gold_prices_from_today():
    """Delete gold price records from today onwards."""
    with app.app_context():
        try:
            today = dt.today()
            GoldPriceHistory.query.filter(GoldPriceHistory.date >= today).delete()
            db.session.commit()
            print(f"Gold prices from {today} onwards deleted successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting gold prices: {e}")


if __name__ == '__main__':
    app.run(debug=True)
