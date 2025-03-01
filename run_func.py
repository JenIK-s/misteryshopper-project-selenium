from typing import Dict

import os
import time
import urllib.parse
from datetime import datetime
from time import sleep

import blinker
from selenium import webdriver
# from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from seleniumwire import webdriver

import logging


def css_selector_or_xpath(driver, param):
    """
    Attempts to find an element using either CSS Selector or XPath.

    This function prioritizes CSS Selector for efficiency.

    Args:
        driver: The Selenium WebDriver instance.
        param: The CSS selector or XPath expression to locate the element.

    Returns:
        By: The type of locator (CSS Selector or XPath) used to find the element.
    """
    try:
        driver.find_element(By.CSS_SELECTOR, param).click()
        logging.info(f'CSS_SELECTOR found')
        return By.CSS_SELECTOR
    except:
        driver.find_element(By.XPATH, param).click()
        logging.info(f'XPATH found')
        return By.XPATH


def click_element(driver, step):
    """
    Clicks on an element on the web page using either CSS Selector or XPath.

    Args:
        driver: The Selenium WebDriver instance.
        step: A dictionary containing the step information,
              including the 'selector' for the element.

    Raises:
        NoSuchElementException: If the element cannot be found using
                                either CSS Selector or XPath.
        """
    try:
        driver.find_element(By.CSS_SELECTOR, step['selector']).click()
        logging.info(f'CSS_SELECTOR')
    except:
        driver.find_element(By.XPATH, step['selector']).click()
        logging.info(f'XPATH')


def text_input_click_and_clear(driver, by, step):
    """
    Clicks, clears, and enters text into a form field.

    Args:
        driver: The WebDriver instance.
        by: The method to locate the element (By.CSS_SELECTOR or By.XPATH).
        step: A dictionary containing step information, including the selector.
    """
    text_input = driver.find_element(by, step['selector'])
    text_input.click()
    text_input.clear()
    sleep(0.1)
    webdriver.ActionChains(driver).send_keys_to_element(
        text_input, step['text']
    ).pause(0.2).perform()
    # The below code is to input letter-by-letter
    # for character in step['text']:
    #     webdriver.ActionChains(driver).send_keys(text_input, character).pause(0.1).perform()
    logging.info(f"Text input: {step['text']}")


def add_subid_to_url(url, data):
    """
    Adds a SUBID parameter with the current Unix timestamp to the URL and saves it in the data dictionary.
    """
    parsed_url = urllib.parse.urlparse(url)
    query_params = dict(urllib.parse.parse_qs(parsed_url.query))
    subid_value = str(int(time.time()*1000))  # Generate Unix timestamp
    query_params['subid'] = subid_value  # Add SUBID
    new_query_string = urllib.parse.urlencode(query_params, doseq=True)
    data['subid'] = subid_value  # Save SUBID in data dictionary
    return urllib.parse.urlunparse(parsed_url._replace(query=new_query_string))


def save_specific_cookies(driver, data: Dict) -> None:
    """
    Saves specified cookies in the data dictionary.

    Args:
        driver: WebDriver instance.
        data: Dictionary to store cookies.
    """
    list_of_required_cookies = [
        'admitad_uid',
        'admitad_aid',
        'tagtag_aid',
        'deduplication_cookie',
        '_source',
        'deduplication_source',
        '_aid',
    ]
    for cookie_name in list_of_required_cookies:
        cookie_value = driver.get_cookie(cookie_name)
        if cookie_value:
            data['cookies'][cookie_name] = cookie_value['value']


def save_first_redirect_url(driver, data: Dict) -> None:
    """
    Extracts and saves parameters from the first redirect URL.

    Args:
        driver: WebDriver instance.
        data: Dictionary to store extracted parameters.
    """
    url_parameters_to_extract = [
        'utm_source',
        'admitad_uid',
        'admitad_aid',
        'tagtag_aid',
        'tagtag_uid',
        'source',
    ]
    data['final_url'] = driver.current_url
    # Parse parameters from final_url
    parsed_url = urllib.parse.urlparse(data['final_url'])
    data['query_params'] = urllib.parse.parse_qs(parsed_url.query)
    for param in url_parameters_to_extract:
        if param in data['query_params']:
            data[param] = data['query_params'][param][0]


