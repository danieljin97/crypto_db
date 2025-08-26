import os 
import polars as pl

from extract import fetch_currencies, fetch_coins_info, save_data
from qa import qa_report

import tqdm
from datetime import date

TODAY = date.today().isoformat()

def main():
    currencies = fetch_currencies()
    coin_ids = currencies["coin_id"].to_list()[:20]  # limit to first 20 coins for testing
    coins_list, failed_coins = fetch_coins_info(coin_ids)
    save_data(coins_list, failed_coins, currencies)

    # QA report
    files = os.listdir("data")
    for file in files: 
        if file.endswith(".csv") and file != "failed_coins.csv":
            df = pl.read_csv(os.path.join("data", file))

            # ingestion time on all tables 
            df = df.with_columns(pl.lit(TODAY).alias("ingestion_date"))
            # save again with ingestion date
            output_path = f"data/{file}"
            df.write_csv(output_path)

            qa_report(df, file, log_to_file=True)

if __name__ == "__main__":
    main()
