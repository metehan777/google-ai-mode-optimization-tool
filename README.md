# WordPress Query Fan-Out SEO Analyzer

A comprehensive tool that analyzes WordPress sites for Google AI Mode optimization using query decomposition and multi-hop reasoning strategies.

## Features

- **WordPress Content Crawling**: Fetches all posts, pages, categories, and tags via wp-json API
- **Content Graph Construction**: Builds a knowledge graph of your site's content and internal links
- **Query Pattern Analysis**: Uses Claude AI to identify complex queries and decomposition opportunities
- **Semantic Clustering**: Groups related content using TF-IDF vectorization
- **Multi-Source Optimization**: Identifies content that can serve multiple Google source types
- **Actionable Recommendations**: Provides specific steps to optimize for query fan-out
- **Visual Graph Export**: Creates interactive visualization of your content network

## Installation

```bash
# Clone or download app.py
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python app.py https://yourwordpresssite.com YOUR_CLAUDE_API_KEY
```

### With Options

```bash
# Custom output file
python app.py https://yourwordpresssite.com YOUR_CLAUDE_API_KEY --output my_report.json

# With visualization
python app.py https://yourwordpresssite.com YOUR_CLAUDE_API_KEY --visualize
```

## Getting Your Claude API Key

1. Sign up at https://console.anthropic.com
2. Go to API Keys section
3. Create a new API key
4. Copy and use in the command

## What the Analyzer Does

### 1. Content Fetching
- Retrieves all published posts and pages
- Fetches categories, tags, and media information
- Respects rate limits to avoid overloading your server

### 2. Graph Construction
- Creates nodes for each piece of content
- Maps internal links as edges
- Identifies content relationships through categories/tags

### 3. Query Analysis with Claude
- Sends content samples to Claude API
- Identifies potential complex user queries
- Predicts how Google would decompose these queries
- Finds gaps in sub-query coverage

### 4. Content Depth Analysis
- Scores each piece of content for depth and comprehensiveness
- Identifies potential hub pages
- Finds orphaned content with no internal links
- Discovers semantic content clusters

### 5. Recommendation Generation
- Content gaps for unanswered sub-queries
- Internal linking opportunities
- Hub page optimization suggestions
- Semantic bridge creation recommendations

## Output Report Structure

```json
{
  "site_url": "https://example.com",
  "analysis_date": "2024-01-15T10:30:00",
  "summary": {
    "total_posts": 156,
    "total_pages": 23,
    "content_nodes": 205,
    "internal_links": 432,
    "orphan_content": 12,
    "hub_pages": 5,
    "semantic_clusters": 8
  },
  "query_optimization": {
    "complex_queries": [
      "How do I set up WooCommerce with custom shipping zones for international orders?"
    ],
    "decompositions": {
      "query_1": [
        "What is WooCommerce?",
        "How to install WooCommerce?",
        "What are shipping zones?",
        "How to set up international shipping?"
      ]
    },
    "gaps": [
      "No content about shipping zones",
      "Missing international shipping guide"
    ]
  },
  "recommendations": [
    {
      "type": "content_gap",
      "priority": "high",
      "action": "Create new content",
      "details": "Create content to answer sub-query: What are shipping zones?",
      "impact": "Enables multi-hop reasoning path"
    }
  ],
  "action_plan": {
    "immediate": [...],
    "short_term": [...],
    "long_term": [...]
  }
}
```

## Interpreting Results

### Content Gaps
These are sub-queries that Google might generate but your site doesn't answer. Creating this content enables Google to use your site in multi-hop reasoning.

### Orphan Content
Valuable content that isn't well-connected to your site's graph. Adding internal links helps Google traverse your content.

### Hub Pages
Pages with high potential to serve as central nodes in query paths. Optimizing these strengthens your site's authority.

### Semantic Clusters
Groups of related content that should be better interconnected to support query fan-out.

## Visualization

If you use the `--visualize` flag, the tool generates an interactive HTML graph showing:
- Blue nodes: Posts
- Orange nodes: Pages  
- Green nodes: Categories
- Red nodes: Tags
- Node size: Based on number of connections
- Edges: Internal links and relationships

## Best Practices

1. **Run Regularly**: Monthly analysis helps track improvements
2. **Focus on High-Priority**: Address "immediate" recommendations first
3. **Create Sub-Query Content**: Each piece should comprehensively answer one specific question
4. **Build Semantic Bridges**: Connect related content with contextual internal links
5. **Monitor Results**: Track performance in Google Search Console

## Troubleshooting

### API Rate Limits
If you hit rate limits, the tool automatically slows down. For large sites, the analysis may take 10-20 minutes.

### Memory Issues
For very large sites (1000+ posts), you may need to modify the code to process in batches.

### Claude API Errors
Ensure your API key is valid and you have sufficient credits.

## Example Use Cases

### E-commerce Site
Identifies complex product queries and ensures all comparison factors are covered.

### Tech Blog
Finds tutorial series that need better interconnection for step-by-step learning paths.

### Service Business
Discovers service-related questions that require multiple pages to answer fully.

## Advanced Usage

### Custom Analysis
Modify the `analyze_query_patterns()` method to focus on specific query types relevant to your niche.

### Export Formats
Extend the `export_report()` method to output in different formats (CSV, HTML, etc.).

### Integration
Use the report data to automatically create content briefs or update your content calendar.

## Support

For issues or questions:
1. Check WordPress REST API is enabled: `https://yoursite.com/wp-json/`
2. Verify Claude API key is active
3. Ensure Python dependencies are installed correctly

## License

MIT License - Feel free to modify and use for your SEO optimization needs.
