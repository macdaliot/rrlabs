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
    browser.get('http://127.0.0.1:9080/users/sign_in')
    browser.find_element_by_id('user_login').send_keys('root')
    browser.find_element_by_id('user_password').send_keys('password')
    browser.find_element_by_name('commit').click()
except Exception as err:
    logging.error('failed to access')
    sys.exit(1)

try:
    browser.get('http://127.0.0.1:9080/root/net-ci-cd')
    if 'Not Found' not in browser.title:
        logging.info('project already created')
        sys.exit(0)
except Exception as err:
    logging.error('failed to login')
    sys.exit(1)

try:
    browser.get('http://127.0.0.1:9080/projects/new')
    browser.find_element_by_id('project_name').send_keys('net-ci-cd')
    browser.find_element_by_id('project_path').send_keys('net-ci-cd')
    browser.find_element_by_id('project_initialize_with_readme').click()
    browser.find_element_by_name('commit').click()
except Exception as err:
    logging.error('failed to login')
    sys.exit(1)

try:
    browser.get('http://127.0.0.1:9080/root/net-ci-cd')
    logging.info('project created')
    sys.exit(0)
except Exception as err:
    logging.error('failed to create project')
    sys.exit(1)
