from flask import Flask, request, jsonify, render_template
from builtins import str 
from functions import graphR
import uuid

app = Flask(__name__)

# In-memory storage for results
results_cache = {}

# Render home.html
@app.route('/')
def home():
    return render_template('home.html')

# Process the profile link
@app.route('/process', methods=['POST'])
def process_link():
    # Get data
    data = request.get_json()
    user_link = data.get('profile_link')

    # Generate a unique ID for this request
    result_id = str(uuid.uuid4())
    # profile_data = graphR.get_profile(user_link)
    # results_cache[result_id] = profile_data
    profile_data = {
        "Profile Name" : "Not found",
        "Profile Description" : "Not found",
        "Profile Picture" : "Not found"
    }

    results_cache[result_id] = profile_data

    return jsonify(
        {
            'result_id' : result_id,
            'success' : True
        }
    )


@app.route('/process_1', methods=['POST'])
def process_1():
    # Intialize browser
    browser = graphR.initialize_browser()

    # Get user input
    data = request.get_json()
    user_link = data.get('profile_link')

    # Scrap Google Scholar
    results = graphR.pubmed_crawl(browser, user_link)

    # Summarize profile
    response_json = graphR.summarize_profile(results)

    return jsonify(response_json)

# Result page route
@app.route('/profile/<result_id>')
def show_result(result_id):
    results = results_cache.get(result_id)

    # Retrieve the result from cache
    name = results.get('Profile Name')
    desc = results.get('Profile Description')
    pic = results.get('Profile Picture')
    if not pic or pic == 'Not found':
        pic = "../static/images/profile.png"


    # Render the result page with the processed data
    return render_template('profile.html', profile_name=name, profile_desc = desc, profile_pict = pic)

if __name__ == '__main__':
    app.run()
