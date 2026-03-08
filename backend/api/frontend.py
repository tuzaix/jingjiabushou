from flask import Blueprint, jsonify, request
from services.market_service import MarketService
from services.kaipanla_service import KaipanlaService
import logging
import time

frontend_bp = Blueprint('frontend', __name__)
logger = logging.getLogger(__name__)

@frontend_bp.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.path} | Args: {request.args} | Body: {request.get_json(silent=True)}")

@frontend_bp.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info(f"Response: {response.status} | Duration: {duration:.3f}s")
    return response

@frontend_bp.route('/api/index/latest', methods=['GET'])
def get_latest_index():
    """
    获取最新指数数据（如上证指数）。
    参数: date (可选, 默认为最新交易日)
    """
    date_str = request.args.get('date')
    data = KaipanlaService.get_latest_index_data(date_str)
    return jsonify(data)

@frontend_bp.route('/api/call_auction/top_n', methods=['GET'])
def get_top_n():
    """
    获取竞价金额前N名的股票。
    参数: 
        limit (默认20)
        date (可选, 默认为最新交易日)
        time (可选, 默认为最新时间)
    """
    limit = request.args.get('limit', 20, type=int)
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    
    logger.debug(f"Querying Top N: limit={limit}, date={date_str}, time={time_str}")
    data = MarketService.get_top_n_call_auction(limit=limit, date_str=date_str, time_str=time_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/yesterday_limit_up', methods=['GET'])
def get_yesterday_limit_up():
    """
    获取昨日涨停股票及其今日表现。
    参数: 
        date (可选, 默认为最新交易日)
        mode: 'performance' 获取昨日涨停股在今日的表现; 否则获取昨日涨停列表
    """
    date_str = request.args.get('date')
    mode = request.args.get('mode')
    
    if mode == 'performance':
        logger.debug(f"Querying Yesterday Limit Up Performance: target_date={date_str}")
        data = MarketService.get_yesterday_limit_up_performance(target_date_str=date_str)
    else:
        logger.debug(f"Querying Yesterday Limit Up: date={date_str}")
        data = MarketService.get_yesterday_limit_up(date_str=date_str)

    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/call_auction/limit_up_925', methods=['GET'])
def get_limit_up_925():
    """
    获取9:25竞价涨停的股票。
    参数: date (可选, 默认为最新交易日)
    """
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Limit Up at 9:25: date={date_str}")
    data = MarketService.get_limit_up_at_925(date_str=date_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/call_auction/limit_down_925', methods=['GET'])
def get_limit_down_925():
    """
    获取9:25竞价跌停的股票。
    参数: date (可选, 默认为最新交易日)
    """
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Limit Down at 9:25: date={date_str}")
    data = MarketService.get_limit_down_at_925(date_str=date_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/call_auction/abnormal_movement_925', methods=['GET'])
def get_abnormal_movement_925():
    """
    获取9:25竞价异动股票（9:15-9:25之间涨幅变化大的股票）。
    参数: 
        date (可选, 默认为最新交易日)
        limit (默认10)
    """
    date_str = request.args.get('date')
    limit = request.args.get('limit', 10, type=int)
    
    logger.debug(f"Querying Abnormal Movement at 9:25: date={date_str}, limit={limit}")
    data = MarketService.get_abnormal_movement_at_925(date_str=date_str, limit=limit)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/call_auction/ranking', methods=['GET'])
def get_auction_ranking():
    """
    获取指定时间范围内的竞价排名。
    参数:
        start_time, end_time (时间范围)
        limit (默认20)
        date (可选)
    """
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    limit = request.args.get('limit', 20, type=int)
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Auction Ranking: start={start_time}, end={end_time}, limit={limit}, date={date_str}")
    data = MarketService.get_ranking_by_time_range(start_time, end_time, limit, date_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@frontend_bp.route('/api/market/sentiment_925', methods=['GET'])
def get_market_sentiment_925():
    """
    获取9:25的市场情绪指标（如涨停数、跌停数、成交额等）。
    参数: date (可选, 默认为最新交易日)
    """
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Market Sentiment 9:25: date={date_str}")
    data = MarketService.get_market_sentiment_925(date_str=date_str)
    return jsonify(data)

@frontend_bp.route('/api/market/trading_days', methods=['GET'])
def get_trading_days():
    """
    获取交易日列表。
    """
    days = MarketService.get_trading_days()
    return jsonify(days)
