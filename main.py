from extract import fetch_currencies, fetch_coins_info, save_data
import polars as pl
import tqdm

def main():
    currencies = fetch_currencies()
    coin_ids = currencies["coin_id"].to_list()[:20]  # limit to first 20 coins for testing
    coins_list, failed_coins = fetch_coins_info(coin_ids)
    save_data(coins_list, failed_coins, currencies)

if __name__ == "__main__":
    main()
