import os
import yaml

from datetime import datetime
from json import dump
from selenium import webdriver
import shutil

import logging

import undetected_chromedriver as uc
from undetected_chromedriver import Chrome

from run_func import shopper_actions_by_steps
from campaigns.campaigns_to_test import list_of_campaigns_to_test


def browser_setup(browser_name='chrome') -> webdriver:
    """
    Sets up a WebDriver instance for the specified browser with desired window size and page loading strategy.
    FIREFOX requires to set executable_path
    Args:
          browser_name (str, optional): The name of the browser to use. Defaults to "chrome".
    Returns:
          webdriver: A WebDriver instance for the specified browser.
    """

    if browser_name.lower() == 'chrome':
        options = webdriver.ChromeOptions()
        # ("--start-maximized")
        # options.add_argument('--window-size=1400,1000')
        # If run in Docker, below line is to be uncommented
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.page_load_strategy = 'eager'
        driver = webdriver.Chrome(options=options)

        # Create a unique user data directory. This is for Docker
        # Or any other suitable path
        user_data_dir = '/tmp/chrome_user_data'
        # create folder if it doesn't exist already
        os.makedirs(user_data_dir,exist_ok=True)
        options.add_argument(f'--user-data-dir={user_data_dir}')

        # https://scrapfly.io/blog/web-scraping-without-blocking-using-undetected-chromedriver/
        # https://www.browserscan.net/bot-detection
        # options = uc.ChromeOptions()
        # driver = uc.Chrome(options=options)
    elif browser_name.lower() == 'firefox':
        options = webdriver.FirefoxOptions()
        service = webdriver.FirefoxService(
            executable_path="/snap/bin/geckodriver")
        options.add_argument('--window-size=1400,1000')
        # options.add_argument('--headless')
        # https://www.selenium.dev/documentation/webdriver/drivers/options/#pageloadstrategy
        options.page_load_strategy = 'eager'
        driver = webdriver.Firefox(options=options, service=service)
    elif browser_name.lower() == 'safari':
        # For Safari, you might need to adjust based on your environment
        # and the specific version of Safari you are using.
        # This is a basic example.
        driver = webdriver.Safari()
    else:
        raise ValueError(f'Unsupported browser: {browser_name}')

    return driver


def complete_purchase_and_save_results():
    """
    This function iterates through a list of campaigns, performs purchase simulations
    using the `shopper_actions_by_steps` function for each user journey within a campaign,
    and saves the results in JSON format.

    It performs the following steps:
        1. Iterates through a list of YAML files specifying user journeys for each campaign.
        2. For each campaign:
            - Opens the corresponding YAML file and loads the user journeys.
            - Iterates through each user journey within the campaign.
                - Creates a folder to store the results for the current campaign (if it doesn't exist).
                - Creates a filename with a timestamp for the current test.
                - Configures logging to suppress excessive output and save test results to a log file.
                - Logs a message indicating the start of the test for the current campaign.
                - Simulates the purchase process using the `shopper_actions_by_steps` function, handling any exceptions.
                - Logs a message indicating the completion of the test for the current campaign.
                - Updates the timestamp for the current user journey.
                - Saves the test results (including user journeys and timestamps) in a JSON file.
                - Prints the test results (likely for debugging purposes).
    """
    run_test_for = list_of_campaigns_to_test
    driver = browser_setup()

    for campaign in run_test_for:
        results = []

        # Open YAML file specifying user journeys for the current campaign
        with open(f'campaigns/{campaign}', 'r') as c:
            tests = yaml.safe_load(c)

        # Unpack YAML as dictionary, extract first line - login
        campaign_login = list(tests.keys())[0]
        shopper_steps = tests.get(campaign_login)[0].get

        for user_journey in shopper_steps('test_case'):
            # Create a folder name to store the results for the current campaign
            folder_name = f"reports/{shopper_steps('campaign_id')}"
            # Create a file name with timestamp for the current test
            file_name = datetime.now().strftime('%d%m%Y-%H%M')
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)

            # Configure logging to save test results in a log file
            logging.getLogger('selenium').setLevel(logging.CRITICAL)
            logging.basicConfig(
                filename=f'reports/{file_name}.log',
                level=logging.DEBUG,
                format='%(levelname)s (%(asctime)s) - %(message)s'
            )
            logging.info(
                f"Running test for campaign id: {shopper_steps('campaign_id')}"
            )

            try:
                # Simulate purchase process using shopper_actions_by_steps
                # function
                result = shopper_actions_by_steps(
                    driver,
                    shopper_steps('campaign_id'),
                    user_journey
                )
                results.append(result)
            except Exception as er:
                print()
                logging.error(
                    f"ERROR ({er}) test for campaign id: {shopper_steps('campaign_id')}"
                )
                continue
            logging.info(
                f"Completed test for campaign id: {shopper_steps('campaign_id')}"
            )

            # Save the test results in JSON file
            with open(f'{folder_name}/{file_name}.json', 'w') as test_file:
                dump(results, test_file, indent=4, ensure_ascii=False)
            # Print the test results (for debugging purposes)
            print(tests)

    driver.close()
    driver.quit()


if __name__ == '__main__':
    complete_purchase_and_save_results()
