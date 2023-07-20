from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import telegram
import asyncio

# 사용자 아이디 및 비밀번호로 로그인
def login(wait: WebDriverWait):
    with open("credentials.json", "r") as credentials:
        crd = json.load(credentials)

    try:
        userIdElement = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="userId"]')))
        userIdElement.send_keys(crd['userId'])
        passwordElement = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
        passwordElement.send_keys(crd['password'])
        submitElement = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="loginForm"]/div/div[3]/div[2]/div[2]/ul/li[3]/button')))
        submitElement.click()
    except Exception as e:
        sendBotMsg(f"Error occured when trying to login\n\n{e}", "ERROR")
        print(f"Error occured when trying to login\n\n{e}")
        return -1

# 받은 메일 개수 반환
def getMailCount(wait: WebDriverWait):
    try:
        res = int(wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="total_mail_count"]'))).text)
        return res
    except Exception as e:
        sendBotMsg(f"Error occured when trying to get count\n\n{e}", "ERROR")
        print(f"Error occured when trying to get count\n\n{e}")
        return -1

# 보낸 사람 및 제목 데이터 수집
def getDataLists(wait: WebDriverWait):
    try:
        # 보낸사람 데이터 저장
        senderList = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[contains(@id, "m_")]/div/p[1]/span/a')))
        for i in range(len(senderList)):
            senderList[i] = senderList[i].text
        # 제목 데이터 저장
        titleList = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[contains(@id, "m_")]/div/p[2]/a[1]')))
        for i in range(len(titleList)):
            titleList[i] = titleList[i].text
        return senderList, titleList
    except Exception as e:
        sendBotMsg(f"Error occured when trying to get data\n\n{e}", "ERROR")
        print(f"Error occured when trying to get data\n\n{e}")
        return -1, -1

# 텔레그램 메시지 전송
def sendBotMsg(title, sender=""):
    with open("credentials.json", "r") as credentials:
        crd = json.load(credentials)
    bot = telegram.Bot(token=crd['token'])
    chatId = crd['chatId']
    asyncio.run(bot.send_message(chatId, f"{title}\n\nfrom: {sender}"))

def crawlKumohMail(refreshTime):
    # 크롤링 옵션
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument("enable-automation")
    # options.add_argument("--disable-infobars")
    # options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get("https://mail.kumoh.ac.kr/mail/list.do")

    timeout = 20
    wait = WebDriverWait(driver, timeout)

    # 로그인 안 되어있는 경우
    if driver.current_url == "https://mail.kumoh.ac.kr/account/login.do":
        res = login(wait)
        if res == -1:
            driver.quit()
            return

    mailCnt = getMailCount(wait)
    if res == -1:
        driver.quit()
        return

    # 5초 전과 현재의 받은 메일 개수 비교
    # 많아지면 받은 순서대로 텔레그램 전송
    while True:
        time.sleep(refreshTime)
        driver.refresh()

        if driver.current_url == "https://mail.kumoh.ac.kr/account/login.do":
            res = login(wait)
            if res == -1:
                driver.quit()
                return

        newMailCnt = getMailCount(wait)
        if newMailCnt == -1:
            driver.quit()
            return
        if mailCnt < newMailCnt:
            senderList, titleList = getDataLists(wait)
            if senderList == -1:
                driver.quit()
                return
            i = newMailCnt - mailCnt
            while i != 0:
                print(f"{titleList[i-1]}\n\nfrom: {senderList[i-1]}")
                sendBotMsg(titleList[i-1], senderList[i-1])
                i -= 1
        
        mailCnt = newMailCnt
        continue

if __name__ == "__main__":
    refreshTime = 3
    crawlKumohMail(refreshTime)