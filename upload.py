import json
from datetime import datetime
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.chrome.options import Options

import logging
import random
import re
import requests
import os
import sys
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime,timedelta
import urllib


# ----setting config----
cwd = os.getcwd()

#setting file config
path_config = "config.json"
if os.path.isfile(path_config):
    with open(path_config, 'r') as f:
        config = json.load(f)
else:
    sys.exit("File Config Tidak Ada, Mohon Setting Dulu")

CHROME = config['setting'][0]['chromedriver']
UPLOAD_FILE = config['setting'][0]['file_upload']
START = config['setting'][0]['start']
LAPORAN_FILE = config['setting'][0]['laporan_file']
JEDA_UPLOAD = config['setting'][0]['jeda_upload']
STATUS = config['schedule'][0]['status']
RANDOM_HARI = config['schedule'][0]['random_hari']

# API_TELE = config['telegram'][0]['api']
# ID_TELE = config['telegram'][0]['grub_id']



# --fungsi untuk tulis--
def fungsi_tulis(text):
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    tulisan = "{} | {}".format(dt_string,text)
    f = open("laporan.txt", "a")
    f.write(tulisan+"\n")
    f.close()
    print(tulisan)

# cookies
def domain_to_url(domain: str) -> str:
    """ Converts a (partial) domain to valid URL """
    if domain.startswith("."):
        domain = "www" + domain
    return "http://" + domain

def login_using_cookie_file(driver: WebDriver, cookie_file: str):
    """Restore auth cookies from a file. Does not guarantee that the user is logged in afterwards.
    Visits the domains specified in the cookies to set them, the previous page is not restored."""
    domain_cookies: Dict[str, List[object]] = {}
    with open(cookie_file) as file:
        cookies: List = json.load(file)
        # Sort cookies by domain, because we need to visit to domain to add cookies
        for cookie in cookies:
            try:
                domain_cookies[cookie["domain"]].append(cookie)
            except KeyError:
                domain_cookies[cookie["domain"]] = [cookie]

    for domain, cookies in domain_cookies.items():
        driver.get(domain_to_url(domain + "/robots.txt"))
        for cookie in cookies:
            cookie.pop("sameSite", None)  # Attribute should be available in Selenium >4
            cookie.pop("storeId", None)  # Firefox container attribute
            try:
                driver.add_cookie(cookie)
            except:
                fungsi_tulis(f"Couldn't set cookie {cookie['name']} for {domain}")

####script upload####

def laporan_upload(judul,file_video,url,jadwal):
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    tulisan = f"{dt_string}\t{jadwal}\t{judul}\t{file_video}\t{url}"
    f = open(LAPORAN_FILE, "a")
    f.write(tulisan+"\n")
    f.close()

# def telegram_send(bot_message):
#     bot_token = API_TELE
#     bot_chatID = ID_TELE
#     send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
#     response = requests.get(send_text)
#     res = response.json()
#     return res['ok']

def _wait_for_processing(driver):
    progress_label: WebElement = driver.find_element_by_css_selector("span.progress-label")
    pattern = re.compile(r"(finished processing)|(Checks complete.*)|(processing hd.*)|(check.*)|(upload complete.*)")
    current_progress = progress_label.get_attribute("textContent")
    last_progress = None
    
    while not pattern.match(current_progress.lower()):
        if last_progress != current_progress:
            fungsi_tulis(f'Current progress: {current_progress}')
        last_progress = current_progress
        sleep(5)
        current_progress = progress_label.get_attribute("textContent")

def upload_file(
        driver: WebDriver,
        path_video: str,
        description: str,
        setting_thumbnail: str,
        thumbnail_path: str,
        title: str,
        
): 

    fungsi_tulis("buka menu upload")
    # click button 
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ytcp-icon-button#upload-icon"))).click()
    # click button upload file
    fungsi_tulis('click upload file')
    # driver.execute_script("arguments[0].click();", WebDriverWait(driver, 50).until(EC.element_to_be_clickable((
    #     By.XPATH, '//tp-yt-paper-item[@test-id="upload-beta"]')))).click()
    video_input = driver.find_element_by_xpath('//input[@type="file"]')
    video_input.send_keys(path_video)
    fungsi_tulis('sedang mengupload video')

    sleep(10)
    # tulis  judul
    fungsi_tulis("menulis judul")
    WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, "//ytcp-social-suggestions-textbox[@id='title-textarea']//div[@id='textbox']")))
    title_input: WebElement = driver.find_element_by_xpath(
        "//ytcp-social-suggestions-textbox[@id='title-textarea']//div[@id='textbox']")
    title_input.send_keys(Keys.CONTROL + 'a', Keys.BACKSPACE)
    title_input.send_keys(title)

