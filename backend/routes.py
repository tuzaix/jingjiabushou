from flask import Blueprint, jsonify, request
from services.market_service import MarketService
from services.sync_service import SyncService
from services.jiuyan_service import JiuyanService
from services.eastmoney_service import EastmoneyService
from services.kaipanla_service import KaipanlaService
import tasks
import logging
import time

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.path} | Args: {request.args} | Body: {request.get_json(silent=True)}")

@api_bp.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info(f"Response: {response.status} | Duration: {duration:.3f}s")
    return response

@api_bp.route('/api/call_auction/top_n', methods=['GET'])
def get_top_n():
    limit = request.args.get('limit', 20, type=int)
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    
    logger.debug(f"Querying Top N: limit={limit}, date={date_str}, time={time_str}")
    data = MarketService.get_top_n_call_auction(limit=limit, date_str=date_str, time_str=time_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@api_bp.route('/api/yesterday_limit_up', methods=['GET'])
def get_yesterday_limit_up():
    date_str = request.args.get('date')
    
    # Check if we should use the new performance logic (limit up prev day + auction today)
    # The frontend will likely pass the *selected* date (today/target)
    # But existing calls might still expect the old behavior?
    # Actually, the user requirement implies replacing the old view with the new view.
    # So we can just switch the implementation.
    # OR, we can add a query param `mode=performance`.
    
    mode = request.args.get('mode')
    
    if mode == 'performance':
        logger.debug(f"Querying Yesterday Limit Up Performance: target_date={date_str}")
        data = MarketService.get_yesterday_limit_up_performance(target_date_str=date_str)
    else:
        logger.debug(f"Querying Yesterday Limit Up: date={date_str}")
        data = MarketService.get_yesterday_limit_up(date_str=date_str)
        
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@api_bp.route('/api/call_auction/limit_up_925', methods=['GET'])
def get_limit_up_925():
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Limit Up at 9:25: date={date_str}")
    data = MarketService.get_limit_up_at_925(date_str=date_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@api_bp.route('/api/call_auction/ranking', methods=['GET'])
def get_auction_ranking():
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    limit = request.args.get('limit', 20, type=int)
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Auction Ranking: start={start_time}, end={end_time}, limit={limit}, date={date_str}")
    data = MarketService.get_ranking_by_time_range(start_time, end_time, limit, date_str)
    logger.debug(f"Found {len(data)} records")
    return jsonify(data)

@api_bp.route('/api/market/sentiment_925', methods=['GET'])
def get_market_sentiment_925():
    date_str = request.args.get('date')
    
    logger.debug(f"Querying Market Sentiment 9:25: date={date_str}")
    data = MarketService.get_market_sentiment_925(date_str=date_str)
    return jsonify(data)

@api_bp.route('/api/market/trading_days', methods=['GET'])
def get_trading_days():
    """
    Get list of trading days.
    """
    days = MarketService.get_trading_days()
    return jsonify(days)

@api_bp.route('/api/upload/yesterday_limit_up', methods=['POST'])
def upload_yesterday_limit_up():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    date_str = request.form.get('date')
    
    try:
        count = SyncService.import_yesterday_limit_up_excel(file, date_str)
        return jsonify({"message": f"Successfully imported {count} records", "count": count})
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/admin/jiuyan/config', methods=['GET', 'POST'])
def jiuyan_config():
    if request.method == 'GET':
        config = JiuyanService.get_config()
        return jsonify(config or {})
    else:
        data = request.get_json()
        curl_command = data.get('curl')
        if not curl_command:
            return jsonify({"error": "Missing curl command"}), 400
            
        success, message = JiuyanService.update_config(curl_command)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500

@api_bp.route('/api/admin/jiuyan/sync', methods=['POST'])
def jiuyan_sync():
    data = request.get_json() or {}
    date_str = data.get('date')
    success, result = JiuyanService.fetch_data(date_str)
    if success:
        return jsonify({"message": "Fetch successful", "data": result})
    else:
        return jsonify({"error": result}), 500

@api_bp.route('/api/admin/jiuyan/test', methods=['POST'])
def jiuyan_test():
    """
    Test fetching data from Jiuyan using the configured cURL command.
    """
    success, result = JiuyanService.fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@api_bp.route('/api/admin/eastmoney/config', methods=['GET', 'POST'])
def eastmoney_config():
    if request.method == 'GET':
        config = EastmoneyService.get_config()
        return jsonify(config or {})
    else:
        data = request.get_json()
        curl_command = data.get('curl')
        if not curl_command:
            return jsonify({"error": "Missing curl command"}), 400
            
        success, message = EastmoneyService.update_config(curl_command)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500

@api_bp.route('/api/admin/eastmoney/test', methods=['POST'])
def eastmoney_test():
    """
    Test fetching data from Eastmoney using the configured cURL command.
    """
    success, result = EastmoneyService.fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@api_bp.route('/api/admin/kaipanla/config', methods=['GET', 'POST'])
def kaipanla_config():
    if request.method == 'GET':
        config = KaipanlaService.get_config()
        return jsonify(config or {})
    else:
        data = request.get_json()
        curl_command = data.get('curl')
        if not curl_command:
            return jsonify({"error": "Missing curl command"}), 400
            
        success, message = KaipanlaService.update_config(curl_command)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500

@api_bp.route('/api/admin/kaipanla/test', methods=['POST'])
def kaipanla_test():
    """
    Test fetching data from Kaipanla using the configured cURL command.
    """
    success, result = KaipanlaService.fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

# Manual trigger for testing
@api_bp.route('/api/test/fetch_call_auction', methods=['POST'])
def trigger_fetch():
    logger.info("Triggering manual fetch of call auction data")
    tasks.fetch_call_auction_data()
    return jsonify({"status": "triggered"})

@api_bp.route('/api/test/init_data', methods=['POST'])
def init_data():
    logger.info("Triggering manual init of stock data")
    tasks.get_all_stock_codes()
    tasks.fetch_yesterday_limit_up()
    return jsonify({"status": "initialized"})
