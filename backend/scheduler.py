from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
import tasks
import datetime
import logging
import os
import time
from utils.date_utils import get_current_or_previous_trading_day

logger = logging.getLogger(__name__)

def job_fetch_call_auction():
    now = datetime.datetime.now().time()
    # Check if within 9:15 - 9:30 (buffer slightly)
    start_time = datetime.time(9, 14)
    end_time = datetime.time(9, 31)
    
    if (start_time <= now <= end_time):
        trading_day = get_current_or_previous_trading_day()
        # Only fetch if today matches the trading day, OR if we want to allow re-fetching past data?
        # If today is Saturday, trading_day is Friday.
        # If we run this on Saturday 9:20, we fetch Friday's data and save as Friday.
        # This seems acceptable.
        tasks.fetch_call_auction_data(date_str=trading_day)

def job_update_stock_list():
    logger.info("Starting daily update job")
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Executing job_update_stock_list for date: {trading_day}")
    
    tasks.get_all_stock_codes()

def job_fetch_jiuyan():
    logger.info("Starting Jiuyan data fetch job")
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Executing job_fetch_jiuyan for date: {trading_day}")
    
    tasks.fetch_jiuyan_data(date_str=trading_day)

def job_fetch_eastmoney_call_auction():
    """
    Fetch Eastmoney call auction data.
    Runs every few seconds during 9:15-9:30.
    """
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Executing job_fetch_eastmoney_call_auction for date: {trading_day}")
    
    tasks.fetch_eastmoney_call_auction(dry_run=True, date_str=trading_day)

def start_scheduler(blocking=False):
    if blocking:
        scheduler = BlockingScheduler()
    else:
        scheduler = BackgroundScheduler()
        
    # Schedule jobs
    
    # Existing job (maybe disable or keep?)
    # scheduler.add_job(job_fetch_call_auction, 'cron', day_of_week='mon-fri', hour=9, minute='15-30', second=0)
    
    # New Eastmoney job - runs every 10 seconds from 9:15 to 9:30
    scheduler.add_job(job_fetch_eastmoney_call_auction, 'cron', day_of_week='mon-fri', hour=9, minute='15-30', second='*/10')

    # 定时获取东方财富的竞价请求，解析里面的--data-raw的股票列表到数据库，3天更新一次
    scheduler.add_job(job_update_stock_list, 'cron', day_of_week='mon-fri', hour=9, minute=0)
    
    # Schedule Jiuyan fetch daily at 18:00
    # 每天定时获取韭研按照题材概念分类的涨停数据
    scheduler.add_job(job_fetch_jiuyan, 'cron', day_of_week='mon-fri', hour=18, minute=0)
    
    try:
        scheduler.start()
        logger.info(f"Scheduler started (blocking={blocking})")
    except (KeyboardInterrupt, SystemExit):
        pass
        
    return scheduler

def init_scheduler():
    # Deprecated: use start_scheduler(blocking=False) instead
    return start_scheduler(blocking=False)

if __name__ == "__main__":
    # Configure logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("scheduler.log"),
            logging.StreamHandler()
        ]
    )
    logger.info("Starting Scheduler Service...")
    start_scheduler(blocking=True)
