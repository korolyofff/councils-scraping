from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import  InvalidArgumentException
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from time import sleep
from to_csv import csv_writer
import re
import json
import logging


class Cliker:
    def __init__(self, proxy):
        self.options = None
        if proxy != '':
            self.options = {
                'proxy': {
                    'http': 'http://{}'.format(proxy),
                    'https': 'https://{}'.format(proxy),
                    'no_proxy': 'localhost,127.0.0.1,dev_server:8080'
                }
            }

        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("intl.accept_languages", 'en-us')
        firefox_profile.update_preferences()

        fireFoxOptions = webdriver.FirefoxOptions()
        # fireFoxOptions.headless = True

        try:
            self.driver = webdriver.Firefox(seleniumwire_options=self.options, firefox_profile=firefox_profile,
                                            firefox_options=fireFoxOptions)
            logging.basicConfig(filename='scraper.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
            logging.info('Scraper started')
            self.driver.maximize_window()

        except InvalidArgumentException:
            logging.error('Firefox not opened')
            raise exit()

    def filter_and_search(self, url, date, council_name):
        self.url = url
        self.driver.get(self.url)
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#advancedSearchForm > div.buttons > input.button.primary')))
        except:
            print('No such element exception')
            pass

        keyword = 'residential'
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        keyword_tag = soup.find('input', {'name': 'searchCriteria.description'})
        if keyword_tag != None:
            keyword_field = self.driver.find_element_by_xpath(xpath_soup(keyword_tag))
            keyword_field.send_keys(keyword)
        else:
            logging.warning(' 61 Failed to scrape {} : {}'.format(council_name, self.url))
            return 'None'

        for date_from, date_to in date.items():
            date_recieved_from_tag = soup.find('input', {'name': 'date(applicationReceivedStart)'})
            date_recieved_to_tag = soup.find('input', {'name': 'date(applicationReceivedEnd)'})
            if date_recieved_from_tag != None and date_recieved_to_tag != None:
                date_recieved_from_field = self.driver.find_element_by_xpath(xpath_soup(date_recieved_from_tag))
                date_recieved_to_field = self.driver.find_element_by_xpath(xpath_soup(date_recieved_to_tag))
                date_recieved_from_field.send_keys(date_from)
                date_recieved_to_field.send_keys(date_to)
            else:
                logging.warning('73 Failed to scrape {} : {}'.format(council_name, self.url))
                return 'None'
        try:
            # click "Search" button
            self.driver.find_element_by_css_selector('#advancedSearchForm > div.buttons > input.button.primary').click()
        except NoSuchElementException:
            logging.warning(' 79 Failed to scrape {} : {}'.format(council_name, self.url))
            return 'None'

    def create_list_objects(self, council_name):
        self.urls = []
        self.council_name = council_name

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#resultsPerPage')))
        except:
            print('No such element exception')
            pass

        # 100 objects per page option
        try:
            self.driver.find_element_by_css_selector('#resultsPerPage').click()
            sleep(0.5)
            self.driver.find_element_by_css_selector('#resultsPerPage > option:nth-child(5)').click()
            self.driver.find_element_by_css_selector('#searchResults > input.button.primary').click()
        except:
            logging.warning('100 Failed to scrape {} : {}'.format(council_name, self.url))
            return 'None'

        sleep(2)

        while True:
            try:
                sleep(1)
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#searchResults > input[type=hidden]:nth-child(3)')))
                except:
                    print('No such element exception')
                    pass

                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                objects = soup.find_all('li', 'searchresult')
                for object in objects:
                    site_domain = re.findall(r'(https://.+?)/', self.url)[0]
                    link = site_domain + object.findChild('a')['href']
                    self.urls.append(link)

                self.driver.find_element_by_css_selector('#searchResultsContainer > p.pager.top > a.next').click()

            except NoSuchElementException:
                break

        scraper = Scraper(self.urls, self.driver, self.council_name)
        scraper.scrape_summary()


class Scraper():
    def __init__(self, urls, driver, council_name):
        self.council_name = council_name
        self.urls = urls
        self.driver = driver

    def scrape_summary(self):
        for url in self.urls:
            data = [[]]

            self.driver.get(url)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#simpleDetailsTable')))
            except:
                print('No such element exception')
                pass

            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            data[0].append(self.scrape_reference(soup))
            data[0].append(self.scrape_application_validated(soup))
            data[0].append(self.scrape_address(soup))
            data[0].append(self.scrape_proposal(soup))
            data[0].append(self.scrape_status(soup))

            try:
                self.driver.find_element_by_css_selector('#subtab_details > span').click()

                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#applicationDetails')))
                except:
                    print('No such element exception')
                    pass

                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                data[0].append(self.scrape_applicant_name(soup))
                data[0].append(self.scrape_applicant_address(soup))
                data[0].append(self.scrape_agent_name(soup))
                data[0].append(self.scrape_agent_company_name(soup))
                data[0].append(self.scrape_agent_address(soup))

            except:
                for _ in range(5):
                    data[0].append('')

            try:
                self.driver.find_element_by_css_selector('#subtab_contacts > span').click()

                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'table.agents')))
                except:
                    print('No such element exception')
                    pass

                soup = BeautifulSoup(self.driver.page_source, 'lxml')

                data[0].append(self.scrape_agent_phone_number(soup))
                data[0].append(self.scrape_agent_email(soup))

            except:
                data[0].append('')
                data[0].append('')

            csv_writer(data, '{}.csv'.format(self.council_name))

    # Summary information
    def scrape_reference(self, soup):
        reference = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Reference' in row:
                reference = row.replace('Reference : ', '')
                reference = reference.replace('Reference:', '')

                break

        return reference

    def scrape_application_validated(self, soup):
        application = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Application Validated' in row:
                application = row.replace('Application Validated : ', '')
                application = application.replace('Application Validated:', '')

                break

        return application

    def scrape_address(self, soup):
        address = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Address' in row:
                address = row.replace('Address : ', '')
                address = address.replace('Address:', '')

                break

        return address

    def scrape_proposal(self, soup):
        proposal = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Proposal' in row:
                proposal = row.replace('Proposal : ', '')
                proposal = proposal.replace('Proposal:', '')

                break

        return proposal

    def scrape_status(self, soup):
        status = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Status' in row:
                status = row.replace('Status : ', '')
                status = status.replace('Status:', '')

                break

        return status

    # Further information
    def scrape_applicant_address(self, soup):
        reference = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Reference' in row:
                reference = row.replace('Applicant Address : ', '')
                reference = reference.replace('Applicant Address:', '')
                break

        return reference

    def scrape_applicant_name(self, soup):
        name = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Applicant Name' in row:
                name = row.replace('Applicant Name : ', '')
                name = name.replace('Applicant Name:', '')

                break

        return name

    def scrape_agent_name(self, soup):
        agent_name = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Agent Name' in row:
                agent_name = row.replace('Agent Name : ', '')
                agent_name = agent_name.replace('Agent Name:', '')
                break

        return agent_name

    def scrape_agent_company_name(self, soup):
        name = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Agent Company Name' in row:
                name = row.replace('Agent Company Name : ', '')
                name = name.replace('Agent Company Name:', '')

                break

        return name

    def scrape_agent_address(self, soup):
        address = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Agent Address' in row:
                address = row.replace('Agent Address : ', '')
                address = address.replace('Agent Address:', '')

                break

        return address

    # Contact information
    def scrape_agent_phone_number(self, soup):
        phone = ''
        scrape_data = soup.find_all('tr')
        for data in scrape_data:
            field = data.findChild('th').text
            value = data.findChild('td').text
            row = ' '.join(('{}:{}'.format(field, value)).split())
            if 'Phone' in row:
                phone = row.replace('Phone : ', '')
                phone = phone.replace('Mobile Phone:', '')
                phone = phone.replace('Phone:', '')

                break

        return phone

    def scrape_agent_email(self, soup):
        email = ''
        scrape_data = soup.find('table', 'agents')
        try:
            field = scrape_data.findChild('th').text
            value = scrape_data.findChild('td').text

        except AttributeError:
            return email

        row = ' '.join(('{}:{}'.format(field, value)).split())

        if 'EMAIL' in row or 'Email' in row:
            email = row.replace('EMAIL : ', '')
            email = email.replace('EMAIL:', '')
            email = email.replace('Email:', '')
            email = email.replace('Email : ', '')

            return email

        return email

def xpath_soup(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
            )
        )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def main():
    clicker = Cliker('')
    dates = [{'01/01/2010': '31/12/2011'}, {'01/01/2012': '31/12/2013'}, {'01/01/2014': '31/12/2015'},
             {'01/01/2016': '31/12/2018'}, {'01/01/2019': '28/10/2020'}]
    with open('councils.json', 'r') as f:
        datas = json.load(f)
        for data in datas['root']['row']:
            for date in dates:
                search = clicker.filter_and_search(data['BaseSearchURL'], date, data['Council'])
                if search != 'None':
                    clicker.create_list_objects(data['Council'])
                else:
                    break
            logging.info('Sucessfilly Scraped {} : {}')
        logging.info('Scraper finished job')


if __name__ == '__main__':
    main()
