from flask import Blueprint, jsonify, request
from services.jiuyan_service import JiuyanService
from services.eastmoney_service import EastmoneyService
from services.kaipanla_service import KaipanlaService
from services.sync_service import SyncService
import tasks
import logging
import time

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.path} | Args: {request.args} | Body: {request.get_json(silent=True)}")

@admin_bp.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logger.info(f"Response: {response.status} | Duration: {duration:.3f}s")
    return response

@admin_bp.route('/api/upload/yesterday_limit_up', methods=['POST'])
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

@admin_bp.route('/api/admin/jiuyan/config', methods=['GET', 'POST'])
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

@admin_bp.route('/api/admin/jiuyan/sync', methods=['POST'])
def jiuyan_sync():
    data = request.get_json() or {}
    date_str = data.get('date')
    success, result = JiuyanService.fetch_data(date_str)
    if success:
        return jsonify({"message": "Fetch successful", "data": result})
    else:
        return jsonify({"error": result}), 500

@admin_bp.route('/api/admin/jiuyan/test', methods=['POST'])
def jiuyan_test():
    """
    Test fetching data from Jiuyan using the configured cURL command.
    """
    success, result = JiuyanService.test_config_fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@admin_bp.route('/api/admin/eastmoney/config', methods=['GET', 'POST'])
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

@admin_bp.route('/api/admin/eastmoney/test', methods=['POST'])
def eastmoney_test():
    """
    Test fetching data from Eastmoney using the configured cURL command.
    """
    success, result = EastmoneyService.test_config_fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@admin_bp.route('/api/admin/kaipanla/config', methods=['GET', 'POST'])
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

@admin_bp.route('/api/admin/kaipanla/test', methods=['POST'])
def kaipanla_test():
    """
    Test fetching data from Kaipanla using the configured cURL command.
    """
    success, result = KaipanlaService.fetch_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@admin_bp.route('/api/admin/kaipanla/volume/config', methods=['GET', 'POST'])
def kaipanla_volume_config():
    if request.method == 'GET':
        config = KaipanlaService.get_volume_config()
        return jsonify(config or {})
    else:
        data = request.get_json()
        curl_command = data.get('curl')
        if not curl_command:
            return jsonify({"error": "Missing curl command"}), 400
            
        success, message = KaipanlaService.update_volume_config(curl_command)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500

@admin_bp.route('/api/admin/kaipanla/volume/test', methods=['POST'])
def kaipanla_volume_test():
    """
    Test fetching volume data from Kaipanla using the configured cURL command.
    """
    success, result = KaipanlaService.fetch_volume_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

@admin_bp.route('/api/admin/kaipanla/index/config', methods=['GET', 'POST'])
def kaipanla_index_config():
    if request.method == 'GET':
        config = KaipanlaService.get_index_config()
        return jsonify(config or {})
    else:
        data = request.get_json()
        curl_command = data.get('curl')
        if not curl_command:
            return jsonify({"error": "Missing curl command"}), 400
            
        success, message = KaipanlaService.update_index_config(curl_command)
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 500

@admin_bp.route('/api/admin/kaipanla/index/test', methods=['POST'])
def kaipanla_index_test():
    """
    Test fetching index data from Kaipanla using the configured cURL command.
    """
    success, result = KaipanlaService.fetch_index_data()
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": result}), 500

# Manual trigger for testing
@admin_bp.route('/api/test/fetch_call_auction', methods=['POST'])
def trigger_fetch():
    logger.info("Triggering manual fetch of call auction data")
    tasks.fetch_call_auction_data()
    return jsonify({"status": "triggered"})

@admin_bp.route('/api/test/init_data', methods=['POST'])
def init_data():
    logger.info("Triggering manual init of stock data")
    tasks.get_all_stock_codes()
    tasks.fetch_yesterday_limit_up()
    return jsonify({"status": "initialized"})
