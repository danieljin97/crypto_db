import os
import requests
import polars as pl
import json
import time
import tqdm

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()
# Load API key from environment variables
API_KEY = os.getenv("API_KEY")

today_date = time.strftime("%Y-%m-%d")


headers = {
    "accept": "application/json",
    "x-cg-demo-api-key": API_KEY,
    "date": f"{today_date}"  # Example date, adjust as needed
}


session = requests.Session()

retries = Retry(
    total=5,                # up to 5 tries total
    backoff_factor=2,       # exponential backoff: 2s, 4s, 8s, 16s...
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


def get_data(url, headers, params=None): 
    """ 

    Fetches data from CoinGecko API with retry logic for error handling.

    """
    try:
        response = session.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # print(f"Data fetched successfully from {url}")
            return response.json()
        
        elif response.status_code == 429:  # Too Many Requests
            print("Rate limit exceeded. Retrying after 5s...")
            time.sleep(5)
            return get_data(url, headers, params)  # recursive retry
        
        else:
            raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def fetch_currencies():
    """ 
    Fetches the list of all cryptocurrencies ids from CoinGecko API.
    Returns a Polars DataFrame with coin_id, coin_name, and coin_symbol.
    """
    # Fetching the list of all coins from CoinGecko API
    response = get_data("https://api.coingecko.com/api/v3/coins/list", headers=headers)
    currencies = pl.DataFrame(response)

    currencies = currencies.select(
        pl.col("id").alias("coin_id"),
        pl.col("name").alias("coin_name"),
        pl.col("symbol").alias("coin_symbol")
    )   
    return currencies



def fetch_single_coin(coin_id):
    """
    query all the metadata (image, websites, socials, description, contract address, etc.) and market data (price, ATH, exchange tickers, etc.) 
    """
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        coin_data = get_data(url, headers)
        if coin_data:
            return {
                "coin_id": coin_data.get("id"),
                "coin_symbol": coin_data.get("symbol"),
                "coin_name": coin_data.get("name"),
                "asset_platform_id": coin_data.get("asset_platform_id"),
                "block_time_in_minutes": coin_data.get("block_time_in_minutes"),
                "hashing_algorithm": coin_data.get("hashing_algorithm"),
                #"links_homepage": coin_data["links"].get("homepage"),
                "links_twitter": coin_data["links"].get("twitter_screen_name"),
                "links_reddit": coin_data["links"].get("subreddit_url"),
                "country_origin": coin_data.get("country_origin"),
                "genesis_date": coin_data.get("genesis_date"),
                "sentiment_votes_up_percentage": coin_data.get("sentiment_votes_up_percentage"),
                "sentiment_votes_down_percentage": coin_data.get("sentiment_votes_down_percentage"),
                "watchlist_portfolio_users": coin_data.get("watchlist_portfolio_users"),
                "market_cap_rank": coin_data.get("market_cap_rank"),
                "market_current_price": coin_data["market_data"]["current_price"].get("usd"),
                "market_ath": coin_data["market_data"]["ath"].get("usd"),
                "market_ath_date": coin_data["market_data"]["ath_date"].get("usd"),
                "market_atl": coin_data["market_data"]["atl"].get("usd"),
                "market_atl_date": coin_data["market_data"]["atl_date"].get("usd"),
                "market_market_cap": coin_data["market_data"]["market_cap"].get("usd"),
                "market_fully_diluted_valuation": coin_data["market_data"]["fully_diluted_valuation"].get("usd"),
                "market_total_volume": coin_data["market_data"]["total_volume"].get("usd"),
                "market_high_24h": coin_data["market_data"]["high_24h"].get("usd"),
                "market_low_24h": coin_data["market_data"]["low_24h"].get("usd"),
                "market_price_change_24h": coin_data["market_data"].get("price_change_24h"),
                "market_price_change_percentage_24h": coin_data["market_data"].get("price_change_percentage_24h"),
                "market_price_change_percentage_7d": coin_data["market_data"].get("price_change_percentage_7d"),
                "market_price_change_percentage_14d": coin_data["market_data"].get("price_change_percentage_14d"),
                "market_price_change_percentage_30d": coin_data["market_data"].get("price_change_percentage_30d"),
                "market_price_change_percentage_60d": coin_data["market_data"].get("price_change_percentage_60d"),
                "market_price_change_percentage_200d": coin_data["market_data"].get("price_change_percentage_200d"),
                "market_price_change_percentage_1y": coin_data["market_data"].get("price_change_percentage_1y"),
                "market_market_cap_change_24h": coin_data["market_data"].get("market_cap_change_24h"),
                "market_market_cap_change_percentage_24h": coin_data["market_data"].get("market_cap_change_percentage_24h"),
                "market_total_supply": coin_data["market_data"].get("total_supply"),
                "market_max_supply": coin_data["market_data"].get("max_supply"),
                "market_circulating_supply": coin_data["market_data"].get("circulating_supply"),
                "market_last_updated": coin_data["market_data"].get("last_updated"),
                "dev_forks": coin_data["developer_data"].get("forks"),
                "dev_stars": coin_data["developer_data"].get("stars"),
                "dev_subscribers": coin_data["developer_data"].get("subscribers"),
                "dev_total_issues": coin_data["developer_data"].get("total_issues"),
                "dev_closed_issues": coin_data["developer_data"].get("closed_issues"),
                "dev_pull_requests_merged": coin_data["developer_data"].get("pull_requests_merged"),
                "dev_pull_requests_contributors": coin_data["developer_data"].get("pull_requests_contributors"),
                "dev_commit_count_4_weeks": coin_data["developer_data"].get("commit_count_4_weeks")
            }
        else:
            return None
    except Exception as e:
        print(f"Error fetching coin {coin_id}: {e}")
        return None
    

def fetch_coins_info(coin_ids, nax_workers = 1):
    
    coins_list = []
    failed_coins = []


    with ThreadPoolExecutor(max_workers=1) as executor:
    # Map coin IDs to futures
    # Future object is a placeholder for the result that will come later.
        futures = {executor.submit(fetch_single_coin, coin_id): coin_id for coin_id in coin_ids}

        #as_completed(futures) yields futures as they finish, not in the original order.
        for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
            coin_id = futures[future]

            result = future.result()
            if result:
                coins_list.append(result)
            else:
                failed_coins.append(coin_id)
    
    return coins_list, failed_coins


def save_data(coins_list, failed_coins, currencies):
    """

    Save the fetched data to CSV files.

    """ 

    failed_df = pl.DataFrame({"failed_coin_ids": failed_coins})
    failed_df.write_csv("data/failed_coins.csv")


    df_coins_data= pl.DataFrame(coins_list)
    df_coins_data.write_csv("data/coins_data.csv")
    
    df_currencies = pl.DataFrame(currencies)
    df_currencies.write_csv("data/currencies.csv")


    print(f"Fetched {len(df_coins_data)} coins, failed {len(failed_coins)} coins")


