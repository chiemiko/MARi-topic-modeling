from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from datetime import datetime
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
        location_string = location_string + '%20' + word

    location_string = location_string[3:len(location_string)] + '%2C'
        
    for word in search_state.split():
        location_string = location_string + '%20' + word
    
    '''Now for each city, search sites for each role in roles list'''
    
        
    for word in role.split():
        search_role = search_role + '%20' + word
    search_role = search_role[3:len(search_role)]
    url = f'https://www.linkedin.com/jobs/search?keywords={search_role}&location={location_string}%2C%20United%20States&trk=homepage-basic_jobs-search-bar_search-submit&redirect=false&position=1&pageNum=0'

    return url 

def get_divs(soup):
    urls = []
    soups = []
    companies = []
    titles = []
    descriptions = []
    locations = []
    post_dates = []
    
    '''Extract company names'''
    # for item in soup.find_all('a', attrs={'class': 'result-card__subtitle-link job-result-card__subtitle-link'}):        
        
    
    for item in soup.find_all('h4', attrs={'class': 'result-card__subtitle job-result-card__subtitle'}):
        companies.append(item.text)
        
    #print()
    #<h4 class="result-card__subtitle job-result-card__subtitle">
    
    '''Extract location'''

    for item in soup.find_all('span', attrs={'class': 'job-result-card__location'}):
        locations.append(item.text)
    
    '''Extract title information'''
    for item in soup.find_all('span', attrs={'class': 'screen-reader-text'}):
        titles.append(item.text)

    '''Extract post date of position'''
    for item in soup.find_all('time'):
        post_dates.append(item.get('datetime'))
    
    '''Extract descriptions'''
    for item in soup.find_all('p', attrs={'class': 'job-result-card__snippet'}):
        descriptions.append(item.text)
    
    '''Extract urls'''
    for item in soup.find_all('a', href=True):

        if item.get('href')[29:34] == '/view':
            new_url = item.get('href')
            urls.append(new_url)

    
    # Make a dataframe object out of a dictionary of arrays
    df = pd.DataFrame({
        "company": companies,
        "location": locations,
        "title": titles,
        "post_date": post_dates,
        "description": descriptions
        , "url": urls
    })
    
    return df
    
    

def add_full_desc(df):
    
    'Extracts full linkedin post info and adds to 5 columns to existing dataframe for city/role'
    
    full_job_desc = []
    seniority_level = []
    employment_type = []
    job_function = []
    industries = []
            
    for index, row in df.iterrows():
        soup = get_names(row[5])
                
        '''Extracting job post body'''
        info = get_linkedin_info(soup)
        full_job_desc.append(info['full_desc'])
                    
        if info['Seniority level'] is not None:
            seniority_level.append(info['Seniority level'])
        else:
            seniority_level.append('NA')
                
        if info['Employment type'] is not None:
            employment_type.append(info['Employment type'])
        else:
            employment_type.append('NA')
                
        if info['Job function'] is not None:
            job_function.append(info['Job function'])
        else:
            job_function.append('NA')
                
        if info['Industries'] is not None:
            industries.append(info['Industries'])
        else:
            industries.append('NA')
                
    df['full_desc'] = full_job_desc
    df['seniority_level']= seniority_level
    df['employment_type']= employment_type
    df['job_function']= job_function
    df['industries']= industries
    
    return df

def get_linkedin_info(soup):
    
    "takes soup object and turns into LinkedIn full description"
    additional_info = {}
    full_desc = ''
    if soup.find_all('p'):
        for item in soup.find_all('p'):
            full_desc = full_desc + item.text
            full_desc = full_desc + ' \n'
    
    additional_info['full_desc'] = full_desc

    '''Extracting Additional Categories from LinkedIn Post'''
    for item in soup.find_all('h3', attrs={'class': 'job-criteria__subheader'}):
        '''Make a library with the key names as the category (ie seniority level, industry, job functions, employment type)'''
        additional_info[item.text] = item.next_sibling.text
        
            
        item2 = item.next_sibling
        while item2.next_sibling is not None:
            additional_info[item.text] = additional_info[item.text] + ', ' + item2.next_sibling.text
            #print(additional_info[item])
            item2 = item2.next_sibling
        #print()
        
        
        
    return additional_info
            
if __name__ == '__main__':

    cities = ['San Francisco,California',
              'New York, New York',
              'Seattle, Washington',
              'Washington, DC',
              'Chicago, Illinois',
              'Atlanta, Georgia',
              'Portland, Oregon',
              'Honolulu, Hawaii']
    
    roles = ['Data Scientist',
    'Data Analyst',
    'Business Analyst',
    'Business Intelligence',
    'Data Engineer',
    'Machine Learning Engineer',
    'Machine Learning Scientist',
    'Artificial Intelligence Researcher',
    'Statistical Modeler']

    
    for role in roles:
        df_main = pd.DataFrame()
        for city in cities:
        
            url =get_url(city, role)
            print(url)
            soup = get_names(url)
            df = get_divs(soup)
            
            df = add_full_desc(df)
            
            frames = [df_main, df]
            result = pd.concat(frames)
            df_main = result
            print(df_main.shape)

        
        # save to csv
        df_main.to_csv('data/linkedin-' + role +' ' +str(datetime.now().month) + '-' + str(datetime.now().day) + '.csv', index=False)
