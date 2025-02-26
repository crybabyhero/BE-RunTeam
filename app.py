from flask import Flask, request, jsonify
from models.model import predict, predict_until
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import date as dt

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
def get_article_detail(id):
    article = Article.query.get_or_404(id)
    result = {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "image": article.image
    }
    return jsonify(result)


@app.route('/predict-until', methods=['POST'])
def get_prediction_until():
    data = request.json.get("day")
    if not isinstance(data, int):
        return jsonify({"error": "Invalid input: 'day' must be an integer"}), 400

    prices = GoldPriceHistory.query.order_by(GoldPriceHistory.date.asc()).all()
    
    # Konversi data SQLAlchemy ke bentuk yang bisa digunakan oleh predict_until
    prices_list = [{"date": p.date.strftime("%Y-%m-%d"), "price_in_rp": p.price_in_rp} for p in prices]

    result = predict_until(n_days=data, prices=prices_list)
    return jsonify(result)

@app.route('/predict', methods=['POST'])
def get_prediction():
    data = request.json.get("day")
    if not isinstance(data, int):
        return jsonify({"error": "Invalid input: 'day' must be an integer"}), 400

    prices = GoldPriceHistory.query.order_by(GoldPriceHistory.date.asc()).all()
    
    # Konversi data ke bentuk JSON-friendly
    prices_list = [{"date": p.date.strftime("%Y-%m-%d"), "price_in_rp": p.price_in_rp} for p in prices]

    result = predict(data, prices=prices_list)
    return jsonify(result)

@app.route('/newprice', methods=['GET'])
def get_newprice():
    latest_price = GoldPriceHistory.query.order_by(GoldPriceHistory.date.desc()).first()
    
    if latest_price is None:
        return jsonify({"error": "No price data available"}), 404
    
    result = {
        "date": latest_price.date.strftime("%Y-%m-%d"),
        "price_in_rp": latest_price.price_in_rp
    }
    
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
