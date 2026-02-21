import datetime
import logging
from services.market_service import MarketService

logger = logging.getLogger(__name__)

def get_current_or_previous_trading_day():
    """
    Returns the current date if it is a trading day.
    Otherwise, returns the most recent previous trading day.
    Format: 'YYYY-MM-DD'
    """
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    try:
        # Get list of trading days (end_date inclusive)
        # Assuming get_trading_days returns sorted list of strings
        trading_days = MarketService.get_trading_days(end_date=today)
        
        if not trading_days:
            logger.warning("No trading days found from MarketService. Returning today.")
            return today
            
        if today in trading_days:
            return today
        else:
            # Today is not a trading day, return the last one in the list
            last_trading_day = trading_days[-1]
            logger.info(f"Today {today} is not a trading day. Using previous trading day: {last_trading_day}")
            return last_trading_day
            
    except Exception as e:
        logger.error(f"Error determining trading day: {e}. Fallback to today.")
        return today
