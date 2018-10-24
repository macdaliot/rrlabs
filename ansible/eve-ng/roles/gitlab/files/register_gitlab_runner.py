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
    browser.get('http://127.0.0.1:9080/users/sign_in')
    browser.find_element_by_id('user_login').send_keys('root')
    browser.find_element_by_id('user_password').send_keys('password')
    browser.find_element_by_name('commit').click()
except Exception as err:
    logging.error('failed to access')
    sys.exit(1)

try:
    browser.get('http://127.0.0.1:9080/admin/runners')
    token = browser.find_element_by_id('registration_token').text
except Exception as err:
    logging.error('failed to access')
    sys.exit(1)

cmd = 'gitlab-runner register --non-interactive --url http://127.0.0.1:9080 --registration-token {} --executor shell'.format(token)
process = subprocess.Popen(cmd.split())
process.communicate()
if process.returncode != 0:
    logging.error('failed to execute "{}"'.format(cmd))
    logging.debug('  stdout = {}'.format(process.stdout))
    logging.debug('  stderr = {}'.format(process.stderr))
