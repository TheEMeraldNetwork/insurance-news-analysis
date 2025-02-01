import requests
from bs4 import BeautifulSoup
import webbrowser
import os
from datetime import datetime, timedelta
import urllib.parse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib_venn
from matplotlib_venn import venn3
import io
import base64
from GoogleNews import GoogleNews
from textblob import TextBlob
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import json
from dotenv import load_dotenv
import aiohttp
import asyncio

# Load environment variables
load_dotenv()

class NewsScanner:
    def __init__(self):
        self.gnews = GoogleNews(lang='it', period='12m')  # Extended to 12 months
        self.companies = [
            "VitaNuova Assicurazioni",  # Fixed company name
            "Unidea Assicurazioni",
            "Alleanza Assicurazioni"
        ]
        self.article_counts = {}
        self.word_clouds = {}
        self.top_topics = {}
        self.articles = {}  # Store articles for search functionality
        self.heygen_api_key = os.getenv('HEYGEN_API_KEY')
        self.heygen_avatar_id = os.getenv('HEYGEN_AVATAR_ID')
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Combine Italian and English stopwords
        self.stop_words = set(stopwords.words('italian') + stopwords.words('english'))
        # Add custom stopwords
        self.stop_words.update([
            'della', 'delle', 'degli', 'dell', 'dal', 'dalla', 'dai', 'dagli', 
            'del', 'alla', 'alle', 'agli', 'allo', 'nell', 'nella', 'nelle', 
            'negli', 'sul', 'sulla', 'sulle', 'sugli', 'con', 'per', 'tra',
            'fra', 'presso', 'dopo', 'prima', 'durante', 'oltre', 'attraverso',
            'mediante', 'tramite', 'verso', 'fino', 'assicurazioni', 'assicurazione',
            'company', 'companies', 'group', 'gruppo', 'società'
        ])

    def clean_text_for_wordcloud(self, text, company):
        # Simple tokenization using split
        words = text.lower().split()
        # Remove company name words, stop words, and short words
        company_words = set(company.lower().split())
        # For VitaNuova, also add individual parts
        if "vitanuova" in company.lower():
            company_words.update(["vita", "nuova"])
        
        filtered_words = [
            word.strip('.,!?()[]{}":;') for word in words 
            if len(word) >= 4 and  # Only words with 4+ letters
            word.strip('.,!?()[]{}":;').isalpha() and  # Only alphabetic words
            word not in company_words and  # Remove company name words
            word not in self.stop_words  # Remove stop words
        ]
        
        # Count word frequencies and get top 20
        word_freq = Counter(filtered_words)
        top_words = [word for word, _ in word_freq.most_common(20)]
        return " ".join(top_words)

    def extract_topics(self, texts):
        """Extract main topics from a list of texts using semantic analysis"""
        # Combine all texts
        combined_text = " ".join(texts)
        
        # Define detailed topic categories with related terms
        topic_categories = {
            'Environmental': ['sostenibilità', 'ambiente', 'green', 'climate', 'energia', 'rinnovabile', 'emissioni', 'riciclo'],
            'Digital Innovation': ['innovazione', 'digitale', 'tecnologia', 'digital', 'startup', 'intelligenza', 'app', 'online'],
            'Investment': ['finanza', 'investimenti', 'risparmio', 'mercato', 'economia', 'finanziario', 'borsa', 'trading'],
            'Health Services': ['salute', 'sanitario', 'benessere', 'prevenzione', 'medico', 'assistenza', 'clinica', 'terapia'],
            'Community Support': ['sociale', 'comunità', 'welfare', 'solidarietà', 'inclusione', 'diversity', 'volontariato', 'donazioni'],
            'Business Growth': ['business', 'strategia', 'partnership', 'crescita', 'sviluppo', 'mercato', 'espansione', 'acquisizione'],
            'Customer Service': ['clienti', 'servizio', 'assistenza', 'supporto', 'soddisfazione', 'qualità', 'esperienza', 'consulenza'],
            'Product Innovation': ['prodotti', 'soluzioni', 'novità', 'lancio', 'offerta', 'polizza', 'copertura', 'protezione'],
            'Market Position': ['leadership', 'competitività', 'posizione', 'quota', 'presenza', 'network', 'distribuzione', 'canali'],
            'Risk Management': ['rischio', 'sicurezza', 'protezione', 'gestione', 'controllo', 'compliance', 'normativa', 'regolamento']
        }
        
        # Count occurrences of topic-related terms
        topic_scores = Counter()
        words = combined_text.lower().split()
        
        for word in words:
            for topic, terms in topic_categories.items():
                if any(term in word for term in terms):
                    topic_scores[topic] += 1
        
        # Get top 3 topics with their scores
        top_topics = topic_scores.most_common(3)
        return [(topic, score) for topic, score in top_topics if score > 0]

    def search_company_news(self, company):
        print(f"\nSearching news for {company}...")
        try:
            self.gnews.clear()
            print("  Making request to Google News...")
            self.gnews.search(company)
            print("  Fetching results...")
            results = self.gnews.results()
            
            # Verify results and filter out duplicates
            verified_results = []
            seen_titles = set()
            for result in results:
                if result.get('title') and result['title'] not in seen_titles:
                    verified_results.append(result)
                    seen_titles.add(result['title'])
            
            actual_count = len(verified_results)
            print(f"  Found {actual_count} unique articles")
            
            # Store article count and results
            self.article_counts[company] = actual_count
            self.articles[company] = verified_results
            
            # Extract texts for topic analysis
            texts = [f"{r['title']} {r.get('desc', '')}" for r in verified_results]
            
            print("  Analyzing topics...")
            # Get top topics
            self.top_topics[company] = self.extract_topics(texts)
            
            # Generate word cloud from titles and descriptions
            text = " ".join(texts)
            if text.strip():
                print("  Generating word cloud...")
                # Clean and filter text
                cleaned_text = self.clean_text_for_wordcloud(text, company)
                if cleaned_text.strip():
                    wordcloud = WordCloud(width=400, height=200, 
                                       background_color='white',
                                       min_word_length=4,  # Additional filter for word length
                                       collocations=False  # Avoid repeated word pairs
                                       ).generate(cleaned_text)
                    
                    # Convert word cloud to base64 image
                    img_buffer = io.BytesIO()
                    plt.figure(figsize=(4, 2))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.tight_layout(pad=0)
                    plt.savefig(img_buffer, format='png', bbox_inches='tight')
                    plt.close()
                    img_buffer.seek(0)
                    self.word_clouds[company] = base64.b64encode(img_buffer.getvalue()).decode()
                else:
                    print("  No words remained after filtering for word cloud")
                    self.word_clouds[company] = None
            else:
                print("  No text available for word cloud")
                self.word_clouds[company] = None
        except Exception as e:
            print(f"  Error processing {company}: {str(e)}")
            self.article_counts[company] = 0
            self.articles[company] = []
            self.top_topics[company] = []
            self.word_clouds[company] = None

    def search_combined_news(self, company1, company2):
        """Search for news mentioning both companies"""
        try:
            query = f'"{company1}" AND "{company2}"'
            print(f"\nSearching for articles mentioning both {company1} and {company2}...")
            self.gnews.clear()
            self.gnews.search(query)
            results = self.gnews.results()
            
            # Verify results and filter out duplicates
            verified_results = []
            seen_titles = set()
            for result in results:
                if result.get('title') and result['title'] not in seen_titles:
                    verified_results.append(result)
                    seen_titles.add(result['title'])
            
            count = len(verified_results)
            print(f"  Found {count} unique articles")
            return count
        except Exception as e:
            print(f"  Error searching combined news: {str(e)}")
            return 0

    def generate_venn_diagram(self):
        """Generate a Venn diagram showing topic overlaps between companies"""
        # Get topics for each company
        topics_by_company = {
            company: set(topic for topic, _ in self.top_topics.get(company, []))
            for company in self.companies
        }
        
        # Calculate overlaps
        company_names = [c.replace(' Assicurazioni', '') for c in self.companies]
        vita_topics = topics_by_company[self.companies[0]]
        unidea_topics = topics_by_company[self.companies[1]]
        alleanza_topics = topics_by_company[self.companies[2]]
        
        # Calculate all possible overlaps
        overlaps = {
            'vita_only': vita_topics - (unidea_topics | alleanza_topics),
            'unidea_only': unidea_topics - (vita_topics | alleanza_topics),
            'alleanza_only': alleanza_topics - (vita_topics | unidea_topics),
            'vita_unidea': vita_topics & unidea_topics - alleanza_topics,
            'vita_alleanza': vita_topics & alleanza_topics - unidea_topics,
            'unidea_alleanza': unidea_topics & alleanza_topics - vita_topics,
            'all': vita_topics & unidea_topics & alleanza_topics
        }
        
        # Create Venn diagram
        plt.figure(figsize=(6, 4))
        venn3([topics_by_company[company] for company in self.companies],
              set_labels=company_names,
              set_colors=('#8BA89B', '#9BB0A5', '#AEBFB4'))
        plt.title('Topic Overlaps Between Companies', pad=20, color='white')
        
        # Style the diagram
        plt.gca().set_facecolor('#1C2B2B')
        plt.gcf().set_facecolor('#1C2B2B')
        for text in plt.gca().texts:
            text.set_color('white')
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', 
                   facecolor='#1C2B2B', 
                   bbox_inches='tight',
                   dpi=300)
        plt.close()
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode(), overlaps

    async def generate_avatar_response(self, question, context):
        """Generate a response using Heygen API"""
        if not self.heygen_api_key or not self.heygen_avatar_id:
            return "Avatar configuration is missing. Please set HEYGEN_API_KEY and HEYGEN_AVATAR_ID environment variables."
        
        try:
            async with aiohttp.ClientSession() as session:
                # First, create a video generation task
                create_url = "https://api.heygen.com/v1/video.generate"
                headers = {
                    "X-Api-Key": self.heygen_api_key,
                    "Content-Type": "application/json"
                }
                
                # Prepare the response based on the context and question
                system_prompt = f"You are an AI assistant analyzing insurance news. Context: {context}"
                
                payload = {
                    "avatar": {
                        "avatar_id": self.heygen_avatar_id
                    },
                    "input": {
                        "text": question,
                        "system_prompt": system_prompt,
                        "voice": {
                            "type": "natural"
                        }
                    }
                }
                
                async with session.post(create_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("video_url", "Sorry, I couldn't generate a response.")
                    else:
                        return f"Error generating response: {await response.text()}"
                        
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_html(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        venn_diagram, overlaps = self.generate_venn_diagram()
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Insurance News Analysis</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #1C2B2B;
                    color: #E0E0E0;
                }}
                .container {{
                    display: flex;
                    gap: 20px;
                    height: calc(100vh - 40px);
                }}
                .news-container {{
                    flex: 2;
                    background: #2A3B3B;
                    border-radius: 8px;
                    overflow-y: auto;
                    padding: 20px;
                }}
                .analysis-container {{
                    flex: 1;
                    background: #2A3B3B;
                    border-radius: 8px;
                    overflow-y: auto;
                    padding: 20px;
                }}
                .company-section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    background: #3A4B4B;
                    border-radius: 8px;
                }}
                .article {{
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #4A5B5B;
                    border-radius: 4px;
                }}
                .article h3 {{
                    margin: 0 0 10px 0;
                    color: #8BA89B;
                }}
                .article p {{
                    margin: 5px 0;
                }}
                .article a {{
                    color: #9BB0A5;
                    text-decoration: none;
                }}
                .article a:hover {{
                    text-decoration: underline;
                }}
                .word-cloud {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .word-cloud img {{
                    max-width: 100%;
                    border-radius: 4px;
                }}
                .topics {{
                    margin: 10px 0;
                }}
                .topic {{
                    display: inline-block;
                    margin: 5px;
                    padding: 5px 10px;
                    background: #4A5B5B;
                    border-radius: 15px;
                    font-size: 0.9em;
                }}
                .venn-diagram {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .venn-diagram img {{
                    max-width: 100%;
                    border-radius: 8px;
                }}
                .overlap-section {{
                    margin-bottom: 20px;
                    padding: 15px;
                    background: #3A4B4B;
                    border-radius: 4px;
                }}
                h1, h2, h3 {{
                    color: #8BA89B;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- News Content -->
                <div class="news-container">
                    <h1>News Coverage</h1>
                    {self._generate_news_content()}
                </div>

                <!-- Topics Analysis and Venn Diagram -->
                <div class="analysis-container">
                    <h1>Topic Analysis</h1>
                    {self._generate_topics_content()}
                    
                    <div class="venn-diagram">
                        <h2>Topic Overlaps</h2>
                        <img src="data:image/png;base64,{venn_diagram}" alt="Topic Overlaps">
                    </div>
                    
                    <!-- Overlap Details -->
                    {self._generate_overlap_content(overlaps)}
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Write HTML to file and open in browser
        with open('news_analysis.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("Done! Opening report in your browser.")
        webbrowser.open('file://' + os.path.realpath('news_analysis.html'))

    def _generate_news_content(self):
        """Generate HTML content for news tab"""
        content = []
        for company in self.companies:
            section = f'''
            <div class="company-section">
                <h2>{company}</h2>
                <p>Found {self.article_counts[company]} articles</p>
                '''
            
            # Add word cloud if available
            if self.word_clouds[company]:
                section += f'''
                <div class="word-cloud">
                    <h3>Word Cloud</h3>
                    <img src="data:image/png;base64,{self.word_clouds[company]}" alt="Word cloud">
                </div>
                '''
            
            # Add articles
            for article in self.articles[company]:
                section += f'''
                <div class="article">
                    <h3><a href="{article['link']}" target="_blank">{article['title']}</a></h3>
                    <p>{article.get('desc', 'No description available')}</p>
                    <p><small>{article.get('date', 'Date not available')}</small></p>
                </div>
                '''
            
            section += '</div>'
            content.append(section)
        
        return '\n'.join(content)

    def _generate_topics_content(self):
        """Generate HTML content for topics tab"""
        content = []
        for company in self.companies:
            section = f'''
            <div class="company-section">
                <h2>{company}</h2>
                <div class="topics">
                    <h3>Top Topics:</h3>
                    '''
            
            # Add topics
            for topic, score in self.top_topics[company]:
                section += f'<span class="topic">{topic} ({score})</span>'
            
            section += '</div></div>'
            content.append(section)
        
        return '\n'.join(content)

    def _generate_overlap_content(self, overlaps):
        """Generate HTML content for overlaps section"""
        content = ['<div class="overlap-details">']
        
        # Add overlap sections
        if overlaps['all']:
            content.append(f'''
            <div class="overlap-section">
                <h3>Common Topics Across All Companies:</h3>
                <div class="topics">
                    {' '.join(f'<span class="topic">{topic}</span>' for topic in overlaps['all'])}
                </div>
            </div>
            ''')
        
        # Add pairwise overlaps
        pairs = [
            ('vita_unidea', 'VitaNuova & Unidea'),
            ('vita_alleanza', 'VitaNuova & Alleanza'),
            ('unidea_alleanza', 'Unidea & Alleanza')
        ]
        
        for key, title in pairs:
            if overlaps[key]:
                content.append(f'''
                <div class="overlap-section">
                    <h3>Topics Shared by {title}:</h3>
                    <div class="topics">
                        {' '.join(f'<span class="topic">{topic}</span>' for topic in overlaps[key])}
                    </div>
                </div>
                ''')
        
        # Add unique topics
        companies = [
            ('vita_only', 'VitaNuova'),
            ('unidea_only', 'Unidea'),
            ('alleanza_only', 'Alleanza')
        ]
        
        for key, company in companies:
            if overlaps[key]:
                content.append(f'''
                <div class="overlap-section">
                    <h3>Topics Unique to {company}:</h3>
                    <div class="topics">
                        {' '.join(f'<span class="topic">{topic}</span>' for topic in overlaps[key])}
                    </div>
                </div>
                ''')
        
        content.append('</div>')
        return '\n'.join(content)

    def run(self):
        print("\nStarting news analysis...")
        print("Period: Last 12 months")
        print("Companies:", ", ".join(self.companies))
        
        for company in self.companies:
            self.search_company_news(company)
        
        print("\nGenerating HTML report...")
        self.generate_html()
        print("Done! Opening report in your browser.")
        return self  # Return self for chaining

if __name__ == "__main__":
    scanner = NewsScanner()
    scanner.run() 