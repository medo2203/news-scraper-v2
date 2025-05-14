def save_articles_to_db(self, articles):
        """Save articles to the SQLite database."""
        fetch_date = datetime.datetime.now().isoformat()
        
        for article in articles:
            try:
                # Prepare data for insertion
                countries = json.dumps(article.get('countries', []))
                categories = json.dumps(article.get('categories', []))
                keywords = json.dumps(article.get('keywords', []) if 'keywords' in article else [])
                
                # Check if article already exists (by link)
                self.cursor.execute(
                    "SELECT id FROM articles WHERE link = ?", 
                    (article['link'],)
                )
                existing = self.cursor.fetchone()
                
                if existing:
                    # Update existing article
                    self.cursor.execute('''
                    UPDATE articles SET
                        title = ?,
                        description = ?,
                        source = ?,
                        language = ?,
                        countries = ?,
                        categories = ?,
                        keywords = ?,
                        author = ?,
                        image_url = ?,
                        pub_date = ?,
                        fetch_date = ?
                    WHERE link = ?
                    ''', (
                        article.get('title', ''),
                        article.get('description', ''),
                        article.get('source', ''),
                        article.get('language', ''),
                        countries,
                        categories,
                        keywords,
                        article.get('author', ''),
                        article.get('image', ''),
                        article.get('date', ''),
                        fetch_date,
                        article['link']
                    ))
                else:
                    # Insert new article
                    self.cursor.execute('''
                    INSERT INTO articles (
                        title, link, description, source, language,
                        countries, categories, keywords, author,
                        image_url, pub_date, fetch_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.get('title', ''),
                        article['link'],
                        article.get('description', ''),
                        article.get('source', ''),
                        article.get('language', ''),
                        countries,
                        categories,
                        keywords,
                        article.get('author', ''),
                        article.get('image', ''),
                        article.get('date', ''),
                        fetch_date
                    ))
            except sqlite3.Error as err:
                logger.error(f"SQLite error: {err} for article: {article['link']}")
            except Exception as err:
                logger.error(f"Unexpected error: {err} for article: {article['link']}")
                
        self.conn.commit()
        logger.info(f"Saved {len(articles)} articles to database.")

import json
import os
import sys
import requests
import xml.etree.ElementTree as ET
from io import StringIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import argparse
import datetime

# Import your existing utility modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logging_config import setup_logger
# from redisSaver import save_articles_to_redis  # Commented out Redis saver

logger = setup_logger()

class UnifiedRssScraper:
    def __init__(self, db_path='db/site_configs.db'):
        """Initialize the scraper with a connection to the configuration database."""
        self.db_path = db_path
        
        # Ensure db directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Initialize articles table if it doesn't exist
        self._init_articles_table()
        
    def _init_articles_table(self):
        """Create the articles table if it doesn't exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL UNIQUE,
            description TEXT,
            source TEXT,
            language TEXT,
            countries TEXT,
            categories TEXT,
            keywords TEXT,
            author TEXT,
            image_url TEXT,
            pub_date TEXT,
            fetch_date TEXT,
            content TEXT
        )
        ''')
        self.conn.commit()

    def fetch_rss_feed(self, url):
        """Fetches and parses an RSS feed from a URL using requests."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return ET.parse(StringIO(response.text))
        except requests.RequestException as err:
            logger.error(f"Request error fetching {url}: {err}")
        except ET.ParseError as err:
            logger.error(f"XML parsing error for {url}: {err}")
        return None

    def fetch_article_image(self, url, xpath=None):
        """Fetches the image from an article URL using configurable xpath or default strategy."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        image_url = ""
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Use xpath if provided, otherwise fallback to first image
            if xpath:
                # BeautifulSoup doesn't directly support xpath, this is simplified targeting
                # For complex xpath, consider using lxml directly
                img = soup.select_one(xpath)
            else:
                img = soup.find('img')
                
            if img and img.has_attr('src'):
                image_url = img['src']
                # Handle relative URLs
                if image_url.startswith('/'):
                    image_url = urljoin(url, image_url)
        except Exception as err:
            logger.error(f"Failed to fetch image from {url}: {err}")
            
        return image_url

    def get_site_config(self, site_name):
        """Get the configuration for a specific news site."""
        try:
            self.cursor.execute(
                "SELECT * FROM site_configs WHERE site_name = ?", 
                (site_name,)
            )
            return self.cursor.fetchone()
        except sqlite3.Error as err:
            logger.error(f"Database error: {err}")
            return None

    def get_site_config_by_url(self, url):
        """Find the site configuration that matches a given URL pattern."""
        try:
            self.cursor.execute(
                "SELECT * FROM site_configs WHERE ? LIKE '%' || url_pattern || '%'", 
                (url,)
            )
            return self.cursor.fetchone()
        except sqlite3.Error as err:
            logger.error(f"Database error: {err}")
            return None

    def extract_value_from_item(self, item, config_field):
        """Extract a value from an RSS item using the configuration field."""
        if not config_field:
            return ""
            
        # Parse the config field which may contain namespace information
        parts = config_field.split('|')
        field_path = parts[0]
        attribute = parts[1] if len(parts) > 1 else None
        
        # Handle namespace notation (e.g., {namespace}element)
        if ':' in field_path and '{' not in field_path:
            prefix, tag = field_path.split(':')
            # Try to find namespace from item's nsmap equivalent
            for k, v in item.getroot().nsmap.items() if hasattr(item, 'getroot') else {}:
                if k == prefix:
                    field_path = f"{{{v}}}{tag}"
        
        try:
            element = item.find(field_path)
            
            if element is not None:
                if attribute:
                    # Extract attribute if specified
                    return element.attrib.get(attribute, "")
                elif element.text:
                    # Extract text content
                    text = element.text.strip()
                    # Check if this is HTML that needs to be parsed
                    if '<' in text and '>' in text:
                        soup = BeautifulSoup(text, "html.parser")
                        return soup.get_text().strip()
                    return text
        except Exception as err:
            logger.error(f"Error extracting {config_field}: {err}")
            
        return ""

    def process_feed(self, rss_url, site_name=None, language=None, categories=None, countries=None):
        """Process an RSS feed with database-stored configuration."""
        # Auto-detect site configuration if not specified
        site_config = None
        if site_name:
            site_config = self.get_site_config(site_name)
        else:
            site_config = self.get_site_config_by_url(rss_url)
            
        if not site_config:
            logger.error(f"No configuration found for {site_name or rss_url}")
            return
            
        # Load configuration
        config = dict(site_config)
        
        # Override with command line arguments if provided
        if language:
            config['default_language'] = language
        if categories:
            config['default_categories'] = json.dumps(categories)
        if countries:
            config['default_countries'] = json.dumps(countries)
            
        # Parse default values from config
        try:
            default_categories = json.loads(config.get('default_categories', '[]'))
            default_countries = json.loads(config.get('default_countries', '[]'))
        except json.JSONDecodeError:
            default_categories = []
            default_countries = []
            
        # Fetch feed
        feed = self.fetch_rss_feed(rss_url)
        if not feed:
            logger.error(f"Failed to fetch RSS feed from {rss_url}")
            return

        # Process articles
        articles = []
        for item in feed.findall(".//item"):
            article = {
                "source": config.get('site_name', 'Unknown'),
                "language": config.get('default_language', 'unknown'),
                "categories": default_categories,
                "countries": default_countries,
            }
            
            # Extract basic fields
            article["title"] = self.extract_value_from_item(item, config.get('title_field', 'title'))
            article["link"] = self.extract_value_from_item(item, config.get('link_field', 'link'))
            article["date"] = self.extract_value_from_item(item, config.get('date_field', 'pubDate'))
            article["description"] = self.extract_value_from_item(item, config.get('description_field', 'description'))
            
            # Extract author if configured
            author_field = config.get('author_field')
            if author_field:
                article["author"] = self.extract_value_from_item(item, author_field)
                
            # Extract keywords/categories if configured
            keywords_field = config.get('keywords_field')
            if keywords_field:
                keywords_str = self.extract_value_from_item(item, keywords_field)
                if keywords_str:
                    article["keywords"] = [k.strip() for k in keywords_str.split(",")]
            
            # Extract image URL - try multiple methods
            image_url = ""
            
            # Method 1: Direct from RSS item
            image_field = config.get('image_field')
            if image_field:
                image_url = self.extract_value_from_item(item, image_field)
                
            # Method 2: Media content tag (with namespace)
            if not image_url and config.get('media_namespace') and config.get('media_content_field'):
                media_content = item.find(f"{{{config['media_namespace']}}}{config['media_content_field']}")
                if media_content is not None and "url" in media_content.attrib:
                    image_url = media_content.attrib["url"]
                    
            # Method 3: Fetch from article URL if allowed and needed
            if not image_url and config.get('fetch_article_image', False) and article["link"]:
                image_url = self.fetch_article_image(
                    article["link"], 
                    config.get('article_image_xpath')
                )
                
            article["image"] = image_url
            articles.append(article)

        # Save to SQLite database
        save_articles_to_db(self,articles)
        logger.info(f"Fetched and saved {len(articles)} articles from {rss_url}.")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

def main():
    """Command line entry point for the unified RSS scraper."""
    parser = argparse.ArgumentParser(description="Unified RSS Feed Scraper")
    parser.add_argument("rss_url", help="URL of the RSS feed to scrape")
    parser.add_argument("--site", help="Site name (optional, will autodetect if not provided)")
    parser.add_argument("--language", help="Override the language for articles")
    parser.add_argument("--categories", help="JSON array of categories")
    parser.add_argument("--countries", help="JSON array of countries")
    parser.add_argument("--db", default="db/site_configs.db", help="Path to the config database")
    
    args = parser.parse_args()
    
    categories = None
    countries = None
    
    if args.categories:
        try:
            categories = json.loads(args.categories)
        except json.JSONDecodeError:
            logger.error("Invalid JSON format for categories")
            return
            
    if args.countries:
        try:
            countries = json.loads(args.countries)
        except json.JSONDecodeError:
            logger.error("Invalid JSON format for countries")
            return
    
    scraper = UnifiedRssScraper(db_path=args.db)
    try:
        scraper.process_feed(
            args.rss_url,
            site_name=args.site,
            language=args.language,
            categories=categories,
            countries=countries
        )
    finally:
        scraper.close()

if __name__ == "__main__":
    main()