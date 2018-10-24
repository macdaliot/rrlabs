#!/usr/bin/env python3
from selenium import webdriver
import logging, sys

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
    browser.get('http://127.0.0.1:9080/')
    browser.find_element_by_id('user_password').send_keys('password')
    browser.find_element_by_id('user_password_confirmation').send_keys('password')
    browser.find_element_by_name('commit').click()
except Exception as err:
    logging.info('administrator password is already set')
    sys.exit(0)

try:
    browser.get('http://127.0.0.1:9080/')
    browser.find_element_by_id('user_password_confirmation')
    logging.error('failed to set administrator password')
    sys.exit(1)
except Exception as err:
    logging.info('administrator password has been set')
    pass
