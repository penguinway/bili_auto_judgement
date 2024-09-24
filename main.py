import random
import sys
import time
from judge import Judgement
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
    datefmt='%Y-%m-%d %A %H:%M:%S'
)
judge = Judgement()


def get_judge_data():  # 获取夹击妹抖的信息
    data_url = "https://api.bilibili.com/x/credit/v2/jury/jury"
    judge_data = judge.get_data(url=data_url)
    term_end = judge_data["term_end"]
    status = judge_data["status"]
    logging.info("获取夹击妹抖信息")
    return term_end, status


def get_next_judge():
    get_url = "https://api.bilibili.com/x/credit/v2/jury/case/next"
    logging.info("获取下一案件信息")
    return judge.get_data(url=get_url)["case_id"]


def get_judge_info(case_id):
    info_url = "https://api.bilibili.com/x/credit/v2/jury/case/info?case_id=" + str(case_id)
    logging.info("获取案件" + str(case_id) + "信息")
    return judge.get_data(url=info_url)["case_type"]


def vote(vote_num=0, case_id=None):
    vote_url = "https://api.bilibili.com/x/credit/v2/jury/vote"
    payload = {
        "case_id": str(case_id),
        "vote": vote_num,
        "insiders": 0,
        "anonymous": 0,
        "content": "",
        "csrf": judge.csrf,
    }
    vote_result = judge.post_data(url=vote_url, data=payload)
    logging.info("案件" + case_id + "投票成功！")


def big_vip_sign():
    sign_url = "https://api.bilibili.com/pgc/activity/score/task/sign"
    payload = {
        "csrf": judge.csrf,
    }
    logging.info("大会员签到")
    sign_result = judge.post_data(url=sign_url, data=payload)


sign_status = True
if not judge.cookies_login():
    sign_status = judge.QR_login()
if sign_status:
    big_vip_sign()
    while True:
        try:
            judge_id = get_next_judge()
            print(judge_id)
            case_type = get_judge_info(case_id=judge_id)
            vote(vote_num=0, case_id=judge_id)
            if case_type in [1, 3]:
                vote(vote_num=1, case_id=judge_id)
            if case_type in [2, 4]:
                vote(vote_num=11, case_id=judge_id)
            time.sleep(random.randint(5, 10))
        except TypeError:
            logging.info("任务结束或中断！")
            sys.exit()
else:
    logging.error("用户未登录或登录失败，任务结束！")
