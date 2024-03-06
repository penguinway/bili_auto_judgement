import json
import logging
import requests
from urllib.parse import quote
import time
import qrcode
import re


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
    datefmt='%Y-%m-%d %A %H:%M:%S'
)


class Judgement:
    def __init__(self):  # 统一配置项
        self.token = None
        self.header = {
            "Host": "api.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "Cookie": "",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        self.csrf = None

    def cookies_login(self):  # 模拟Cookies登录行为
        with open("cookies.json", "r", encoding="UTF-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            if cookie["name"] == "bili_jct":
                self.csrf = cookie["value"]
            if cookie["name"] in ["SESSDATA", "DedeUserID", "bili_jct"]:
                self.header["Cookie"] += cookie['name'] + "=" + cookie["value"] + ";"
        check_url = "https://api.bilibili.com/x/web-interface/nav"
        login_status = requests.get(url=check_url, headers=self.header).json()
        print(login_status)
        if login_status:
            logging.info(f'用户{login_status["data"]["uname"]}, 欢迎使用！')
            logging.info("Cookies登录成功！")
            print(self.header)
            return True
        else:
            logging.warning("登录态失效，10s后重新登录！")
            return False


    def QR_login(self):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        generate_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        login_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key="
        generate_result = requests.get(url=generate_url, headers=header).json()
        qr_url = generate_result["data"]["url"]
        qr = qrcode.QRCode(border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        time.sleep(20)
        login_url += quote(generate_result["data"]["qrcode_key"])
        login_result = requests.get(login_url, headers=header)
        time.sleep(3)
        cookies = login_result.headers["Set-Cookie"]
        sess_data = re.search(r"SESSDATA=([^;]+)", cookies).group(1)
        bili_jct = re.search(r"bili_jct=([^;]+)", cookies).group(1)
        dede_user_id = re.search(r"DedeUserID=([^;]+)", cookies).group(1)
        self.header["Cookies"] += f"SESSDATA={sess_data};bili_jct={bili_jct};DedeUserID={dede_user_id};"

    def get_data(self, url):
        post_data = {
            "csrf": self.csrf,
        }
        data_json = requests.get(url=url, headers=self.header, data=post_data).json()
        if data_json["code"] != 0:
            logging.error("Error:" + data_json["message"])
            return False
        else:
            logging.info(url + "发送GET请求成功！")
            return data_json["data"]

    def post_data(self, url, data):
        data_json = requests.post(url=url, data=data, headers=self.header).json()
        if data_json["code"] != 0:
            logging.error("Error:" + data_json["message"])
            return False
        else:
            logging.info(url + "发送POST请求成功！")
            return True
