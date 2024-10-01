import json
import logging
import requests
from urllib.parse import quote
import time
import qrcode
import re
import zlib
import brotli
import gzip
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
    datefmt='%Y-%m-%d %A %H:%M:%S'
)


def qrcode_generate(data):
    qr = qrcode.QRCode(border=1)
    qr.add_data(data=data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def decompress_response(response):
    content_encoding = response.headers.get('Content-Encoding')
    try:
        if content_encoding == 'gzip':
            return zlib.decompress(response.content, zlib.MAX_WBITS | 16)
        elif content_encoding == 'deflate':
            return zlib.decompress(response.content)
        elif content_encoding == 'br':
            return brotli.decompress(response.content)
        else:
            return response.content
    except zlib.error:
        return response.text


class Judgement:
    def __init__(self):  # 统一配置项
        self.token = None
        self.post_header = {
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
        self.get_header = {
            "Cookie": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, */*",
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
        try:
            with open("cookies.json", "r", encoding="UTF-8") as f:
                cookies = json.load(f)
            for cookie in cookies:
                if cookie["name"] == "bili_jct":
                    self.csrf = cookie["value"]
                if cookie["name"] in ["SESSDATA", "DedeUserID", "bili_jct"]:
                    self.get_header["Cookie"] += cookie['name'] + "=" + cookie["value"] + ";"
                    self.post_header["Cookie"] += cookie['name'] + "=" + cookie["value"] + ";"
            check_url = "https://api.bilibili.com/x/web-interface/nav"
            login_status = requests.get(url=check_url, headers=self.get_header).json()
            # print(login_status)
            if not login_status["code"]:
                logging.info(f'用户{login_status["data"]["uname"]}, 欢迎使用！')
                logging.info("Cookies登录成功！")
                # print(self.get_header)
                return True
            else:
                logging.warning("登录态失效，10s后重新登录！")
                return False
        except json.decoder.JSONDecodeError:
            logging.error("JSON解析有误！请检查接口返回！")
            return False
        except requests.exceptions.JSONDecodeError:
            logging.error("JSON解析有误！请检查接口返回！")
            return False
        except KeyError:
            logging.error("Cookies登录失败！")
            return False
        except TypeError:
            logging.error("Cookies登录失败！")
            return False

    def QR_login(self):
        generate_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
        login_url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key="
        try:
            generate_result = requests.get(url=generate_url, headers=self.get_header).json()  # 生成二维码链接
            qrcode_generate(data=generate_result["data"]["url"])
            time.sleep(20)
            login_url += quote(generate_result["data"]["qrcode_key"])
            login_result = requests.get(login_url, headers=self.get_header)  # 检查登录状态
            time.sleep(3)
            cookies = login_result.headers["Set-Cookie"]
            sess_data = re.search(r"SESSDATA=([^;]+)", cookies).group(1)
            bili_jct = re.search(r"bili_jct=([^;]+)", cookies).group(1)
            dede_user_id = re.search(r"DedeUserID=([^;]+)", cookies).group(1)
            self.get_header["Cookie"] += f"SESSDATA={sess_data};bili_jct={bili_jct};DedeUserID={dede_user_id};"
            self.post_header["Cookie"] += f"SESSDATA={sess_data};bili_jct={bili_jct};DedeUserID={dede_user_id};"
            self.csrf = bili_jct
            cookies = [
                {
                    "name": "SESSDATA",
                    "value": sess_data
                },
                {
                    "name": "bili_jct",
                    "value": bili_jct
                },
                {
                    "name": "DedeUserID",
                    "value": dede_user_id
                }
            ]
            # 持久化保存
            with open("cookies.json", "w", encoding="UTF-8") as f:
                json.dump(cookies, fp=f, indent=4)
            return True
        except json.decoder.JSONDecodeError:
            logging.error("JSON解析有误！请检查接口返回！")
            return False
        except requests.exceptions.JSONDecodeError:
            logging.error("JSON解析有误！请检查接口返回！")
            return False
        except KeyError:
            logging.error("QR登录失败！")
            return True

    def get_data(self, url):
        post_data = {
            "csrf": self.csrf,
        }
        try:
            get_datas = requests.get(url=url, headers=self.get_header, data=post_data)
            data_json = None
            if sys.platform.startswith('win'):
                data_json = get_datas.json()
            elif sys.platform.startswith('linux'):
                decompressed_content = decompress_response(get_datas)
                data_json = json.loads(decompressed_content)
            if data_json["code"] != 0:
                logging.error("Error:" + data_json["message"])
                return False
            else:
                logging.critical(url + "发送GET请求成功！")
                return data_json["data"]
        except json.decoder.JSONDecodeError:
            logging.error("GET JSON解析有误！请检查接口返回！")
            return False
        except requests.exceptions.JSONDecodeError:
            logging.error("GET JSON解析有误！请检查接口返回！")
            return False
        except zlib.error:
            logging.error("GET 解压错误！")
            return False
        except KeyError:
            logging.error("QR登录失败！")
            return True

    def post_data(self, url, data):
        try:
            post_datas = requests.post(url=url, data=data, headers=self.post_header)
            data_json = None
            if sys.platform.startswith('win'):
                data_json = post_datas.json()
            elif sys.platform.startswith('linux'):
                decompressed_content = decompress_response(post_datas)
                data_json = json.loads(decompressed_content)
            if data_json["code"] != 0:
                logging.error("Error:" + data_json["message"])
                return False
            else:
                logging.critical(url + "发送POST请求成功！")
                return True
        except json.decoder.JSONDecodeError:
            logging.error("POST JSON解析有误！请检查接口返回！")
            return False
        except requests.exceptions.JSONDecodeError:
            logging.error("POST JSON解析有误！请检查接口返回！")
            return False
        except KeyError:
            logging.error("QR登录失败！")
            return True
