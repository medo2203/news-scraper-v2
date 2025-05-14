def list_articles(db_path, source=None, limit=10):
    """List recent articles from the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT id, title, source, pub_date FROM articles"
    params = []
    
    if source:
        query += " WHERE source = ?"
        params.append(source)
    
    query += " ORDER BY pub_date DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    articles = cursor.fetchall()
    
    if not articles:
        print("No articles found.")
        return
    
    print(f"Found {len(articles)} recent articles:")
    for article in articles:
        print(f"[{article['id']}] {article['title']} - {article['source']} ({article['pub_date']})")
    
    conn.close()
    
    
import sqlite3
import json
import os
import argparse

def setup_database(db_path):
    """Create and initialize the site configuration database."""
    # Create db directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    # Create database if it doesn't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS site_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_name TEXT NOT NULL UNIQUE,
        url_pattern TEXT NOT NULL,
        default_language TEXT DEFAULT 'fr',
        default_categories TEXT DEFAULT '[]',
        default_countries TEXT DEFAULT '[]',
        title_field TEXT DEFAULT 'title',
        link_field TEXT DEFAULT 'link',
        date_field TEXT DEFAULT 'pubDate',
        description_field TEXT DEFAULT 'description',
        author_field TEXT,
        keywords_field TEXT,
        image_field TEXT,
        media_namespace TEXT,
        media_content_field TEXT,
        fetch_article_image BOOLEAN DEFAULT 0,
        article_image_xpath TEXT
    )
    ''')
    
    # Create articles table
    cursor.execute('''
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
    
    # Sample configurations for French news sites
    sites = [
        {
            "site_name": "Le Monde",
            "url_pattern": "lemonde.fr",
            "default_language": "fr",
            "default_countries": json.dumps(["France"]),
            "description_field": "description",
            "media_namespace": "http://search.yahoo.com/mrss/",
            "media_content_field": "content",
            "fetch_article_image": False
        },
        {
            "site_name": "L'Équipe",
            "url_pattern": "lequipe.fr",
            "default_language": "fr",
            "default_countries": json.dumps(["France"]),
            "description_field": "description",
            "author_field": "{http://purl.org/dc/elements/1.1/}creator",
            "keywords_field": "category",
            "fetch_article_image": True
        },
        {
            "site_name": "Les Echos",
            "url_pattern": "lesechos.fr",
            "default_language": "fr",
            "default_countries": json.dumps(["France"]),
            "description_field": "description",
            "media_namespace": "http://search.yahoo.com/mrss/",
            "media_content_field": "content",
            "fetch_article_image": False
        },
        {
            "site_name": "Le Figaro",
            "url_pattern": "lefigaro.fr",
            "default_language": "fr",
            "default_countries": json.dumps(["France"]),
            "description_field": "description",
            "media_namespace": "http://search.yahoo.com/mrss/",
            "media_content_field": "content",
            "fetch_article_image": False
        }
    ]
    
    # Insert or update configurations
    for site in sites:
        # Check if site already exists
        cursor.execute("SELECT id FROM site_configs WHERE site_name = ?", (site["site_name"],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing site
            placeholders = ", ".join([f"{k} = ?" for k in site.keys() if k != "site_name"])
            values = [site[k] for k in site.keys() if k != "site_name"]
            values.append(site["site_name"])
            
            cursor.execute(
                f"UPDATE site_configs SET {placeholders} WHERE site_name = ?",
                values
            )
        else:
            # Insert new site
            placeholders = ", ".join(["?"] * len(site))
            columns = ", ".join(site.keys())
            
            cursor.execute(
                f"INSERT INTO site_configs ({columns}) VALUES ({placeholders})",
                list(site.values())
            )
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {db_path} with {len(sites)} site configurations")

def add_site(db_path, site_data):
    """Add a new site configuration to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Format any JSON fields
    for key in ['default_categories', 'default_countries']:
        if key in site_data and not isinstance(site_data[key], str):
            site_data[key] = json.dumps(site_data[key])
    
    # Check if site already exists
    cursor.execute("SELECT id FROM site_configs WHERE site_name = ?", (site_data["site_name"],))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing site
        placeholders = ", ".join([f"{k} = ?" for k in site_data.keys() if k != "site_name"])
        values = [site_data[k] for k in site_data.keys() if k != "site_name"]
        values.append(site_data["site_name"])
        
        cursor.execute(
            f"UPDATE site_configs SET {placeholders} WHERE site_name = ?",
            values
        )
        print(f"Updated configuration for {site_data['site_name']}")
    else:
        # Insert new site
        placeholders = ", ".join(["?"] * len(site_data))
        columns = ", ".join(site_data.keys())
        
        cursor.execute(
            f"INSERT INTO site_configs ({columns}) VALUES ({placeholders})",
            list(site_data.values())
        )
        print(f"Added new configuration for {site_data['site_name']}")
    
    conn.commit()
    conn.close()