def extract_order_id_from_url(url, search_list=None):
    """
    Extracts the order ID from the URL, if present, using a list of search parameters.

    Args:
        url: The URL to extract the order ID from.
        search_list: A list of query parameters or path component patterns to search for.
                     If None, defaults to ['order_id', 'order', 'transaction_id'].

    Returns:
        The order ID if found, otherwise None.
    """
    if search_list is None:
        search_list = ['order_id', 'order', 'transaction_id', 'ORDER_ID']
    try:
        parsed_url = urllib.parse.urlparse(url)
        # Check query parameters
        query_params = urllib.parse.parse_qs(parsed_url.query)
        for param in search_list:
            order_id = query_params.get(param, [None])
            if order_id:
                return order_id
        # Check path components
        path_components = parsed_url.path.strip('/').split('/')
        for component in path_components:
            if any(pattern in component for pattern in search_list):
                return component
        return None  # Order ID not found in URL
    except Exception as e:
        logging.error(f"Error extracting order ID from URL: {e}")
        return None


def shopper_actions_by_steps(
        driver: webdriver.Chrome,
        campaign_id: int,
        user_journey: Dict,
        search_list: list = None) -> Dict:
    """
    Executes a user journey defined in a dictionary format using a WebDriver instance.

    This function simulates a user's journey through a website by following a series of steps
    provided in the 'user_journey' dictionary. It interacts with web elements based on
    actions specified in the steps and captures various details during the process.

    Args:
        driver (webdriver.Chrome): An instance of the WebDriver (e.g., Chrome) used to
                                  interact with the web page.
        campaign_id (int): The campaign ID associated with the user journey.
        user_journey (Dict): A dictionary containing the user journey information,
                             including:
                                - 'title' (str): The name of the user journey test case.
                                - 'steps' (list): A list of dictionaries, where each dictionary
                                                 represents a single step in the journey and
                                                 contains the following keys:
                                                    - 'action' (str): The action to perform (e.g., "goto", "click_object", "type_in_data").
                                                    - 'url' (str, optional): The URL to open for "goto" actions.
                                                    - 'selector' (str): The CSS selector or XPath expression to locate
                                                                     web elements for click, type, etc. actions.
                                                    - 'text' (str, optional): The text to enter for "type_in_data" actions.
                                                    - 'element' (str, optional): The value to select from a dropdown menu
                                                                     (used in "drop_down_menu" actions).
        search_list (list, optional): A list of query parameters or path component patterns to
                                      search for when extracting the order ID from the URL.
                                      If None, defaults to ['order_id', 'order', 'transaction_id'].

    Returns:
        dict: A dictionary containing data collected during the user journey, including:
            - 'datetime' (str): Timestamp of the user journey execution.
            - 'test_name' (str): The name of the user journey test case.
            - 'initial_link' (str): The initial URL of the user journey.
            - 'final_url' (str): The final URL reached after completing the steps.
            - 'query_params' (dict): A dictionary of query parameters parsed from the final URL.
            - 'cookies' (dict): A dictionary containing captured cookies (focusing on Admitad cookies).
            - 'subid' (str): The SUBID value added to the URL.
            - 'Cart' (str, optional): Information about the shopping cart (if applicable).
            - 'Thank_you_page' (str, optional): URL of the 'thank you' page (if applicable).
            - 'Order_number' (str, optional): Order number (if applicable).
            - 'Request_Response' (str, optional): Any request/response data captured during the journey (if applicable).
    """
    start_time = time.time()
    # Test results template, data to collect
    data = {
        'datetime': str(datetime.now().strftime('%d.%m.%Y-%H:%M:%S')),
        'test_name': user_journey.get('title'),
        'initial_link': user_journey.get('steps')[0]['url'],
        'final_url': '',
        'query_params': '',
        'cookies': {},
        'subid': '',
        'Cart': '',
        'Thank_you_page': '',
        'Order_number': '',
        'Request_Response': '',
    }

    # Add SUBID to the initial link and save it in the data dictionary
    initial_url = user_journey.get('steps')[0]['url']
    modified_url = add_subid_to_url(initial_url, data)  # Add SUBID and save it
    user_journey.get('steps')[0]['url'] = modified_url  # Update the URL in the user journey

    first_redirect = True

    for step in user_journey.get('steps'):
        action = step['action']
        # Opening required URL
        if action == 'goto':
            logging.info(f"Open URL: {step['url']}")
            driver.get(step['url'])
            sleep(3)
            driver_cookie = driver.get_cookies()
            # Collect and save only first redirect in the user's journey within one testcase
            if first_redirect:
                save_first_redirect_url(driver, data)
                save_specific_cookies(driver, data)
                first_redirect = False
            logging.info(f"Redirect URL: {data['final_url']}")
            logging.info(f"Link parameters: {data['query_params']}")
            logging.info(f'All cookies: {driver_cookie}')
            logging.info(f"Admitad cookies: {data['cookies']}")
        # Set additional time for page to load
        elif action == 'wait':
            logging.info(f'Awaiting some event')
            duration = int(step['value'])
            sleep(duration)
            logging.info(f'Waited for {duration} secs')
            logging.info(f'Current page URL: {driver.current_url}')
        elif action == 'tab_key':
            logging.info(f'Attempting TAB to jump')
            webdriver.ActionChains(driver).send_keys(Keys.TAB).perform()
            logging.info(f'Success TAB to jump')
            sleep(1)
        elif action == 'enter_key':
            logging.info(f'Attempting ENTER to confirm action')
            webdriver.ActionChains(driver).send_keys(Keys.ENTER).perform()
            logging.info(f'Success ENTER to confirm action')
            sleep(1)
        elif action == 'arrow_down':
            logging.info(f'Attempting ARROW DOWN')
            webdriver.ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
            logging.info(f'Success ARROW DOWN')
            sleep(1)
        elif action == 'arrow_up':
            logging.info(f'Attempting ARROW UP')
            webdriver.ActionChains(driver).send_keys(Keys.ARROW_UP).perform()
            logging.info(f'Success ARROW UP')
            sleep(1)
        elif action == 'scroll':
            sleep(1)
            driver.execute_script('window.scrollBy(0, 250)')
            logging.info(f'Scroll the page down')
            sleep(1)
        # Clicking required object
        elif action in [
            'close_popup_window', 'click_object', 'click_add_to_cart',
            'click_confirm_order', 'click_confirm_payment',
        ]:
            logging.info(f'Try to {action}')
            for request in driver.requests:
                if request.response and any(
                        domain in request.url for domain in ['aflink.ru',
                                                             'ad.admitad.com',
                                                             'tjzuh.com',
                                                             'z.asbmit.com',
                                                             'pafutos.com',
                                                             'lenkmio.com',
                                                             ]):
                    logging.info(f"Captured request to {request.url}:")
                    logging.info(f" - Method: {request.method}")
                    logging.info(f" - Headers: {request.headers}")
                    logging.info(
                        f" - Response status code: {request.response.status_code}")
                    logging.info(
                        f" - Response body: {request.response.body.decode('utf-8')}")
            try:
                (driver.find_element(css_selector_or_xpath(
                    driver, step['selector']))
                 .click())
                logging.info(f'All cookies: {driver_cookie}')
                logging.info(f"Admitad cookies: {data['cookies']}")
            except:
                button = webdriver.ActionChains(driver).send_keys(Keys.ESCAPE)
                button.perform()
                logging.info(f'Object to click not found, attempted ESCAPE key')
                logging.info(f'All cookies: {driver_cookie}')
                logging.info(f"Admitad cookies: {data['cookies']}")
            sleep(3)
        # Typing in any fields
        elif action == 'type_in_data':
            logging.info(f'Perform type-in')
            try:
                logging.info(f'Text element by XPATH')
                text_input_click_and_clear(driver, By.XPATH, step)
            except:
                logging.info(f'Text element by CSS_SELECTOR')
                text_input_click_and_clear(driver, By.CSS_SELECTOR, step)
            sleep(0.5)
        # Selecting option from drop-down menu
        elif action == 'drop_down_menu':
            logging.info(f'Searching for selector')
            try:
                element = driver.find_element(By.CSS_SELECTOR, step['selector'])
                select = Select(element)
                select.select_by_value(step['element'])
                logging.info(f'CSS_SELECTOR found')
            except:
                element = driver.find_element(By.XPATH, step['selector'])
                select = Select(element)
                select.select_by_value(step['element'])
                logging.info(f'XPATH found')
            sleep(2)
        # Making required screenshots, file name contains date and time
        elif action == 'make_screenshot':
            folder_name = f'reports/{campaign_id}'
            file_name = datetime.now().strftime('%d%m%Y-%H%M%S')
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            driver.save_screenshot(f'{folder_name}/{file_name}.png')
            logging.info(f'Screenshot saved in folder')
        elif action == 'capture_order_confirmation':
            order_id = extract_order_id_from_url(driver.current_url, search_list)
            if order_id:
                data['Order_number'] = order_id
                logging.info(f"Captured order ID from URL: {order_id}")
            else:
                pass
        sleep(2)
    end_time = time.time()
    # Test time measurement and logging
    execution_time = end_time - start_time
    logging.info(f'Execution time: {execution_time} sec')
    print(execution_time)
    return data
