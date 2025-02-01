from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from simple_search import NewsScanner
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Initialize the scanner and run it once
scanner = NewsScanner()
scanner.run()

@app.route('/')
def home():
    return send_file('news_analysis.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Get relevant context from articles
        context = ""
        for company, articles in scanner.articles.items():
            for article in articles:
                context += f"{article.get('title', '')} {article.get('desc', '')} "
        
        # Call Heygen API
        response = "Your avatar will respond here with a video about: " + question
        return jsonify({'video_url': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    load_dotenv()
    print("Server starting at http://localhost:5000")
    app.run(debug=True, port=5000) 