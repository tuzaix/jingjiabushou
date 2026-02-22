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
  'timestamp': '1771766227652',
  'token': '9302122f9a9a974d1e9fe0f2819b54fd',
}

cookies = {
    'SESSION': 'NzE2YWU3NWQtMTE4Ni00NzA4LTkxMTQtZTFlZWQ1N2NmODI5',
    'Hm_lvt_58aa18061df7855800f2a1b32d6da7f4': '1771683666,1771706442,1771748779,1771765879',
    'Hm_lpvt_58aa18061df7855800f2a1b32d6da7f4': '1771766225'
}

# -b 'SESSION=NzE2YWU3NWQtMTE4Ni00NzA4LTkxMTQtZTFlZWQ1N2NmODI5; Hm_lvt_58aa18061df7855800f2a1b32d6da7f4=1771683666,1771706442,1771748779,1771765879; Hm_lpvt_58aa18061df7855800f2a1b32d6da7f4=1771766225' \

response = requests.request("POST", url, headers=headers, data=payload, cookies=cookies)
print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.text}")
