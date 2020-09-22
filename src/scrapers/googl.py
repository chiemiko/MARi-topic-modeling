from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import urllib.request

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
    Downloads the Google page to create a beautiful soup object with html information
    """
    
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                response = resp.content
                if response is not None:
                    html = BeautifulSoup(response, 'lxml')
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
    search_role = ''
        
    for word in role.split():
        search_role = search_role + '+' + word
    search_role = search_role[1:len(search_role)]
    
    for word in city.split():
        search_role = search_role + '+' + word
    url = f'https://www.google.com/search?q={search_role}&ibp=htl;jobs#fpstate=tldetail&htidocid=bNuueDIcYnkfbPOvAAAAAA%3D%3D&htivrt=jobs'
    # https://www.google.com/search?q=data+science+jobs+new+york,+new+york&ibp=htl;jobs#fpstate=tldetail&htidocid=bNuueDIcYnkfbPOvAAAAAA%3D%3D&htivrt=jobs

    return url 

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
            print('link:')
            print(url)
            print()
            soup = get_names(url)
            print('soup obhect: ')
            print(soup)
            print()
