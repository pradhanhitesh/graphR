from flask import Flask, request, jsonify, render_template
import concurrent.futures
from builtins import str 
import uuid
from functions import graphR

app = Flask(__name__)

# In-memory storage for results
results_cache = {}
result_id = str()
results_storage = {}

# Render home.html
@app.route('/')
def home():
    return render_template('home.html')

# Process the profile link
@app.route('/process', methods=['POST'])
def process_link():
    # Get data
    data = request.get_json()
    user_input = data.get('profile_link')
    
    if graphR.validateLink(profile_link=user_input)['status']:
        user_input = graphR.parseUserInput(profile_link=data.get('profile_link'), abstract_view=False)
        data = graphR.setupScrapping(profile_link=user_input)
        profileName = data['profileName']

        # Generate a unique ID for this request
        global result_id
        result_id = str(uuid.uuid4())
        results_cache[result_id] = {"profileName" : profileName}
        
        return jsonify(
            {
            'success' : True,
            'result_id': result_id,
            'message': graphR.validateLink(profile_link=user_input)['message']
        }
        )
    else:
        return jsonify(
            {
            'success' : False,
            'message': graphR.validateLink(profile_link=user_input)['message']
        }
        )

@app.route('/scrap', methods=['POST'])
def scrap():
    # Get user input
    data = request.get_json()
    user_input = data.get('profile_link')

    # Setup scrapping
    data = graphR.setupScrapping(profile_link=user_input)
    dataPageLinks = data['pageLinks']
    dataProfileName = data['profileName']
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map each URL to the fetch_and_parse function
        results = list(executor.map(graphR.FetchAndParse, dataPageLinks))

    results_dict = {}
    for soups in results:  # Loop through each BeautifulSoup object (each page result)
        output = graphR.pubmed_crawl(soups)  # Call the pubmed_crawl function
        for title, value in output.items():  # Loop through each paper's title and its value pair
            if title not in results_dict:  # If the paper title isn't already in the results dictionary
                results_dict[title] = value  # Add it to the dictionary
            else:
                results_dict[title].update(value)  # Assuming value is also a dictionary to updat
    
    global result_id
    results_cache[result_id] = {'profileName' : dataProfileName,
                                'profileData' : results_dict}
    try:
        response_json = graphR.summarize_profile(results_dict, profileName=dataProfileName)
        response_json["success"] = True
        return jsonify(response_json)
    
    except Exception as e:
        print(f"Error: {e}")

        return jsonify(
            {
                'success' : False,
                'message' : f'Open-AI FAILURE: {e}'
            }
        )

# Result page route
@app.route('/profile/<result_id>')
def show_result(result_id):
    results = results_cache.get(result_id)

    # Render the result page with the processed data
    return render_template('profile.html', profile_name=results['profileName'])

@app.route('/graph', methods=['POST'])
def graph():
    # Get the JSON data from the request body
    request_data = request.get_json()
    result_id = request_data.get('result_id')
    
    # Perform the necessary processing, e.g., create the graph
    results_dict = results_cache.get(result_id)['profileData']
    paper_names = list(results_dict.keys())
    
    communities, data, community_paper = graphR.create_graph(results_dict, paper_names)
    response = graphR.summarize_graph(communities)

    # Return the response as JSON
    return jsonify(
        {
        "response": response,
        "rawData": data,
        "communityData": community_paper
        }
    )


# Result page route with Graph Network
@app.route('/graph/<result_id>')
def something(result_id):
    return render_template('graph.html')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
