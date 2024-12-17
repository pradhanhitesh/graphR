
---

# 🧠 GraphR - Get comprehensive profile of researchers

Welcome to **GraphR**! This tool scrapes and summarizes academic profiles from **PubMed** using automated browser interaction. It's designed to quickly extract key information, saving you time from manual searches.

## 🚀 Features

- 🔍 **Profile Scraping**: Extracts profile details including name, bio, and profile picture.

- 📚 **Publication Summary**: Gathers and summarizes recent publications.

- 📝 **Smart Summarization**: Uses OpenAI API to generate a concise overview of the profile.

- 🖥️ **Interactive UI**: Simple and responsive frontend for inputting and viewing profiles.

## 🎥 How to find PubMed profile link of any researcher?

Please watch the YouTube video <a href="https://www.youtube.com/watch?v=waPMcZsQJBs">here</a>.

## 📦 Installation

Get started by cloning the repository and setting up the environment:

1. Ensure you have **Python 3.10** installed.
   - You can check your Python version with: `python3 --version`

2. Then do this:
```bash
git clone https://github.com/pradhanhitesh/graphR.git
cd graphR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 🔑 API Key Setup

This project uses OpenAI's API for text summarization. Add your API key to your environment:

```bash
export API_KEY='your-api-key-here'
```

Alternatively, you can set it in a `.env` file:

```
API_KEY=your-openai-api-key-here
```

## 🚀 Running the App

Start the Flask server with the following command:

```bash
python app.py
```

Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser to access the application.

## 🛠️ Project Structure

```
📁 scholar-profile-scraper/
├── 📂 static/
│   └── images/
|   └── css/
|   └── js/
├── 📂 templates/
│   └── home.html
│   └── profile.html
├── 📂 functions/
│   └── graphR.py
|   └── __init__.py
├── app.py
├── requirements.txt
└── README.md
```

- **`app.py`**: Main Flask application server.
- **`functions/graphR.py`**: Contains scraping and summarization functions.
- **`templates/`**: HTML templates for rendering the frontend.
- **`static/`**: Contains static files like CSS, JS and images.

## ⚙️ How It Works

1. **User Input**: Enter the PubMed profile link in the input box.

2. **Scraping**: The backend uses Selenium to navigate the profile page and extract key details.

3. **Summarization**: The extracted data is passed to OpenAI's 4o-mini for a summarized response.

4. **Display**: The results are rendered on a dynamic profile page.

## 🐛 Known Issues
 
- **Limited PubMed Support**: Current implementation only supports basic scraping of PubMed profiles

- **Error generating Profile Image**: PubMed do not stores user profile image, therefore, trying altenative ways.

- **Large scope of search**: PubMed do not necessarily differeniates researchers, therefore, the search name is indexed across all articles in PubMed.

- **Large Serveless Function**: Vecel/AWS do not allow bundles larger than 250MB to run. Adding the "graph" functionality has added to the size and therefore not allowing the project to be deployed.

## 🔨 Fixed Issues
 
- **[FIXED] Error generating Profile Name**: Used meta-content tag to find the profile name

- **[FIXED] Longer Profile Generation Time**: Used concurency module to simultaneously scrap multiple pages

## 📣 Feedback

Have suggestions or issues? Feel free to [open an issue](https://github.com/pradhanhitesh/graphR/issues).


## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🌟 Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [OpenAI API](https://openai.com/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [Mechanize](https://mechanize.readthedocs.io/en/latest/)

<p align="center">
  Made with ❤️ by [Hitesh] (https://github.com/pradhanhitesh)
</p>
# graphR
