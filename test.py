from judge import Judgement
import requests
import re


# judge = Judgement()
# judge.QR_login()
# re = requests.get("https://www.bilibili.com")
# cookies = requests.utils.dict_from_cookiejar(re.cookies)
# print(cookies)
with open("cookies_test.json", "r", encoding="UTF-8") as f:
    cookies = f.read()
sess_data = re.search(r"SESSDATA=([^;]+)", cookies).group(1)
bili_jct = re.search(r"bili_jct=([^;]+)", cookies).group(1)
dede_user_id = re.search(r"DedeUserID=([^;]+)", cookies).group(1)

# 打印结果
print(f"SESSDATA={sess_data};bili_jct={bili_jct};DedeUserID={dede_user_id};")
