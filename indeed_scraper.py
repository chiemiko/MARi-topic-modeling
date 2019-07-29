from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.request

import re


import pandas as pd



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
    Downloads the LinkedIn page to create a beautiful soup object with html information
    """
    
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                response = resp.content
                
                
                if response is not None:
                    html = BeautifulSoup(response, 'lxml')
                    #print(html)
                    return html
                # Raise an exception if we failed to get any data from the url
                #raise Exception('Error retrieving contents at {}'.format(url))

                
            else:
                pass

    except RequestException as e:
        # MAIN ERROR? 
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def get_url(city, role):
    
    '''gets the url for the city (ie 'San Francisco, California') and job role (ie 'Data Scientist')'''
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
                
                search_state = search_state + ' ' +city.split()[x]
                # search_state = search_state + ' ' + city.split()[x]
                        
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
    print(url)
    #https://www.indeed.com/jobs?q=data+scientist&l=new+york%2C+new+york
    #https://www.indeed.com/jobs?q=Data+Scientist&l=New+York%2C+York
    
    return url 

def get_divs(soup):
    for item in soup.find_all('script', attrs={'type': 'text/javascript'}):
        # <script type="text/javascript">
        #print(item.text.find_all('jobmap'))
        if re.search('jobmap', item.text):
            for item2 in re.split('jobmap', item.text):
                if item2[0] == '[':                    
                    print(item2.split(','))
                    print()

def get_divs2(soup):
    for item in soup.find_all('span',  attrs = {'class': 'company'}):
        print(item.text)
    
    
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
            url =get_url(city, role)
            print(url)
            soup = get_names(url)
            print('technique 1 results: ')
            get_divs(soup)  
            print('technique 2 results: ')
            get_divs2(soup)

