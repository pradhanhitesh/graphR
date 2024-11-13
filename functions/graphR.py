from bs4 import BeautifulSoup
from builtins import str
from bs4 import BeautifulSoup
from mechanize import Browser
from openai import OpenAI
import json
import os
        
def initialize_browser():
    """Initialize the browser with specific headers."""
    b = Browser()
    b.set_handle_robots(False)
    b.addheaders = [
        ('Referer', 'https://pubmed.ncbi.nlm.nih.gov'), 
        ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36')
    ]
    return b

def get_profile(profile_link: str) -> dict:
    """Fetch and return the profile details from the given Google Scholar profile link."""
    browser = initialize_browser()
    profile_data = {"Profile Name": "Not found", "Profile Description": "Not found", "Profile Picture": "Not found"}
    
    try:
        browser.open(profile_link,  timeout=60)
        soup = BeautifulSoup(browser.response().read(), "html.parser")

        # Extract Profile Name
        profile_name_elem = soup.find("div", {"id": "gsc_prf_in"})
        if profile_name_elem:
            profile_data["Profile Name"] = profile_name_elem.text.strip()

        # Extract Profile Description
        profile_desc_elem = soup.find("div", {"class": "gsc_prf_il"})
        if profile_desc_elem:
            profile_data["Profile Description"] = profile_desc_elem.text.strip()

        # Extract Profile Picture URL
        profile_pic_elem = soup.find("img", {"id": "gsc_prf_pup-img"})
        if profile_pic_elem and 'src' in profile_pic_elem.attrs:
            profile_pic_url = profile_pic_elem['src'].replace("view_photo","medium_photo")
            if '/citations/images/avatar_scholar_128.png' not in profile_pic_url:
                profile_data["Profile Picture"] = profile_pic_url

    except Exception as e:
        print(f"Error fetching profile data: {e}")

    finally:
        browser.close()

    return profile_data


def scrap_pubmed(browser: Browser, paper: str) -> dict:
    query = paper.replace(" ", "+")
    url = f"https://pubmed.ncbi.nlm.nih.gov/?term={query}&size=200"
    abstract_content = {}

    try:
        # Open the URL with Mechanize
        response = browser.open(url, timeout=60)
        
        # Check if the response is successful
        if response.code != 200:
            print(f"Failed to fetch PubMed page for: {paper}")
            return abstract_content

        soup = BeautifulSoup(response.read(), "html.parser")

        # Look for abstract sections using more reliable classes or attributes
        abstract_sections = soup.find_all('div', {'class': 'abstract-content'})
        
        if not abstract_sections:
            print(f"No Abstract Found: {paper}")
            return abstract_content

        # Iterate over sections to check structured or unstructured abstract
        for section in abstract_sections:
            paragraphs = section.find_all('p')

            if not paragraphs:
                print(f"No paragraphs found in abstract for {paper}")
                continue

            if len(paragraphs) == 1:
                # Unstructured abstract
                print(f"Single-paragraph Abstract Found: {paper}")
                abstract_content["Abstract"] = paragraphs[0].get_text(strip=True)
            else:
                # Structured abstract
                print(f"Structured Abstract Found: {paper}")
                for p in paragraphs:
                    subtitle_tag = p.find('strong', class_='sub-title')
                    subtitle = subtitle_tag.get_text(strip=True).rstrip(':') if subtitle_tag else "Abstract"
                    content = p.get_text(strip=True).replace(f"{subtitle}:", "").strip()
                    abstract_content[subtitle] = content

        # Author Names
        try:
            authors = sorted(list(set([x.get_text(strip=True) for x in soup.find_all('a', {'class' : 'full-name'})])))
        except Exception as e:
            authors = []
            

    except Exception as e:
        print(f"An error occurred while scraping PubMed for {paper}: {str(e)}")

    return abstract_content, authors

def get_description(browser, link):
    """Retrieve the description text from the given link."""
    try:
        browser.open(link, timeout=60)
        soup = BeautifulSoup(browser.response().read(), "html.parser")
        text_elements = soup.find_all("div", {"class": "gsh_csp"})
        texts = [element.text for element in text_elements]
        return "\n".join(texts) if texts else "No description available"
    except Exception as e:
        print(f"Error fetching description: {e}")
        return "Error fetching description"
    
