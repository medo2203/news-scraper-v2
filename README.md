# News Scraper v2

A unified RSS feed scraper that intelligently processes news articles from various sources using configurable site-specific settings stored in an SQLite database.

## Features

- **Unified RSS Processing**: Single scraper that adapts to different news sites using database-stored configurations
- **Intelligent Site Detection**: Automatically detects site configurations based on URL patterns
- **Flexible Field Mapping**: Configurable field extraction for titles, links, descriptions, authors, images, and more
- **Image Extraction**: Multiple methods for extracting article images (RSS tags, media content, or from article pages)
- **Database Storage**: SQLite database for both configurations and scraped articles
- **Comprehensive Logging**: Daily rotating logs with both file and console output
- **Command Line Interface**: Easy-to-use CLI for managing configurations and scraping feeds

## Project Structure

```
.
├── .gitignore
├── requirements.txt
├── README.md
├── db/
│   └── site_configs.db          # SQLite database for configurations and articles
├── log/         # Daily rotating log files
└── src/
    ├── logging_config.py        # Centralized logging configuration
    ├── setup_site_configs.py    # Database setup and site management
    ├── unified_rss_scraper.py   # Main RSS scraper
    └── __pycache__/
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/medo2203/news-scraper-v2.git
   cd news-scraper-v2
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python src/setup_site_configs.py setup
   ```

## Usage

### Setting Up Site Configurations

Before scraping, you need to configure news sites in the database:

#### Initialize Database
```bash
python src/setup_site_configs.py setup
```

#### Add a New Site Configuration
```bash
python src/setup_site_configs.py add \
  --name "Example News" \
  --url-pattern "example.com" \
  --language "en" \
  --countries '["US", "UK"]' \
  --media-namespace "http://search.yahoo.com/mrss/" \
  --media-content-field "content" \
  --fetch-article-image
```

#### List All Configured Sites
```bash
python src/setup_site_configs.py list
```

#### Export Site Configuration
```bash
python src/setup_site_configs.py export "Example News"
```

### Scraping RSS Feeds

#### Basic Scraping (Auto-detect site configuration)
```bash
python src/unified_rss_scraper.py "https://example.com/rss"
```

#### Scraping with Specific Site Configuration
```bash
python src/unified_rss_scraper.py "https://example.com/rss" --site "Example News"
```

#### Override Default Settings
```bash
python src/unified_rss_scraper.py "https://example.com/rss" \
  --language "fr" \
  --categories '["politics", "technology"]' \
  --countries '["FR", "BE"]'
```

### Managing Articles

#### View Recent Articles
```bash
python src/setup_site_configs.py articles
```

#### Filter by Source
```bash
python src/setup_site_configs.py articles --source "Example News" --limit 20
```

## Configuration

### Site Configuration Fields

The database stores the following configuration for each news site:

| Field | Description | Default |
|-------|-------------|---------|
| `site_name` | Unique identifier for the site | Required |
| `url_pattern` | URL pattern for auto-detection | Required |
| `default_language` | Default language code | 'fr' |
| `default_categories` | JSON array of default categories | '[]' |
| `default_countries` | JSON array of default countries | '[]' |
| `title_field` | RSS field for article title | 'title' |
| `link_field` | RSS field for article link | 'link' |
| `date_field` | RSS field for publication date | 'pubDate' |
| `description_field` | RSS field for description | 'description' |
| `author_field` | RSS field for author | null |
| `keywords_field` | RSS field for keywords/tags | null |
| `image_field` | RSS field for image URL | null |
| `media_namespace` | Namespace for media content | null |
| `media_content_field` | Field name for media content | null |
| `fetch_article_image` | Whether to fetch images from article pages | false |
| `article_image_xpath` | XPath/CSS selector for article images | null |

### Database Schema

#### Site Configurations Table
```sql
CREATE TABLE site_configs (
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
);
```

#### Articles Table
```sql
CREATE TABLE articles (
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
);
```

## Logging

The application uses a centralized logging system ([`src/logging_config.py`](src/logging_config.py)) that:

- Creates daily rotating log files in the `log/` directory
- Outputs logs to both file and console
- Uses the format: `timestamp - script_name - level - message`
- Automatically manages log rotation and cleanup (keeps 7 days of logs)

## Error Handling

The scraper includes comprehensive error handling for:

- Network timeouts and connection errors
- XML parsing errors
- Database connection issues
- Missing or malformed RSS fields
- Image fetching failures

## Dependencies

- **requests**: HTTP requests for fetching RSS feeds and web pages
- **beautifulsoup4**: HTML/XML parsing for content extraction
- **sqlite3**: Database operations (built-in Python module)
- **xml.etree.ElementTree**: RSS/XML parsing (built-in Python module)

See [`requirements.txt`](requirements.txt) for complete dependency list.

## Development

### Adding New Features

1. **Site Configuration Fields**: Add new columns to the `site_configs` table in [`setup_site_configs.py`](src/setup_site_configs.py)
2. **Article Processing**: Extend the `process_feed` method in [`UnifiedRssScraper`](src/unified_rss_scraper.py)
3. **Field Extraction**: Enhance the `extract_value_from_item` method for complex field parsing

### Testing

Test the scraper with different RSS feeds:

```bash
# Test with a simple RSS feed
python src/unified_rss_scraper.py "https://feeds.feedburner.com/example"

# Test with custom configuration
python src/setup_site_configs.py add --name "Test Site" --url-pattern "test.com"
python src/unified_rss_scraper.py "https://test.com/rss" --site "Test Site"
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]