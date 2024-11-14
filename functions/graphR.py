from bs4 import BeautifulSoup
from builtins import str
from bs4 import BeautifulSoup
from mechanize import Browser
from openai import OpenAI
import json
import os
import math
from bs4 import BeautifulSoup
import requests

def initialize_browser():
    """Initialize the browser with specific headers."""
    b = Browser()
    b.set_handle_robots(False)
    b.addheaders = [
        ('Referer', 'https://pubmed.ncbi.nlm.nih.gov'), 
        ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    ]
    return b

def validateLink(profile_link: str) -> dict:
    if all(substring in profile_link for substring in ['cauthor_id=', 'term=', 'https://pubmed.ncbi.nlm.nih.gov']):
        try:
            # Send a GET request to the URL
            response = requests.get(profile_link)

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                return {
                    'status' : True,
                    'message' : f'VALID URL. STATUS CODE [{response.status_code}]'
                }
            else:
                return {
                    'status' : False,
                    'message' : f'INVALID URL. STATUS CODE [{response.status_code}]'
                }
            
        except requests.exceptions.RequestException as e:
            return {
                'status' : False,
                'message' : f"UKNOWN ERROR OCCURED {e}"
            }
        
    else:
        return {
            'status' : False,
            'message' : f"INVALID URL ENTERED"
        }
    
def parseUserInput(profile_link: str, abstract_view=True) -> str:
    targetPageSize = 20
    targetProfileName = [x for x in profile_link.split("&") if 'term=' in x][0]
    targetAuthorID = [x for x in profile_link.split("&") if 'cauthor_id=' in x][0]
    if abstract_view:
        return f"https://pubmed.ncbi.nlm.nih.gov/?size={targetPageSize}" + f"&{targetProfileName}&" + targetAuthorID + "&format=abstract"
    else:
        return f"https://pubmed.ncbi.nlm.nih.gov/?size={targetPageSize}" + f"&{targetProfileName}&" + targetAuthorID

def FetchAndParse(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup

def pubmed_crawl(page_soup):
    papers = page_soup.find_all('article', {"class" : "article-overview"})
    results = {}
    for paper in papers:
        # Get paper name
        paper_name = paper.find('h1',{'class':'heading-title'}).find('a').get_text(strip=True)

        # Get authors name
        authors_list = []
        for authors in paper.find_all('span', {'class' : 'authors-list-item'}):
            try:
                author_name = authors.find('a', {'class' : 'full-name'}).get_text(strip=True)
                authors_list += [author_name]
            except Exception as e:
                continue

        abstract_content = {}
        try:        
            abstract_area = paper.find_all('div',{'class':'abstract'})[0].find('div',{"class":"abstract-content selected"})
            abstract_structure = abstract_area.find_all('p')

            if len(abstract_structure) == 0: # Abstract not found
                pass
            elif len(abstract_structure) == 1: # Unstructured Abstract
                abstract_content["Abstract"] = abstract_area.get_text(strip=True)
            else:
                for sections in abstract_structure:
                    subtitle_tag = sections.find('strong', class_='sub-title')
                    subtitle = subtitle_tag.get_text(strip=True).rstrip(':') if subtitle_tag else "Abstract"
                    content = sections.get_text(strip=True).replace(f"{subtitle}:", "").strip()
                    abstract_content[subtitle] = content


            results[paper_name] = {
            "Authors" : list(set(authors_list)),
            "Abstract" : abstract_content
        }
        except Exception as e:
            pass

    
    return results

def summarize_profile(pubmed: dict, profileName: str) -> dict:
    api_key = os.environ.get('API_KEY')
    client = OpenAI(api_key=api_key)

    # Create a user message with the text
    prompt = {
    "role": "user",
    "content": (
        f"You are a Scientific Profiler tasked with analyzing the work of {profileName} work. "
        "Go through **all available research papers**, abstracts, and other related publications from the researcher. "
        "Provide a detailed summary of the following aspects:\n\n"
        "1. **Background**: Give a brief overview of the researcher's professional background, expertise, and affiliations.\n"
        "2. **Research Interests**: Identify and summarize the primary research areas. "
        "Ensure you consider information from **all available publications** to capture the full scope of their interests.\n"
        "3. **Preferred Methodologies**: Analyze the full body of work to understand common methodologies or techniques frequently used by the researcher.\n"
        "4. **Insights**: Highlight interesting and significant findings across various studies, focusing on impactful results.\n\n"
        "Output your response in the following JSON format:\n"
        "{\n"
        '  "Background": "<insert>",\n'
        '  "Research Interests": "<insert>",\n'
        '  "Preferred Methodologies": "<insert>",\n'
        '  "Insights": "<insert>"\n'
        "}\n"
        "Make sure to write clear, crisp, and comprehensive paragraphs for each section. "
        "**Do not limit your analysis to a subset of articles; include insights from all relevant sources.**"
    )
}

    user_message = {
            "role": "user",
            "content": str(pubmed)
        }

    # Send the request to the OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[prompt, user_message],
        temperature=0.7,
    )

    # Extract and return the response content
    response_content = response.choices[0].message.content

    if "```json" in response_content:
        # Clean the response by removing the code block markers
        response_content_cleaned = response_content.replace("```json", "").replace("```", "").strip()
        response_json = json.loads(response_content_cleaned)
    else:
        # Parse the response content back to a Python dictionary
        response_json = json.loads(response_content)

    return response_json

def setupScrapping(profile_link: str) -> dict:
    # Initialize browser
    browser = initialize_browser()

    # Update the user-input
    user_input = parseUserInput(profile_link, abstract_view=True)

    # Open browser and get results
    browser.open(user_input)
    soup = BeautifulSoup(browser.response().read(), "html.parser")

    # Extract basic details
    dataProfileName = soup.find('meta', {'name' : 'log_query'})['content']
    dataTotalResults = int(soup.find('meta', {'name' : 'log_resultcount'})['content'])
    dataPagesToScrap = math.ceil((dataTotalResults/20))

    # Extract pages to scrap
    dataPageLinks = []
    for k in range(dataPagesToScrap):
        dataPageLinks += [user_input + f"&page={k+1}"]

    return {
        'profileName' : dataProfileName,
        'pageLinks' : dataPageLinks
    }
