import os
import requests
import polars as pl
import json

from dotenv import load_dotenv

load_dotenv()
 
API_KEY = os.getenv("API_KEY")

URL_CURRENCIES = "https://api.coingecko.com/api/v3/coins/list"

headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": API_KEY
}

response = requests.get(URL_CURRENCIES, headers=headers)
currencies = pl.DataFrame(response.json())

currencies = currencies.select(
    pl.col("id").alias("currency_id"),
    pl.col("name").alias("currency_name"),
    pl.col("symbol").alias("currency_symbol")
)   

print(currencies)