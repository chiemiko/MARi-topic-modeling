from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.request
import pandas as pd
import lxml
import boto

# s3_client = boto3.client('s3')

class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


def main_fx():
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
                # if is_good_response(resp):
                response = resp.content
                if response is not None:
                    html = BeautifulSoup(response, 'lxml')
                    return html

        except RequestException as e:
            # MAIN ERROR? 
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
            if word[len(word) - 1] == ',':
                for x in range(i + 1):
                    search_city = search_city + ' ' + city.split()[x]
                search_city = search_city[0:len(search_city) - 1]
                for x in range(i + 1, len(city.split())):
                    search_state = search_state + ' ' + city.split()[x]
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
        companies = []
        titles = []
        descriptions = []
        locations = []
        post_dates = []

        '''Extract company names'''
        for item in soup.find_all('h4', attrs={'class': 'result-card__subtitle job-result-card__subtitle'}):
            companies.append(item.text)
        '''Extract location'''
        for item in soup.find_all('span', attrs={'class': 'job-result-card__location'}):
            locations.append(item.text)
        '''Extract title information'''
        for item in soup.find_all('span', attrs={'class': 'screen-reader-text'}):
            titles.append(item.text)
        '''Extract post date of position'''
        for item in soup.find_all('time'):
            post_dates.append(item.get('datetime'))

        #'''Extract descriptions'''
        #for item in soup.find_all('p', attrs={'class': 'jobs-description-content__text'}):
            #descriptions.append(item.text)

        '''Extract urls'''
        for i, item in enumerate(soup.find_all('a', href=True)):
            if item.get('href')[29:34] in ['/view', 'view/']:
                new_url = item.get('href')
                # if no url present, append None
                if not new_url:
                    print(f"item url that's broken for: {item}")
                    new_url = None    
                urls.append(new_url)
                
        # Make a dataframe object out of a dictionary of arrays

        for item in [companies, locations, titles, post_dates, urls]:
            print(len(item))

        df = pd.DataFrame({
            "company": companies,
            "location": locations,
            "title": titles,
            "post_date": post_dates,
            #"description": descriptions,
            "url": urls
        })
        return df


    def parse_description(df):
        """Extracts full LinkedIn post info and adds to 5 columns to existing DataFrame for city/role"""

        full_job_desc = []
        seniority_level = []
        employment_type = []
        job_function = []
        industries = []

        # iterates over list of urls from urls column in df
        for index, row in df.iterrows():
            if row[4]:
                soup = get_names(row[4])
                
                '''Extracting job post body'''
                info = get_linkedin_info(soup)
                full_job_desc.append(info['full_desc'])

                if 'Seniority level' in info.keys():
                    seniority_level.append(info['Seniority level'])
                else:
                    seniority_level.append('NA')

                if 'Employment type' in info.keys():
                    employment_type.append(info['Employment type'])
                else:
                    employment_type.append('NA')

                if 'Job function' in info.keys():
                    job_function.append(info['Job function'])
                else:
                    job_function.append('NA')

                if 'Industries' in info.keys():
                    industries.append(info['Industries'])
                else:
                    industries.append('NA')
            else:
                full_job_desc.append(None)
                seniority_level.append(None)
                employment_type.append(None)
                job_function.append(None)
                industries.append(None)

        df['full_desc'] = full_job_desc
        df['seniority_level'] = seniority_level
        df['employment_type'] = employment_type
        df['job_function'] = job_function
        df['industries'] = industries
        return df

    def get_linkedin_info(soup):
        """Takes soup object and turns it into LinkedIn full description"""
        additional_info = {}
        full_desc = ''
        if soup.find_all('p'):
            for item in soup.find_all("div", {"class": "description__text"}):
                full_desc = full_desc + item.text
                full_desc = full_desc + ' \n'
        else:
            full_desc = 'NA'
        additional_info['full_desc'] = full_desc

        '''Extracting Additional Categories from LinkedIn Post'''
        for item in soup.find_all('h3', attrs={'class': 'job-criteria__subheader'}):
            '''Make a library with key names as category (ie seniority level, industry, job functions, employment type)'''
            additional_info[item.text] = item.next_sibling.text

            item2 = item.next_sibling
            while item2.next_sibling is not None:
                additional_info[item.text] = additional_info[item.text] + ', ' + item2.next_sibling.text
                item2 = item2.next_sibling

        return additional_info

    cities = ['San Francisco, California',]
            #   'New York, New York',
            #   'Seattle, Washington',
            #   'Washington, DC',
            #   'Chicago, Illinois',
            #   'Atlanta, Georgia',
            #   'Portland, Oregon',
            #   'Honolulu, Hawaii']


    roles = ['Data Scientist',
    'Data Analyst',
    'Business Analyst',
    'Business Intelligence',
    'Data Engineer',
    'Machine Learning Engineer',
    'ML Engineer',
    'Artificial Intelligence Researcher',
    'Statistical Modeler',
    'Research Intern',
    'Software Engineer',
    'Full Stack Engineer',
    'Computer Vision Engineer',
    'Risk Analyst']

    df_main = pd.DataFrame()
    
    start = datetime.now()
    for role in roles:
        for city in cities:
            url = get_url(city, role)
            print(url)
            soup = get_names(url)
            df = get_divs(soup)
            df = parse_description(df)
            df['search_role'] = len(df.index)*[role]
            df['search_city'] = len(df.index)*[city]

            # df = add_full_desc(df)
            frames = [df_main, df]
            df_main = pd.concat(frames)
    
    end = datetime.now()
    # save to csv
    # df_main.to_csv('../../data/raw/2020/linkedin-' +str(datetime.now().month) + '-' + str(datetime.now().day) + '-raw.csv', index=False)     
    return df_main
    print(f"final time to scrape: {end-start}")

def lambda_handler(event, context):
    main_fx()

    return{
        'statusCode': 200, 
        'body': "FINALIZED I THINK"    
        }

# if __name__ == '__main__':
#     main_fx()
