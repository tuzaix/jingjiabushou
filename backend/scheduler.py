from apscheduler.schedulers.background import BackgroundScheduler
import tasks
import datetime
import logging
import os

logger = logging.getLogger(__name__)

def job_fetch_call_auction():
    now = datetime.datetime.now().time()
    # Check if within 9:15 - 9:30 (buffer slightly)
    start_time = datetime.time(9, 14)
    end_time = datetime.time(9, 31)
    
    if (start_time <= now <= end_time):
        tasks.fetch_call_auction_data()

def job_daily_update():
    logger.info("Starting daily update job")
    tasks.get_all_stock_codes()
    tasks.fetch_yesterday_limit_up()

def job_fetch_jiuyan():
    logger.info("Starting Jiuyan data fetch job")
    tasks.fetch_jiuyan_data()

def init_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule jobs
    
    scheduler.add_job(job_fetch_call_auction, 'cron', day_of_week='mon-fri', hour=9, minute='15-30', second=0)
    scheduler.add_job(job_daily_update, 'cron', day_of_week='mon-fri', hour=9, minute=0)
    
    # Schedule Jiuyan fetch daily at 17:00
    scheduler.add_job(job_fetch_jiuyan, 'cron', day_of_week='mon-fri', hour=17, minute=0)
    
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler
