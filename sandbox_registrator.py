"""
Script for registering Sandbox accounts in bulk.
"""

from sys import stderr, exit
import json
import tkinter as tk
import secrets
from time import sleep
import platform

import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service
from loguru import logger
from random_username.generate import generate_username


logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> |"
                          "<cyan>{line}</cyan> - <white>{message}</white>")


class FileManager:
    """
    Class contains functions for manipulating txt and json files.
    """

    @staticmethod
    def read_config_file(file_name: str):
        """
        Method for reading json files
        :param file_name: str
        :return: json data
        """
        with open(f'{file_name}.json') as json_file:
            return json.load(json_file)

    @staticmethod
    def read_txt_file(file_name: str):
        """
        Method for reading txt files
        :param file_name: str
        :return: list
        """
        with open(f'{file_name}.txt') as file:
            return [line.rstrip() for line in file]

    @staticmethod
    def append_txt_file(file_name: str, data: str):
        """
        Method for saving txt files
        :param file_name: str
        :param data: str
        """

        with open(f'{file_name}.txt', 'a') as file:
            file.write(f'{data}\n')


class MetamaskInterface:
    """
    Object that init metamask interface buttons and input fields.
    """

    def __init__(self):
        self.start_button = '//button[@class="button btn--rounded btn-primary first-time-flow__button"]'
        self.create_new_wallet_button = '//*[@id="app-content"]/div/div[2]/div/div/div[2]/div/div[2]/div[2]/button'
        self.i_agree_button = '//button[@data-testid="page-container-footer-next"]'
        self.password_input = '//input[@autocomplete="new-password"]'
        self.confirm_password_input = '//input[@autocomplete="confirm-password"]'
        self.agreement_checkbox = '//div[@class="first-time-flow__checkbox"]'
        self.final_create_wallet_button = '//button[@class="button btn--rounded btn-primary first-time-flow__button"]'
        self.continue_button = '//*[@id="app-content"]/div/div[2]/div/div/div[2]/div/div[1]/div[2]/button'
        self.reveal_seed_field = '//div[@class="reveal-seed-phrase__secret-blocker"]'
        self.seedphrase_div = '//*[@id="app-content"]/div/div[2]/div/div/div[2]/div[1]/div[1]/div[5]/div'
        self.remind_later_button = '//*[@id="app-content"]/div/div[2]/div/div/div[2]/div[2]/button[1]'
        self.public_key_copy_div = '//div[@class="selected-account__address"]'


class SandboxInterface:
    """
    Object that init sandbox interface buttons and input fields.
    """

    def __init__(self):
        self.sign_in_button = '//*[@id="sign-in-button"]'
        self.log_in_with_metamask_button = '//div[contains(@class,"small-logos only-mobile")]'
        self.metamask_popup_next_button = '//*[@id="app-content"]/div/div[2]/div/div[3]/div[2]/button[2]'
        self.metamask_popup_connect_button = '//*[@id="app-content"]/div/div[2]/div/div[2]/div[2]/div[2]/' \
                                             'footer/button[2]'
        self.email_input = '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div[1]/div/div[1]/input'
        self.nickname_input = '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div[1]/div/div[3]/input'
        self.continue_registration_button = '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div[2]/button'
        self.input_error_message = '//p[@class="input-error"]'
        self.metamask_sign_button = '//*[@id="app-content"]/div/div[2]/div/div[3]/button[2]'
        self.password_input = '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div/div[1]/div/div[1]/div/input'
        self.repeat_password_input = \
            '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div/div[1]/div/div[2]/div/input'
        self.save_password_button = '//*[@id="__layout"]/div/div/div[4]/div/div[2]/div/div/div/div[2]/button'
        self.buy_land_button = '//button[contains(.,"Buy LAND")]'
        self.avatar_randomize_button = '//button[@class="randomizeButton"]'
        self.save_avatar_button = '//*[@id="basic"]/div[2]/div[5]/button'


class DolphinAccount:
    """
    Class for init dolphin account object with credentials and generate access token.
    """

    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.authorization_token = None

    def authorise_account(self):
        """
        Method for authorising account for future api calls.
        :return: bool
        """

        url = 'https://anty-api.com/auth/login'
        payload = {'username': self.login, 'password': self.password}
        response = requests.post(url, data=payload)
        json_response = json.loads(response.text)

        if 'token' in json_response:
            self.authorization_token = json_response['token']
            return True
        else:
            return False


class DolphinProfile:
    """
    Class that contains methods for manipulating Dolphin profiles using local API.
    """

    def __init__(self, user_agent: str, proxy: str):
        self.user_agent = user_agent
        self.proxy = proxy
        self.browser_profile_id = None
        self.window_port = None
        self.window_endpoint = None
        self.proxy_host = None
        self.proxy_port = None
        self.proxy_login = None
        self.proxy_password = None
        self.__parse_proxy()

    def __parse_proxy(self):
        self.proxy_host = self.proxy.split('@')[1].split(':')[0]
        self.proxy_port = self.proxy.split('@')[1].split(':')[1]
        self.proxy_login = self.proxy.split('@')[0].split('//')[1].split(':')[0]
        self.proxy_password = self.proxy.split('@')[0].split('//')[1].split(':')[1]

    def create_new_profile(self, authorization_token: str):
        """
        Create new profile in Dolphin browser using local API.
        :param authorization_token: str
        :return: bool
        """

        url = 'https://anty-api.com/browser_profiles'
        headers = {'Authorization': authorization_token}
        payload = {
            'name': 't.me/CryptoKiddiesClub',
            'platform': 'windows',
            'mainWebsite': 'crypto',
            'useragent[mode]': 'manual',
            'useragent[value]': self.user_agent,
            'webrtc[mode]': 'altered',
            'canvas[mode]': 'real',
            'webgl[mode]': 'real',
            'webglInfo[mode]': 'noise',
            'timezone[mode]': 'auto',
            'locale[mode]': 'auto',
            'geolocation[mode]': 'auto',
            'cpu[mode]': 'real',
            'memory[mode]': 'real',
            'browserType': "['anty']",
            'proxy[type]': 'http',
            'proxy[host]': self.proxy_host,
            'proxy[port]': self.proxy_port,
            'proxy[login]': self.proxy_login,
            'proxy[password]': self.proxy_password,
            'proxy[name]': 't.me/CryptoKiddiesClub'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            json_response = json.loads(response.text)

            if json_response['success'] != 1:
                return False
            else:
                self.browser_profile_id = json_response['browserProfileId']
                return True
        except:
            return False

    def delete_profile(self, authorization_token: str):
        """
        Deletes profile in Dolphin browser.
        :return: bool
        """

        url = f"https://anty-api.com/browser_profiles/{self.browser_profile_id}"
        authorization = f"Bearer {authorization_token}"
        headers = {'Authorization': authorization}
        response = requests.delete(url, headers=headers)

        try:
            json_response = json.loads(response.text)
            if json_response['success']:
                return True
        except:
            return False

    def start_profile(self):
        """
        Starts profile in Dolphin browser.
        :return: bool
        """

        url = f'http://localhost:3001/v1.0/browser_profiles/{self.browser_profile_id}/start?automation=1'
        response = requests.get(url)
        json_response = json.loads(response.text)
        if json_response['success']:
            self.window_port = json_response['automation']['port']
            self.window_endpoint = json_response['automation']['wsEndpoint']
            return True
        else:
            return False

    def stop_profile(self):
        """
        Stops profile in Dolphin browser.
        :return: bool
        """

        url = f'http://localhost:3001/v1.0/browser_profiles/{self.browser_profile_id}/stop'
        response = requests.get(url)
        json_response = json.loads(response.text)
        if json_response['success']:
            return True
        else:
            return False


class MetamaskAccount:
    """
    Class for manipulating metamask accounts.
    """

    def __init__(self, password):
        self.password = password
        self.seed_phrase = None
        self.public_key = None

    def register_metamask(self, new_driver: webdriver):
        """
        Registers new metamask account using password from "config.json" file.
        :param new_driver: web-driver
        :return: bool
        """

        try:
            root = tk.Tk()
            interface = MetamaskInterface()
            wait = WebDriverWait(new_driver, 60)
            wait.until(ec.number_of_windows_to_be(2))

            new_driver.switch_to.window(new_driver.window_handles[1])

            wait.until(ec.presence_of_element_located((By.XPATH, interface.start_button))).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.create_new_wallet_button))).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.i_agree_button))).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.password_input))).send_keys(self.password)
            new_driver.find_element(By.XPATH, interface.confirm_password_input).send_keys(self.password)
            new_driver.find_element(By.XPATH, interface.agreement_checkbox).click()
            new_driver.find_element(By.XPATH, interface.final_create_wallet_button).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.continue_button))).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.reveal_seed_field))).click()
            page_html = new_driver.execute_script('return document.getElementById("app-content").innerHTML')
            self.seed_phrase = page_html.split('<div class="reveal-seed-phrase__secret-words notranslate">')[1] \
                .split('</div>')[0]

            new_driver.find_element(By.XPATH, interface.remind_later_button).click()
            wait.until(ec.presence_of_element_located((By.XPATH, interface.public_key_copy_div))).click()
            self.public_key = root.clipboard_get()
            return True
        except:
            return False


class SandboxAccount:
    """
    Sandbox account object.
    """

    def __init__(self, email: str):
        self.email = email
        self.username = None
        self.password = None

    def __generate_username(self):
        self.username = generate_username()[0]

    def __generate_password(self):
        self.password = secrets.token_urlsafe(15)

    def register_sandbox_account(self, new_driver: webdriver, window_port: str):
        """
        Registers new Sandbox account.
        :param new_driver: web-driver
        :param window_port: str
        """

        interface = SandboxInterface()

        with new_driver:
            new_driver.get('https://www.sandbox.game/en/')

        sleep(5)
        new_driver = init_selenium_driver(window_port)
        wait = WebDriverWait(new_driver, 60)

        new_driver.get('https://www.sandbox.game/en/')
        new_driver.switch_to.window(new_driver.window_handles[1])
        wait.until(ec.visibility_of_element_located((By.XPATH, interface.sign_in_button)))
        sleep(5)
        new_driver.switch_to.window(new_driver.window_handles[0])
        new_driver.close()
        new_driver.switch_to.window(new_driver.window_handles[0])

        wait.until(ec.visibility_of_element_located((By.XPATH, interface.sign_in_button))).click()
        wait.until(ec.visibility_of_element_located((By.XPATH, interface.log_in_with_metamask_button))).click()

        wait.until(ec.number_of_windows_to_be(2))
        new_driver.switch_to.window(new_driver.window_handles[1])
        wait.until(ec.visibility_of_element_located((By.XPATH, interface.metamask_popup_next_button))).click()
        wait.until(ec.visibility_of_element_located((By.XPATH, interface.metamask_popup_connect_button))).click()

        new_driver.switch_to.window(new_driver.window_handles[0])
        wait.until(ec.element_to_be_clickable((By.XPATH, interface.email_input))).send_keys(self.email)

        while True:
            try:
                self.__generate_username()
                self.__generate_password()
                wait.until(ec.element_to_be_clickable((By.XPATH, interface.nickname_input))).clear()
                wait.until(ec.element_to_be_clickable((By.XPATH, interface.nickname_input))).send_keys(self.username)
                wait.until(ec.element_to_be_clickable((By.XPATH, interface.continue_registration_button))).click()
                sleep(5)

                WebDriverWait(new_driver, 20).until(ec.number_of_windows_to_be(2))
                new_driver.switch_to.window(new_driver.window_handles[1])
                wait.until(ec.visibility_of_element_located((By.XPATH, interface.metamask_sign_button))).click()
                new_driver.switch_to.window(new_driver.window_handles[0])
                WebDriverWait(new_driver, 20).until(ec.element_to_be_clickable((By.XPATH, interface.password_input)))
                logger.success('Passed email and username input page.')
                break
            except:
                logger.error('Error message occurred after inputting email and username. Trying again.')
                continue

        new_driver.switch_to.window(new_driver.window_handles[0])
        wait.until(ec.element_to_be_clickable((By.XPATH, interface.password_input))).send_keys(self.password)
        wait.until(ec.element_to_be_clickable((By.XPATH, interface.repeat_password_input))).send_keys(self.password)
        wait.until(ec.element_to_be_clickable((By.XPATH, interface.save_password_button))).click()
        wait.until(ec.element_to_be_clickable((By.XPATH, interface.buy_land_button)))

        try:
            new_driver.get('https://www.sandbox.game/en/me/avatar/')
            wait.until(ec.element_to_be_clickable((By.XPATH, interface.avatar_randomize_button))).click()
            sleep(1)
            wait.until(ec.element_to_be_clickable((By.XPATH, interface.save_avatar_button))).click()
            logger.success('Avatar updated.')
        except:
            logger.error('Failed to update avatar.')

        return True


