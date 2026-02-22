from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
import tasks
import datetime
import logging
import os
import time
from utils.date_utils import get_current_or_previous_trading_day

logger = logging.getLogger(__name__)
    # Configure logging if running standalone
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

def job_fetch_call_auction():
    '''
    定时获取东方财富的竞价数据 - runs every 10 seconds from 9:15 to 9:30
    '''
    now = datetime.datetime.now().time()
    # Check if within 9:15 - 9:30 (buffer slightly)
    start_time = datetime.time(9, 14)
    end_time = datetime.time(9, 31)
    trading_day = get_current_or_previous_trading_day()

    if (start_time <= now <= end_time):
        # Only fetch if today matches the trading day, OR if we want to allow re-fetching past data?
        # If today is Saturday, trading_day is Friday.
        # If we run this on Saturday 9:20, we fetch Friday's data and save as Friday.
        # This seems acceptable.
        logger.info(f"Executing job_fetch_call_auction for date: {trading_day}")
        tasks.run_update_call_auction_data(date_str=trading_day)

def job_update_stock_list():
    '''
    定时获取东方财富的竞价请求，解析里面的--data-raw的股票列表到数据库，3天更新一次
    '''
    logger.info("Starting daily update job")
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Executing job_update_stock_list for date: {trading_day}")
    
    tasks.run_update_stock_list()

def job_fetch_limit_up():
    '''
    每天定时获取韭研按照题材概念分类的涨停数据
    '''
    logger.info("Starting Jiuyan data fetch job")
    trading_day = get_current_or_previous_trading_day()
    logger.info(f"Executing job_fetch_jiuyan for date: {trading_day}")
    
    tasks.run_update_yesterday_limit_up(date_str=trading_day)

def start_scheduler(blocking=False):
    if blocking:
        scheduler = BlockingScheduler()
    else:
        scheduler = BackgroundScheduler()
        
    # 定时获取东方财富的竞价数据 - runs every 10 seconds from 9:15 to 9:30
    scheduler.add_job(job_fetch_call_auction, 'cron', day_of_week='mon-fri', hour=9, minute='15-30', second='*/10')

    # 定时获取东方财富的竞价请求，解析里面的--data-raw的股票列表到数据库，3天更新一次
    scheduler.add_job(job_update_stock_list, 'cron', day_of_week='mon-fri', hour=9, minute=0)
    
    # Schedule Jiuyan fetch daily at 18:00
    # 每天定时获取韭研按照题材概念分类的涨停数据
    scheduler.add_job(job_fetch_limit_up, 'cron', day_of_week='mon-fri', hour=18, minute=0)
    
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

    logger.info("Starting Scheduler Service...")
    start_scheduler(blocking=True)
