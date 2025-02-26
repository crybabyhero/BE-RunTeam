import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
import numpy as np
import datetime
from scipy.ndimage import gaussian_filter1d
 
def predict_until(n_days: int, prices):
    df = pd.DataFrame([{"price_in_rp": price['price_in_rp']} for price in prices])
    print(df.head())
    # Load model and transformer
    model = joblib.load("./models/Forcasting.pkl")
    transform = joblib.load("./models/scaler.pkl")

    # Normalize data
    df_trans = transform.fit_transform(df[['price_in_rp']].to_numpy().reshape(-1, 1))
    df_trans = pd.DataFrame(df_trans, columns=['price_in_rp'])

    # Train and test split
    train, test = train_test_split(df_trans, test_size=0.2, shuffle=False)
    sequence_length = 6
    train_X, train_y, test_X, test_y = [], [], [], []

    for i in range(len(train) - sequence_length):
        train_X.append(train[i:i+sequence_length])
        train_y.append(train.iloc[i+sequence_length])

    for i in range(len(test) - sequence_length):
        test_X.append(test[i:i+sequence_length])
        test_y.append(test.iloc[i+sequence_length])

    train_X, train_y = np.array(train_X), np.array(train_y)
    test_X, test_y = np.array(test_X), np.array(test_y)

    # Forecasting
    forecasted_values = []
    current_input = test_X[-1]
    for day in range(n_days):
        forecast = model.predict(np.array([current_input]))[0][0]
        forecasted_values.append(forecast)
        current_input = np.roll(current_input, shift=-1)
        current_input[-1] = forecast
    
    forecasted_values = transform.inverse_transform(np.array(forecasted_values).reshape(-1, 1))
    smoothed_forecast = gaussian_filter1d(forecasted_values.flatten(), sigma=2)

    # Mapping forecasted values to dates
    start_date = datetime.date.today()
    forecast_dates = [start_date + datetime.timedelta(days=i) for i in range(0, n_days + 1)]
    forecast_dict = {date.strftime('%Y-%m-%d'): float(value) for date, value in zip(forecast_dates, forecasted_values.flatten())}
    
    return forecast_dict

def predict(n_days: int, prices):
    df = pd.DataFrame([{"price_in_rp": price['price_in_rp']} for price in prices])
    print(df.head())
    # Load model and transformer
    model = joblib.load("./models/Forcasting.pkl")
    transform = joblib.load("./models/scaler.pkl")

    # Normalize data
    df_trans = transform.fit_transform(df[['price_in_rp']].to_numpy().reshape(-1, 1))
    df_trans = pd.DataFrame(df_trans, columns=['price_in_rp'])


    train, test = train_test_split(df_trans, test_size=0.2, shuffle=False)
    sequence_length = 6
    train_X, train_y, test_X, test_y = [], [], [], []

    for i in range(len(train) - sequence_length):
        train_X.append(train[i:i+sequence_length])
        train_y.append(train.iloc[i+sequence_length])

    for i in range(len(test) - sequence_length):
        test_X.append(test[i:i+sequence_length])
        test_y.append(test.iloc[i+sequence_length])

    train_X, train_y = np.array(train_X), np.array(train_y)
    test_X, test_y = np.array(test_X), np.array(test_y)

    current_input = test_X[-1]
    forecast_value = None

    for day in range(1, n_days + 1):
        forecast = model.predict(np.array([current_input]))[0][0]
        current_input = np.roll(current_input, shift=-1)
        current_input[-1] = forecast
        if day == n_days:
            forecast_value = forecast

    if forecast_value is not None:
        forecast_value = transform.inverse_transform(np.array([[forecast_value]]))[0][0]

    forecast_date = datetime.date.today() + datetime.timedelta(days=n_days - 1)
    return {forecast_date.strftime('%Y-%m-%d'): float(forecast_value)}
