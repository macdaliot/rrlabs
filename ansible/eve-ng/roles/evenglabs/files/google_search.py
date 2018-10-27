#!/usr/bin/env python3
from selenium import webdriver
import logging, subprocess, sys

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

options = webdriver.ChromeOptions()
options.binary_location = '/usr/bin/chromium-browser'
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('start-maximized')
options.add_argument('--disable-gpu')
options.add_argument('disable-infobars')
options.add_argument('--disable-extensions')
browser = webdriver.Chrome(options = options)

try:
    browser.get('https://www.google.com/')
    browser.find_element_by_name('q').send_keys('wikipedia')
    browser.find_element_by_name('btnK').click()
    print(browser.find_element_by_xpath('//html/body').text)
except Exception as err:
    logging.error('cannot fill the form', exc_info = True)
    sys.exit(1)
