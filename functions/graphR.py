from bs4 import BeautifulSoup
from builtins import str
import json
import os
import math
from urllib.parse import urlparse, parse_qs
import requests
from itertools import combinations
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def parseUserInput(profile_link: str, abstract_view=True) -> str:
    targetPageSize = 20 # DO NOT EDIT
    parsed_url = urlparse(profile_link)
    query_params = parse_qs(parsed_url.query)
    targetProfileName = query_params.get("term", [None])[0].replace(" ","+")
    targetAuthorID = query_params.get("cauthor_id", [None])[0]
    if abstract_view:
        return f"https://pubmed.ncbi.nlm.nih.gov/?size={targetPageSize}" + f"&term={targetProfileName}&" + f"cauthor_id={targetAuthorID}" + "&format=abstract"
    else:
        return f"https://pubmed.ncbi.nlm.nih.gov/?size={targetPageSize}" + f"&term={targetProfileName}&" + f"cauthor_id={targetAuthorID}"

def FetchAndParse(url):
    headers ={
        "User-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup

def validateLink(profile_link: str) -> dict:
    if all(substring in profile_link for substring in ["cauthor_id=", "term=", "https://pubmed.ncbi.nlm.nih.gov"]):
        profile_link = parseUserInput(profile_link, abstract_view=False)
        try:
            # Send a GET request to the URL
            headers ={
                "User-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            }
            response = requests.get(profile_link, headers=headers)

            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                return {
                    "status" : True,
                    "message" : f"VALID URL. STATUS CODE [{response.status_code}]"
                }
            else:
                return {
                    "status" : False,
                    "message" : f"INVALID URL. STATUS CODE [{response.status_code}]"
                }
            
        except requests.exceptions.RequestException as e:
            return {
                "status" : False,
                "message" : f"UKNOWN ERROR OCCURED {e}"
            }
        
    else:
        return {
            "status" : False,
            "message" : f"INVALID URL ENTERED"
        }

def pubmed_crawl(page_soup):
    papers = page_soup.find_all("article", {"class" : "article-overview"})
    results = {}
    for paper in papers:
        # Get paper name
        paper_name = paper.find("h1",{"class":"heading-title"}).find("a").get_text(strip=True)

        # Get PubMed ID
        pubmed_id = paper.find("strong", {"class": "current-id"}).get_text(strip=True)

        # Get authors name
        authors_list = []
        for authors in paper.find_all("span", {"class" : "authors-list-item"}):
            try:
                author_name = authors.find("a", {"class" : "full-name"}).get_text(strip=True)
                authors_list += [author_name]
            except Exception as e:
                continue

        abstract_content = {}
        try:        
            abstract_area = paper.find_all("div",{"class":"abstract"})[0].find("div",{"class":"abstract-content selected"})
            abstract_structure = abstract_area.find_all("p")

            if len(abstract_structure) == 0: # Abstract not found
                pass
            elif len(abstract_structure) == 1: # Unstructured Abstract
                abstract_content["Abstract"] = abstract_area.get_text(strip=True)
            else:
                for sections in abstract_structure:
                    subtitle_tag = sections.find("strong", class_="sub-title")
                    subtitle = subtitle_tag.get_text(strip=True).rstrip(":") if subtitle_tag else "Abstract"
                    content = sections.get_text(strip=True).replace(f"{subtitle}:", "").strip()
                    abstract_content[subtitle] = content


            results[paper_name] = {
            "PubMed ID" : int(pubmed_id),
            "Authors" : list(set(authors_list)),
            "Abstract" : abstract_content
        }
        except Exception as e:
            pass

    return results

def summarize_profile(pubmed: dict, profileName: str):
    api_key = os.environ.get('API_KEY')

   # Create a user message with the text
    prompt = {
        "role": "system",
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
            "  \"Background\": \"<insert>\",\n"
            "  \"Research Interests\": \"<insert>\",\n"
            "  \"Preferred Methodologies\": \"<insert>\",\n"
            "  \"Insights\": \"<insert>\"\n"
            "}\n"
            "Make sure to write clear, crisp, and comprehensive paragraphs for each section. "
            "**Do not limit your analysis to a subset of articles; include insights from all relevant sources.**"
        )
    }

    user_message = {
            "role": "user",
            "content": str(pubmed)
        }

    response = requests.post("https://api.openai.com/v1/chat/completions", 
                            headers={"Authorization": f"Bearer {api_key}"}, 
                            json={
                                "model": "gpt-4o-mini",
                                "messages": [prompt, user_message],
                                "temperature": 0.7
                                })

    # Extract and return the response content
    response_content = response.json()["choices"][0]["message"]["content"]

    if "```json" in response_content:
        # Clean the response by removing the code block markers
        response_content_cleaned = response_content.replace("```json", "").replace("```", "").strip()
        response_json = json.loads(response_content_cleaned)
    else:
        # Parse the response content back to a Python dictionary
        response_json = json.loads(response_content)

    return response_json

def setupScrapping(profile_link: str) -> dict:
    # Update the user-input
    user_input = parseUserInput(profile_link, abstract_view=True)

    # Open browser and get results
    headers ={
        "User-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }
    response = requests.get(user_input, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract basic details
    dataProfileName = soup.find("meta", {"name" : "log_query"})["content"]
    dataTotalResults = int(soup.find("meta", {"name" : "log_resultcount"})["content"])
    dataPagesToScrap = math.ceil((dataTotalResults/20))

    if dataPagesToScrap > 6:
        # Extract pages to scrap
        dataPageLinks = []
        for k in range(5):
            dataPageLinks += [user_input + f"&page={k+1}"]

        return {
            "profileName" : dataProfileName,
            "pageLinks" : dataPageLinks
        }
    else:
        # Extract pages to scrap
        dataPageLinks = []
        for k in range(dataPagesToScrap):
            dataPageLinks += [user_input + f"&page={k+1}"]
        return {
            "profileName" : dataProfileName,
            "pageLinks" : dataPageLinks
        }
    
def cosine_match(paper1: dict, paper2: dict):
    # Define the abstracts
    paragraph1_abstract = json.dumps(paper1)
    paragraph2_abstract = json.dumps(paper2)

    # Create a TF-IDF vectorizer and compute the similarity
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([paragraph1_abstract, paragraph2_abstract])

    # Compute cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])

    return similarity[0][0]

def summarize_graph(graph: dict) -> dict:
    api_key = os.environ.get('API_KEY')

    # Create a user message with the text
    prompt = {
        "role": "system",
        "content": (
            f"You are a Scientific Profiler tasked with analyzing the research papers from three distinct communities detected through the Louvain community detection algorithm. "
            "These communities consist of papers related to Alzheimer's disease. "
            "For each community, please analyze and summarize the following aspects:\n\n"
            "1. **Summary**: Provide a brief overview of the community's overall theme based on the research papers. "
            "What is the primary focus or common thread that links the papers together?\n"
            "2. **Short Name**: Generate a concise and relevant short name for the community that reflects its core theme.\n"
            "3. **Key Points**: Identify and summarize the top three key insights or themes emerging from the papers in each community.\n"
            "4. **Key Papers**: List all the key papers that were analyzed for this community, including their titles and authors.\n\n"
            "Output your response in the following JSON format:\n"
            "{\n"
            "  \"community_1\": {\n"
            "    \"summary\": \"<insert summary for community 1>\",\n"
            "    \"short_name\": \"<insert short name for community 1>\",\n"
            "  },\n"
            "  \"community_2\": {\n"
            "    \"summary\": \"<insert summary for community 2>\",\n"
            "    \"short_name\": \"<insert short name for community 2>\",\n"
            "  },\n"
            "  \"community_3\": {\n"
            "    \"summary\": \"<insert summary for community 3>\",\n"
            "    \"short_name\": \"<insert short name for community 3>\",\n"
            "}\n"
            "Make sure to provide clear, crisp, and comprehensive paragraphs for each section. "
            "Each description of the community should be limited to 100 words only."
            "Do not limit your analysis to a subset of the papers; ensure you capture the full essence of each community."
        )
    }


    user_message = {
            "role": "user",
            "content": str(graph)
        }

    response = requests.post("https://api.openai.com/v1/chat/completions", 
                            headers={"Authorization": f"Bearer {api_key}"}, 
                            json={
                                "model": "gpt-4o-mini",
                                "messages": [prompt, user_message],
                                "temperature": 0.7
                                })

    # Extract and return the response content
    response_content = response.json()['choices'][0]['message']['content']

    if "```json" in response_content:
        # Clean the response by removing the code block markers
        response_content_cleaned = response_content.replace("```json", "").replace("```", "").strip()
        response_json = json.loads(response_content_cleaned)
    else:
        # Parse the response content back to a Python dictionary
        response_json = json.loads(response_content)

    return response_json

def jaccard_match(author1: list, author2: list):
    set1, set2 = set(author1), set(author2)
    jaccard_index = len(set1 & set2) / len(set1 | set2)

    return jaccard_index

def compute_similarity(results_dict: dict, pair):
    A = results_dict[pair[0]]['Abstract']
    B = results_dict[pair[1]]['Abstract']
    C = results_dict[pair[0]]['Authors']
    D = results_dict[pair[1]]['Authors']
    abstract_similarity = cosine_match(A, B)
    author_similarity = jaccard_match(C, D)
    total_similarity = abstract_similarity + author_similarity
    
    return [pair[0], pair[1], total_similarity]


def create_graph(results_dict: dict, paper_names: list):
    unique_pairs = list(combinations(paper_names, 2))
    similarity_df = []

    for k in range(len(unique_pairs)):
        similarity_df += [compute_similarity(results_dict, unique_pairs[k])]

    data = []
    for k in range(len(similarity_df)):
        data += [
            {"Paper 1" : similarity_df[k][0],
            "Paper 2" : similarity_df[k][1],
            "Composite" : similarity_df[k][2]
            }
        ]

    # Create a graph
    G = nx.Graph()

    # Add edges from your data
    for d in data:
        paper1 = d["Paper 1"]
        paper2 = d["Paper 2"]
        overlap = d["Composite"]
        G.add_edge(paper1, paper2, weight=overlap)

    from networkx.algorithms.community import louvain_communities

    # Apply Louvain community detection
    communities = louvain_communities(G, weight='weight')

    # Sort communities by size (largest to smallest)
    sorted_communities = sorted(communities, key=len, reverse=True)

    # Get the top three communities
    top_three_communities = sorted_communities[:3]
    final_communities = {}

    # Iterate through each community
    for k, communities in enumerate(top_three_communities):
        # Create a list to hold the papers for each community
        papers = []
        for article in communities:
            papers.append({
                "Paper Name": article,
                "Paper Description": results_dict[article]['Abstract']
            })
        
        # Assign the list of papers to the corresponding community
        final_communities[f"{k+1}"] = papers

    community_paper = []
    for key in list(final_communities.keys()):
        for k in range(len(final_communities[key])):
            community_paper += [{"Community" : key, 
                                "Paper Name" : final_communities[key][k]['Paper Name'],
                                "Paper Authors" : results_dict[final_communities[key][k]['Paper Name']]['Authors'],
                                "Paper Description": results_dict[final_communities[key][k]['Paper Name']]['Abstract']}]

    return final_communities, data, community_paper