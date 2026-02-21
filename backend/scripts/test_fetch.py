import requests
import json
import datetime

url = "https://apphis.longhuvip.com/w1/api/index.php"

headers = {
    "Host": "apphis.longhuvip.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Accept": "*/*",
    "User-Agent": "lhb/5.21.1 (com.kaipanla.www; build:1; iOS 17.6.1) Alamofire/4.9.1",
    "Accept-Language": "zh-Hans-US;q=1.0, en-US;q=0.9, zh-Hant-US;q=0.8"
}

# Fetch for 2026-02-20
date_str = "2026-02-13"

data = {
    "Day": date_str,
    "Filter": "0",
    "FilterGem": "0",
    "FilterMotherboard": "0",
    "FilterTIB": "0",
    "Index": "0",
    "Is_st": "1",
    "Order": "1",
    "PhoneOSNew": "2",
    "PidType": "8",
    "Type": "18",
    "VerSion": "5.21.0.1",
    "a": "HisDaBanList",
    "apiv": "w42",
    "c": "HisHomeDingPan",
    "st": "20"
}

try:
    print(f"Fetching for {date_str}...")
    response = requests.post(url, headers=headers, data=data)
    data = response.json()
    if 'list' in data and len(data['list']) > 0:
        print(f"Found {len(data['list'])} items.")
        for j in range(min(3, len(data['list']))):
            item = data['list'][j]
            print(f"\nItem {j}:")
            for i, val in enumerate(item):
                print(f"{i}: {val}")
    else:
        print("No data found or structure different")
        print(data)
except Exception as e:
    print(e)
