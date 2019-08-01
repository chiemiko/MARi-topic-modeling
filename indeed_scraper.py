from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib.request
import re
import pandas as pd
from datetime import datetime


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


def is_good_response(resp):
    """
    Returns 'True' if the response seems to be HTML, 'False' otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. This function just prints them, but you can make it do anything.
    """
    print(e)


def get_names(url):
    """
    Downloads the page to create a beautiful soup object with html information
    """
    
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                response = resp.content
                
                if response is not None:
                    html = BeautifulSoup(response, 'lxml')
                    return html
            else:
                pass

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def get_url(city, role):
    """
    Gets the url for the city (ie 'San Francisco, California') and job role (ie 'Data Scientist')
    """
    search_city = ''
    search_state = ''
    location_string = ''
    search_role = ''
    
    '''Makes separate strings for city and state'''
    for i, word in enumerate(city.split()):
        if word[len(word)-1] == ',':
            for x in range(i+1):
                search_city = search_city + ' ' + city.split()[x]

            search_city = search_city[0:len(search_city)-1]

            for x in range(i+1,len(city.split())):
                search_state = search_state + ' ' + city.split()[x]

    for word in search_city.split():        
        location_string = location_string + '+' + word

    location_string = location_string[1:len(location_string)] + '%2C'
    
    for word in search_state.split():
        location_string = location_string + '+' + word
    
    '''Now for each city, search sites for each role in roles list'''

    for word in role.split():
        search_role = search_role + '+' + word
    search_role = search_role[1:len(search_role)]
    url = f'https://www.indeed.com/jobs?q={search_role}&l={location_string}'

    return url


def get_sub_urls(soup):
    '''Extracting list of job post urls for each search'''
    urls = []
    for item in soup.find_all('div', attrs={'class': 'title'}):
        for tag in item.find_all('a'):
            urls.append(tag.get('href'))
    return urls

def get_divs_from_sub_url(soup, company='', title= '', location='', post_date='', description=''):
    '''Extract information from divs of soup object'''
    
    '''Extraction of Companies'''
    for item in soup.find_all('div', attrs = {'class': 'jobsearch-CompanyAvatar-cta'}):
        company = item.text[21:len(item.text)]

    
    '''Extraction of position titles'''
    
    title = soup.title.text.split('-')[0]
    
    '''Extraction of job location'''

    location = soup.title.text.split('-')[len(soup.title.text.split('-'))-2].strip()
    
    '''Extraction of dates'''
    for item in soup.find_all('div', attrs = {'class': 'jobsearch-JobMetadataFooter'}):
        #print(item.text.split('-'))
        for item in item.text.split('-'):
            if 'today' in item or 'minute' in item or 'hour' in item or 'just posted' in item:
                post_date = '0'
            
            elif 'day' in item:
                post_date = item.split()[0]
                            
                
    '''Extraction of full job post'''
    list_desc = []
    description = ''
    for item in soup.findAll('div', attrs={'class': 'jobsearch-jobDescriptionText'}):
        for tag in item:

            list_desc.append(tag)
            
        '''To take out all of the tags'''
        for i, item in enumerate(list_desc):
            sub = re.sub(r'<\w*>', '', str(item))
            sub = re.sub(r'</\w*>', '', sub)
            description = description + ' \n ' + sub
    
    return company, title, location, post_date, description




if __name__ == '__main__':



    cities = ['San Francisco, California', 'Honolulu, Hawaii', 'New York, New York']

    roles = ['Data Scientist',
    'Data Analyst']
    #'Business Analyst',
    #'Business Intelligence',
    #'Data Engineer',
    #'Machine Learning Engineer',
    #'Machine Learning Scientist',
    #'Artificial Intelligence Researcher',
    #'Statistical Modeler']

    df_main = pd.DataFrame()
    for city in cities:
        for role in roles:
            url = get_url(city, role)
            print(url)
            soup = get_names(url)
            urls = get_sub_urls(soup)

            titles = []
            post_dates = []
            locations = []
            companies = []
            descriptions = []
            full_urls = []

            for item in urls:
                
                full_url = 'https://www.indeed.com' + item
                full_urls.append(full_url)
                soup = get_names(full_url)
                

                
                
                company, title, location, post_date, description = get_divs_from_sub_url(soup)
                
                
                titles.append(title)
                post_dates.append(post_date)
                locations.append(location)
                companies.append(company)
                descriptions.append(description)

            df = pd.DataFrame({
            "company": companies,
            "location": locations,
            "title": titles,
            "post_date": post_dates,
            "description": descriptions
            , "url": full_urls
            })

            print(df)
            frames = [df_main, df]
            df_main = pd.concat(frames)

    df_main.to_csv('data/indeed-' +str(datetime.now().month) + '-' + str(datetime.now().day) + '.csv', index=False)
                        

