from curl_cffi import requests
import os
import re
import time
import logging
from urllib.parse import urljoin

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 網站設定
BASE_URL = 'https://zodgame.xyz/'
SIGN_URL = urljoin(BASE_URL, 'plugin.php?id=dsu_paulsign:sign')

# 重試設定
MAX_RETRIES = 3
RETRY_DELAY = 10
MAX_ROUNDS = 3        # 最多幾輪（每輪 MAX_RETRIES 次）
LONG_RETRY_DELAY = 3600  # 輪次之間的等待（秒）

# 必要的 cookie 名稱（只保留這四個，cf_clearance 不帶）
ESSENTIAL_COOKIES = [
    'qhMq_2132_saltkey',
    'qhMq_2132_auth',
    'qhMq_2132_lastvisit',
    'qhMq_2132_ulastactivity'
]

def parse_cookies(cookie_str):
    """解析 cookie 字串並只保留必要的 cookie"""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item or '=' not in item:
            continue
        name, value = item.split('=', 1)
        name = name.strip()
        if name in ESSENTIAL_COOKIES:
            cookies[name] = value.strip()
    return cookies

def check_sign_status(response_text):
    """檢查簽到狀態"""
    if '您今天已經簽到過了' in response_text or '您今天已经签到过了' in response_text:
        return 'already_signed'
    elif '您還未登錄' in response_text or '您还未登录' in response_text:
        return 'not_logged_in'
    return 'ready_to_sign'

def extract_formhash(html_content):
    """從 HTML 內容中提取 formhash"""
    match = re.search(r'name="formhash" value="([^"]+)"', html_content)
    return match.group(1) if match else None

def extract_reward(response_text):
    """從回應中提取獎勵資訊"""
    match = re.search(r'获得随机奖励\s*酱油\s*(\d+)\s*瓶', response_text)
    return match.group(1) if match else None

def sign_with_retry(cookies, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY):
    """帶有重試機制的簽到函數（多輪重試，輪次間長等待）"""
    for round_num in range(MAX_ROUNDS):
        if round_num > 0:
            logger.info(f"等待 {LONG_RETRY_DELAY} 秒後開始第 {round_num + 1} 輪重試...")
            time.sleep(LONG_RETRY_DELAY)

        for attempt in range(max_retries):
            try:
                session = requests.Session(impersonate="chrome120")
                session.cookies.update(cookies)
                session.headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Referer': SIGN_URL
                })

                response = session.get(SIGN_URL, timeout=30)
                response.raise_for_status()

                status = check_sign_status(response.text)
                if status == 'already_signed':
                    logger.info("今天已經簽到過了")
                    return True
                elif status == 'not_logged_in':
                    logger.error("Cookie 已過期或無效，請更新 ZODGAME_COOKIE")
                    return False

                formhash = extract_formhash(response.text)
                if not formhash:
                    logger.error("無法獲取 formhash，可能未正確登入")
                    return False

                sign_data = {
                    'formhash': formhash,
                    'qdxq': 'kx',
                    'qdmode': '1',
                    'todaysay': '每日簽到',
                    'fastreply': '0'
                }

                sign_url = f"{SIGN_URL}&operation=qiandao&infloat=1&inajax=1"
                sign_response = session.post(sign_url, data=sign_data, timeout=30)
                sign_response.raise_for_status()

                if "恭喜你签到成功" in sign_response.text or "簽到成功" in sign_response.text:
                    reward = extract_reward(sign_response.text)
                    if reward:
                        logger.info(f"簽到成功！獲得酱油 {reward} 瓶")
                    else:
                        logger.info("簽到成功！")
                    return True
                elif "已經簽到" in sign_response.text or "已经签到" in sign_response.text:
                    logger.info("今天已經簽到過了")
                    return True
                else:
                    logger.warning(f"簽到回應不符合預期：{sign_response.text[:200]}...")

            except Exception as e:
                logger.error(f"第 {round_num + 1} 輪第 {attempt + 1} 次嘗試失敗：{str(e)}")

            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒後重試...")
                time.sleep(retry_delay)

    logger.error(f"已重試 {MAX_ROUNDS} 輪，簽到失敗")
    return False

def main():
    try:
        cookie_str = os.environ.get('ZODGAME_COOKIE')
        if not cookie_str:
            logger.error("請設定 ZODGAME_COOKIE 環境變數")
            exit(1)

        cookies = parse_cookies(cookie_str)
        logger.info(f"已載入 {len(cookies)} 個 cookie")

        if sign_with_retry(cookies):
            logger.info("簽到操作完成")
            exit(0)
        else:
            logger.error("簽到失敗！")
            exit(1)
    except Exception as e:
        logger.exception(f"發生未預期的錯誤：{str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