# #####setting deskripsi#####
    fungsi_tulis("Membuat deskripsi")
    WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, '//ytcp-social-suggestions-textbox[@label="Description"]//div[@id="textbox"]')))
    deskripsi_input: WebElement = driver.find_element_by_xpath( 
        '//ytcp-social-suggestions-textbox[@label="Description"]//div[@id="textbox"]')
    deskripsi_input.send_keys(description)
    fungsi_tulis("membuat deskripsi done")

    
    if setting_thumbnail=="on":
        fungsi_tulis("setting thumbnail")
        # driver.execute_script("arguments[0].click();", WebDriverWait(driver, 50).until(EC.element_to_be_clickable((
        # By.XPATH, "//button[@class='remove-default-style style-scope ytcp-thumbnails-compact-editor-uploader']/span[@class='style-scope ytcp-thumbnails-compact-editor-uploader']"))))
        WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='remove-default-style style-scope ytcp-thumbnails-compact-editor-uploader']/span[@class='style-scope ytcp-thumbnails-compact-editor-uploader']")))
        thumnail_input = driver.find_element_by_xpath('//input[@type="file"]')
        thumnail_input.send_keys(thumbnail_path)

    fungsi_tulis("Setting Menu Anak anak")
    WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.NAME, 'VIDEO_MADE_FOR_KIDS_NOT_MFK'))).click()

    sleep(5)

    fungsi_tulis("Mengarah Ke Step 3")
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 100).until(EC.element_to_be_clickable((
        By.ID, "step-badge-3"))))

    upload_time = ""
    sleep(10)
    if STATUS:
        # Penjadwalan
        fungsi_tulis("Setting Penjadwalan")
        menit = [0,15,30,45]
        today = datetime.now()

        upload_time = datetime(today.year, today.month, today.day, 0, 0)
        upload_time = upload_time+timedelta(days=random.randrange(1,int(30)),hours=random.randrange(1,23),minutes=random.choice(menit))

        # fungsi_tulis(upload_time)

        # Start time scheduling
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, "SCHEDULE"))).click()

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#datepicker-trigger > ytcp-dropdown-trigger:nth-child(1)"))).click()

        date_input: WebElement = driver.find_element_by_xpath("//ytcp-date-picker//iron-input/input[@class='style-scope tp-yt-paper-input']")
        sleep(5)
        date_input.clear()
        # Transform date into required format: Mar 19, 2021
        date_input.send_keys(upload_time.strftime("%b %d, %Y"))
        date_input.send_keys(Keys.RETURN)

        sleep(5)

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//ytcp-form-input-container[@id='time-of-day-container']//iron-input/input[@class='style-scope tp-yt-paper-input']"))).click()

        time_list = driver.find_elements_by_css_selector("tp-yt-paper-item.tp-yt-paper-item")
        # Transform time into required format: 8:15 PM
        time_str = upload_time.strftime("%I:%M %p").strip("0")
        time = [time for time in time_list[2:] if time.text == time_str][0]
        time.click()
        fungsi_tulis("Setting Penjadwalan Done")

        sleep(10)
    else:
        #Untuk publish 
        fungsi_tulis("Memilih Untuk Publish")
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-radio-button[@class='style-scope ytcp-video-visibility-select'][3]"))).click()
        # untuk menekan tombol save
        sleep(10)


    fungsi_tulis("Wait Prosess")    
    _wait_for_processing(driver)
    fungsi_tulis("Proses Berhasil")

    url_video_upload = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.CLASS_NAME, "video-url-fadeable"))).get_attribute("innerText")

    sleep(10)
    # done
    driver.execute_script("arguments[0].click();", WebDriverWait(driver, 50).until(EC.element_to_be_clickable((
        By.XPATH, "//ytcp-button[@id='done-button']"))))


    # close floating
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((
        By.XPATH, "//div[@class='footer style-scope ytcp-dialog']/ytcp-button[@id='close-button']/div[@class='label style-scope ytcp-button']"))).click()
    
    if upload_time == "":
        upload_time = datetime.now()
    upload_time = upload_time.strftime("%d/%m/%Y %H:%M:%S")
    laporan_upload(title,path_video,url_video_upload,upload_time)
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    text_tg = f"Sukses Upload Video\n\nWaktu upload : {dt_string}\nSchedule : {upload_time}\nJudul : {title}\nURL : {url_video_upload}"
    text_tg = urllib.parse.quote_plus(text_tg)
    telegram_send(text_tg)
    fungsi_tulis(f"Berhasil upload video {title} dengan URL {url_video_upload}")

f = open(UPLOAD_FILE, "r")
a = f.readlines()[START:]
f.close()

for line in a:
    driver = webdriver.Chrome(CHROME)

    kolom = line.split(";")
    urutan = kolom[0]
    judul = kolom[1]
    video = kolom[2]
    set_deskripsi = "{}\n\n{}".format(judul,kolom[3].replace("[enter]","\n"))
    setting_thumbnail = kolom[4]
    thumbnail = kolom[5]
    cookies = kolom[6].replace("\n","")

    fungsi_tulis("upload video ke ==> {} | {}".format(urutan, judul))


    try:
        login_using_cookie_file(driver,cookies)
        fungsi_tulis("Mencoba login dengan cookies")
        driver.get("https://studio.youtube.com")
        fungsi_tulis("Done Login Cookies")
        upload_file(
            driver,
            path_video = video,
            title = judul,
            description = set_deskripsi,
            setting_thumbnail = setting_thumbnail,
            thumbnail_path = thumbnail,
            # game=None,
            # kid=None,
            )
        driver.quit()
        fungsi_tulis("Upload Selesai video ke --> {} | {}".format(urutan, judul))
        fungsi_tulis("Jeda {} detik".format(JEDA_UPLOAD))
        sleep(JEDA_UPLOAD)
    except Exception as e: 
        fungsi_tulis("Error saat memproses {}".format(urutan))
        fungsi_tulis(e)
        driver.quit()

        