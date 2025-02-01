import streamlit as st
from simple_search import NewsScanner
import base64
from io import BytesIO

st.set_page_config(
    page_title="Insurance News Analysis",
    page_icon="📰",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
        .stApp {
            background-color: #1C2B2B;
            color: #E0E0E0;
        }
        h1, h2, h3 {
            color: #8BA89B !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #2A3B3B;
            padding: 10px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #E0E0E0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #8BA89B !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            background-color: #2A3B3B;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        a {
            color: #9BB0A5 !important;
        }
        .topic-tag {
            background-color: #4A5B5B;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 5px;
            display: inline-block;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("Insurance News Analysis")
    
    # Initialize scanner
    with st.spinner("Fetching news..."):
        scanner = NewsScanner()
        scanner.run()
    
    # Create two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("News Coverage")
        
        # Display news for each company
        for company in scanner.companies:
            with st.expander(f"{company} ({scanner.article_counts[company]} articles)", expanded=True):
                # Display word cloud if available
                if scanner.word_clouds[company]:
                    st.image(
                        f"data:image/png;base64,{scanner.word_clouds[company]}", 
                        caption="Word Cloud",
                        use_column_width=True
                    )
                
                # Display articles
                for article in scanner.articles[company]:
                    st.markdown(f"""
                        <div style='background-color: #3A4B4B; padding: 15px; border-radius: 4px; margin-bottom: 10px;'>
                            <h3><a href="{article['link']}" target="_blank">{article['title']}</a></h3>
                            <p>{article.get('desc', 'No description available')}</p>
                            <p><small>{article.get('date', 'Date not available')}</small></p>
                        </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.header("Topic Analysis")
        
        # Display topics for each company
        for company in scanner.companies:
            with st.expander(company, expanded=True):
                st.subheader("Top Topics")
                for topic, score in scanner.top_topics[company]:
                    st.markdown(f"""
                        <span class="topic-tag">{topic} ({score})</span>
                    """, unsafe_allow_html=True)
        
        # Display Venn diagram
        st.subheader("Topic Overlaps")
        venn_diagram, overlaps = scanner.generate_venn_diagram()
        st.image(
            f"data:image/png;base64,{venn_diagram}", 
            caption="Topic Overlaps Between Companies",
            use_column_width=True
        )
        
        # Display overlap details
        st.subheader("Common Topics")
        if overlaps['all']:
            st.markdown("**Shared by all companies:**")
            for topic in overlaps['all']:
                st.markdown(f"<span class='topic-tag'>{topic}</span>", unsafe_allow_html=True)

if __name__ == "__main__":
    main() 