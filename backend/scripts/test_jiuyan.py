import requests
import json

url = "https://app.jiuyangongshe.com/jystock-app/api/v1/action/field"

payload = json.dumps({
  "date": "2026-02-13",
  "pc": 1
})

headers = {
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
  'Connection': 'keep-alive',
  'Content-Type': 'application/json',
  'Origin': 'https://www.jiuyangongshe.com',
  'Referer': 'https://www.jiuyangongshe.com/',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-site',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
  'platform': '3',
  'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Windows"',
  'timestamp': '1771756657913',
  'token': 'a7088080f42f75fc684fbbceb332751e'
}

try:
    response = requests.request("POST", url, headers=headers, data=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