def scrap_gsc(browser, profile_link: str) -> dict:
    # Ensure the correct sorting of links
    by_cited = profile_link.replace('&sortby=pubdate', '')
    by_year = profile_link if '&sortby=pubdate' in profile_link else f'{profile_link}&sortby=pubdate'

    # Store the links in the list
    links_to_scrap = [by_cited, by_year]
    results = {}

    for link in links_to_scrap:
        browser.open(link, timeout=60)
        soup = BeautifulSoup(browser.response().read(), "html.parser")

        # Find paper entries and citations
        papers = soup.find_all("td", {"class": "gsc_a_t"})
        citations = soup.find_all("td", {"class": "gsc_a_c"})

        # Process papers and citations only if counts match
        if len(papers) == len(citations):
            for paper, cite in zip(papers, citations):
                try:
                    # Extract paper name
                    paper_name = paper.find('a', class_='gsc_a_at')
                    if not paper_name:
                        print("Paper name not found, skipping entry.")
                        continue
                    
                    paper_name_text = paper_name.text.strip()
                    href = "https://scholar.google.co.in" + paper_name['href']

                    # Extract journal info safely
                    journal_info_elements = paper.find_all('div', class_='gs_gray')
                    if len(journal_info_elements) < 2:
                        print(f"Journal info not found for {paper_name_text}. Using default 'N/A'.")
                        journal_info = "N/A"
                    else:
                        journal_info = journal_info_elements[1].text.strip()

                    # Extract year safely
                    year_span = paper.find('span', class_='gs_oph')
                    year = year_span.text.strip(',').replace(" ", "") if year_span else "N/A"

                    # Extract citation number safely
                    citation_link = cite.find('a', class_='gsc_a_ac')
                    citation_number = citation_link.text.strip() if citation_link and citation_link.text else "0"

                    # Get description using the helper function
                    descp = get_description(browser, href)

                    # Search on PubMed
                    pubmed_abstract, pubmed_authors  = scrap_pubmed(browser, paper_name_text)

                    # Add entry if it doesn't already exist
                    if paper_name_text not in results:
                        results[paper_name_text] = {
                            'Journal Name': journal_info,
                            'Year': year,
                            'Link': href,
                            'Citation': citation_number,
                            'Description': descp,
                            'PubMed Abstract' : pubmed_abstract,
                            'PubMed Authors' : pubmed_authors

                        }

                except Exception as e:
                    print(f"Error processing entry for {paper_name.text if paper_name else 'unknown'}: {e}")
                    continue

    browser.close()  # Close the browser once all links are scraped
    return results


def summarize_profile(pubmed: dict) -> dict:
    api_key = os.environ.get('API_KEY')
    client = OpenAI(api_key=api_key)

    # Create a user message with the text
    prompt = {
    "role": "user",
    "content": (
        "You are a Scientific Profiler tasked with analyzing a researcher's work. "
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

    response_json["success"] = True

    return response_json


def pubmed_crawl(browser, profile_link: str) -> dict:
    browser.open(profile_link + "&format=abstract", timeout=60)
    soup = BeautifulSoup(browser.response().read(), "html.parser")

    papers = soup.find_all('article', {"class" : "article-overview"})
    results = {}
    for paper in papers:
        # Get paper name
        paper_name = paper.find('h1',{'class':'heading-title'}).find('a').get_text(strip=True)
        print(paper_name)

        # Get authors name
        authors_list = []
        for authors in paper.find_all('span', {'class' : 'authors-list-item'}):
            try:
                author_name = authors.find('a', {'class' : 'full-name'}).get_text(strip=True)
                # author_afl = authors.find('a', {'class': 'affiliation-link'})['title']
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
            "Authors" : authors_list,
            "Abstract" : abstract_content
        }
        except Exception as e:
            results[paper_name] = {
                "Authors" : "NA",
                "Abstract" : "NA"
            }

    
    return results