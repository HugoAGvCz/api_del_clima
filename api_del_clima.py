import openmeteo_requests

import os
import requests_cache
import pandas as pd
import schedule
import time
from retry_requests import retry
from datetime import datetime

def consulta_api():
    dir_codigo = os.path.dirname(os.path.realpath(__file__)) 
    carpeta = 'datos_clima'
    current_date = datetime.now().strftime('%Y-%m-%d')
    folder = os.path.join(dir_codigo, carpeta, current_date)
    os.makedirs(folder, exist_ok=True)
    
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"	
    params = {
        "latitude": 20.659698,
        "longitude": -103.349609,
        "hourly": ["temperature_2m", "precipitation_probability", "wind_speed_10m", "uv_index", "uv_index_clear_sky", "is_day", "sunshine_duration", "direct_radiation"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max", "precipitation_probability_max"],
        "timezone": "auto",
        "past_days": 31,
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
    hourly_uv_index = hourly.Variables(3).ValuesAsNumpy()
    hourly_uv_index_clear_sky = hourly.Variables(4).ValuesAsNumpy()
    hourly_is_day = hourly.Variables(5).ValuesAsNumpy()
    hourly_sunshine_duration = hourly.Variables(6).ValuesAsNumpy()
    hourly_direct_radiation = hourly.Variables(7).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["uv_index"] = hourly_uv_index
    hourly_data["uv_index_clear_sky"] = hourly_uv_index_clear_sky
    hourly_data["is_day"] = hourly_is_day
    hourly_data["sunshine_duration"] = hourly_sunshine_duration
    hourly_data["direct_radiation"] = hourly_direct_radiation

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    print(hourly_dataframe)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_sunrise = daily.Variables(3).ValuesAsNumpy()
    daily_sunset = daily.Variables(4).ValuesAsNumpy()
    daily_daylight_duration = daily.Variables(5).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(6).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(7).ValuesAsNumpy()
    daily_uv_index_clear_sky_max = daily.Variables(8).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(9).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["weather_code"] = daily_weather_code
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["sunrise"] = daily_sunrise
    daily_data["sunset"] = daily_sunset
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["sunshine_duration"] = daily_sunshine_duration
    daily_data["uv_index_max"] = daily_uv_index_max
    daily_data["uv_index_clear_sky_max"] = daily_uv_index_clear_sky_max
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max

    daily_dataframe = pd.DataFrame(data = daily_data)
    print(daily_dataframe)
 
    hourly_dataframe.to_csv(os.path.join(folder, f'hourly_data_{current_date}.csv'), index=False)
    daily_dataframe.to_csv(os.path.join(folder, f'daily_data_{current_date}.csv'), index=False)

def comprobar_dia():
    # Día 9 de cada mes
    if datetime.now().day == 9:
        consulta_api()
    # Estas lineas solamente son para probar el programa 
    # else:
    #     print(datetime.now().day)
    #     print("Hoy no es el día 9, la consulta a la API no se realizará.")

# Modifica la hora para hacer pruebas. En caso de que no, dejar la hora como 00.00
schedule.every().day.at("00:00").do(comprobar_dia)

while True:
    # Run pending tasks
    schedule.run_pending()
    time.sleep(1)