def list_sites(db_path):
    """List all site configurations in the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT site_name, url_pattern FROM site_configs ORDER BY site_name")
    sites = cursor.fetchall()
    
    print(f"Found {len(sites)} site configurations:")
    for site in sites:
        print(f"- {site['site_name']} ({site['url_pattern']})")
    
    conn.close()

def export_site(db_path, site_name):
    """Export a site configuration to JSON."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM site_configs WHERE site_name = ?", (site_name,))
    site = cursor.fetchone()
    
    if not site:
        print(f"Site '{site_name}' not found")
        return
    
    site_dict = dict(site)
    print(json.dumps(site_dict, indent=2))
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Setup and manage RSS site configurations")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Initialize the database with default configurations')
    setup_parser.add_argument('--db', default='db/site_configs.db', help='Database path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all site configurations')
    list_parser.add_argument('--db', default='db/site_configs.db', help='Database path')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export a site configuration to JSON')
    export_parser.add_argument('site_name', help='Name of the site to export')
    export_parser.add_argument('--db', default='db/site_configs.db', help='Database path')
    
    # Add command (simplified, would need more args for full functionality)
    add_parser = subparsers.add_parser('add', help='Add a new site configuration')
    add_parser.add_argument('--db', default='db/site_configs.db', help='Database path')
    add_parser.add_argument('--name', required=True, help='Site name')
    add_parser.add_argument('--url-pattern', required=True, help='URL pattern for auto-detection')
    add_parser.add_argument('--language', default='fr', help='Default language')
    add_parser.add_argument('--countries', help='JSON array of countries')
    add_parser.add_argument('--media-namespace', help='Media namespace for images')
    add_parser.add_argument('--media-content-field', help='Media content field name')
    add_parser.add_argument('--fetch-article-image', action='store_true', help='Fetch images from article')
    
    # List articles command
    articles_parser = subparsers.add_parser('articles', help='List recent articles in the database')
    articles_parser.add_argument('--db', default='db/site_configs.db', help='Database path')
    articles_parser.add_argument('--source', help='Filter by news source')
    articles_parser.add_argument('--limit', type=int, default=10, help='Number of articles to show')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        setup_database(args.db)
    elif args.command == 'list':
        list_sites(args.db)
    elif args.command == 'export':
        export_site(args.db, args.site_name)
    elif args.command == 'add':
        site_data = {
            "site_name": args.name,
            "url_pattern": args.url_pattern,
            "default_language": args.language
        }
        
        if args.countries:
            site_data["default_countries"] = args.countries
        
        if args.media_namespace:
            site_data["media_namespace"] = args.media_namespace
            
        if args.media_content_field:
            site_data["media_content_field"] = args.media_content_field
            
        if args.fetch_article_image:
            site_data["fetch_article_image"] = True
            
        add_site(args.db, site_data)
    elif args.command == 'articles':
        list_articles(args.db, args.source, args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()