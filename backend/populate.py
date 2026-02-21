import tasks
import logging

if __name__ == "__main__":
    print("Fetching all stock codes...")
    tasks.get_all_stock_codes()
    print("Fetching yesterday limit up...")
    tasks.fetch_yesterday_limit_up()
    print("Done.")