def init_selenium_driver(window_port: str):
    """
    Init selenium webdriver for connecting to Dolphin profile.
    :param window_port: str
    :return: selenium driver object
    """

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", f'127.0.0.1:{window_port}')
    if platform.system() == 'Windows':
        ser = Service("./chromedriver.exe")
        return webdriver.Chrome(service=ser, options=chrome_options)
    else:
        ser = Service("./mac_101_chromedriver")
        return webdriver.Chrome(service=ser, options=chrome_options)


if __name__ == "__main__":
    proxies_list = FileManager.read_txt_file('proxies')
    user_agents_list = FileManager.read_txt_file('user_agents')
    emails_list = FileManager.read_txt_file('emails')
    config = FileManager.read_config_file('config')

    if len(proxies_list) != len(user_agents_list) or len(proxies_list) != len(emails_list):
        logger.error('Amount of proxies is not matching amount of user agents or emails.')
        exit()

    dolphin_account = DolphinAccount(config['dolphin_login'], config['dolphin_pass'])
    authorised = dolphin_account.authorise_account()
    if not authorised:
        logger.error('Failed to authorize Dolphin account, check "config.json" file.')
        exit()

    i = 0
    while i < len(proxies_list):
        logger.info(f'Registering account {i + 1}/{len(proxies_list)}')

        dolphin_profile = DolphinProfile(user_agents_list[i], proxies_list[i])

        profile_created = dolphin_profile.create_new_profile(dolphin_account.authorization_token)
        if not profile_created:
            logger.error('Failed to create Dolphin profile.')
            exit()
        else:
            logger.success('Dolphin profile created.')

        profile_started = dolphin_profile.start_profile()
        if not profile_started:
            logger.error('Failed to start Dolphin profile. Make sure that Dolphin is running an proxies are legit.')
            exit()
        else:
            logger.success('Dolphin profile started.')

        driver = init_selenium_driver(str(dolphin_profile.window_port))
        metamask_account = MetamaskAccount(config['metamask_pass'])
        metamask_registered = metamask_account.register_metamask(driver)
        if not metamask_registered:
            logger.error('Failed to register metamask account. Make sure you have added an extension to Dolphin.')
            exit()
        else:
            logger.success('Metamask account registered.')

        sandbox_account = SandboxAccount(emails_list[i])
        sandbox_registered = sandbox_account.register_sandbox_account(driver, str(dolphin_profile.window_port))
        if not sandbox_registered:
            logger.error('Failed to register sandbox account.')
            exit()
        else:
            logger.success('Sandbox account registered.')

        FileManager.append_txt_file('registered_accounts', f'{sandbox_account.username}:{sandbox_account.email}'
                                                           f':{sandbox_account.password}:{metamask_account.public_key}'
                                                           f':{metamask_account.seed_phrase}:{proxies_list[i]}'
                                                           f':{user_agents_list[i]}')
        logger.success('Data saved to txt file.')

        profile_stopped = dolphin_profile.stop_profile()
        if not profile_stopped:
            logger.error('Failed to stop Dolphin profile. You can do it manually.')
        else:
            logger.success('Dolphin profile stopped.')

        profile_deleted = dolphin_profile.delete_profile(dolphin_account.authorization_token)
        if not profile_deleted:
            logger.error('Failed to delete Dolphin profile. You can do it manually with care.')
        else:
            logger.success('Dolphin profile deleted.')

        i += 1
