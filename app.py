import requests
import json
import networkx as nx
from urllib.parse import urlparse, urljoin
import time
from datetime import datetime
import anthropic
from typing import List, Dict, Set, Tuple
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WordPressQueryFanOutAnalyzer:
    """Analyze WordPress sites for Google AI Mode query fan-out optimization"""
    
    def __init__(self, site_url: str, claude_api_key: str):
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.claude = anthropic.Anthropic(api_key=claude_api_key)
        self.content_graph = nx.DiGraph()
        self.query_patterns = defaultdict(list)
        self.content_cache = {}
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def fetch_all_content(self) -> Dict:
        """Fetch all content from WordPress site"""
        logger.info(f"Fetching content from {self.site_url}")
        
        content = {
            'posts': self.fetch_posts(),
            'pages': self.fetch_pages(),
            'categories': self.fetch_categories(),
            'tags': self.fetch_tags(),
            'media': self.fetch_media_info()
        }
        
        logger.info(f"Fetched {len(content['posts'])} posts and {len(content['pages'])} pages")
        return content
    
    def fetch_posts(self, per_page=100) -> List[Dict]:
        """Fetch all posts from WordPress"""
        posts = []
        page = 1
        
        while True:
            try:
                response = requests.get(
                    f"{self.api_base}/posts",
                    params={'per_page': per_page, 'page': page, '_embed': True}
                )
                
                if response.status_code == 200:
                    batch = response.json()
                    if not batch:
                        break
                    posts.extend(batch)
                    page += 1
                    time.sleep(0.5)  # Rate limiting
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching posts: {e}")
                break
                
        return posts
    
    def fetch_pages(self, per_page=100) -> List[Dict]:
        """Fetch all pages from WordPress"""
        pages = []
        page = 1
        
        while True:
            try:
                response = requests.get(
                    f"{self.api_base}/pages",
                    params={'per_page': per_page, 'page': page, '_embed': True}
                )
                
                if response.status_code == 200:
                    batch = response.json()
                    if not batch:
                        break
                    pages.extend(batch)
                    page += 1
                    time.sleep(0.5)
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching pages: {e}")
                break
                
        return pages
    
    def fetch_categories(self) -> List[Dict]:
        """Fetch all categories"""
        try:
            response = requests.get(f"{self.api_base}/categories", params={'per_page': 100})
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def fetch_tags(self) -> List[Dict]:
        """Fetch all tags"""
        try:
            response = requests.get(f"{self.api_base}/tags", params={'per_page': 100})
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def fetch_media_info(self) -> List[Dict]:
        """Fetch media information"""
        try:
            response = requests.get(f"{self.api_base}/media", params={'per_page': 50})
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def build_content_graph(self, content: Dict) -> nx.DiGraph:
        """Build a graph representation of the site's content"""
        logger.info("Building content graph...")
        
        # Add posts as nodes
        for post in content['posts']:
            self.content_graph.add_node(
                post['id'],
                type='post',
                title=post['title']['rendered'],
                url=post['link'],
                content=self.clean_html(post['content']['rendered']),
                excerpt=self.clean_html(post['excerpt']['rendered']),
                categories=post.get('categories', []),
                tags=post.get('tags', []),
                date=post['date']
            )
            
        # Add pages as nodes
        for page in content['pages']:
            self.content_graph.add_node(
                f"page_{page['id']}",
                type='page',
                title=page['title']['rendered'],
                url=page['link'],
                content=self.clean_html(page['content']['rendered']),
                parent=page.get('parent', 0),
                date=page['date']
            )
        
        # Build edges based on internal links
        self.build_internal_link_edges()
        
        # Build edges based on category/tag relationships
        self.build_taxonomy_edges(content)
        
        logger.info(f"Content graph built with {self.content_graph.number_of_nodes()} nodes and {self.content_graph.number_of_edges()} edges")
        return self.content_graph
    
    def clean_html(self, html: str) -> str:
        """Remove HTML tags and clean text"""
        text = re.sub('<.*?>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def build_internal_link_edges(self):
        """Extract and build edges from internal links"""
        for node_id, data in self.content_graph.nodes(data=True):
            if 'content' in data:
                # Extract internal links
                links = re.findall(rf'{self.site_url}/[^"\'>\s]+', data['content'])
                
                for link in links:
                    # Find the target node
                    for target_id, target_data in self.content_graph.nodes(data=True):
                        if target_data.get('url') == link:
                            self.content_graph.add_edge(node_id, target_id, type='internal_link')
                            break
    
    def build_taxonomy_edges(self, content: Dict):
        """Build edges based on categories and tags"""
        # Create category nodes
        for cat in content['categories']:
            self.content_graph.add_node(
                f"cat_{cat['id']}",
                type='category',
                name=cat['name'],
                slug=cat['slug']
            )
        
        # Create tag nodes
        for tag in content['tags']:
            self.content_graph.add_node(
                f"tag_{tag['id']}",
                type='tag',
                name=tag['name'],
                slug=tag['slug']
            )
        
        # Connect posts to categories and tags
        for node_id, data in self.content_graph.nodes(data=True):
            if data['type'] == 'post':
                for cat_id in data.get('categories', []):
                    self.content_graph.add_edge(node_id, f"cat_{cat_id}", type='categorized_as')
                
                for tag_id in data.get('tags', []):
                    self.content_graph.add_edge(node_id, f"tag_{tag_id}", type='tagged_as')
    
    def analyze_query_patterns(self) -> Dict:
        """Analyze content for complex query patterns using Claude"""
        logger.info("Analyzing query patterns with Claude API...")
        
        patterns = {
            'complex_queries': [],
            'decompositions': {},
            'coverage_analysis': {},
            'opportunities': []
        }
        
        # Sample content for analysis
        sample_content = self.get_content_sample()
        
        # Analyze with Claude
        prompt = f"""Analyze this WordPress site content for Google AI Mode query optimization opportunities.

Site URL: {self.site_url}

Content Sample:
{json.dumps(sample_content, indent=2)[:3000]}

Identify:
1. Complex queries users might ask that would trigger Google's query fan-out
2. How Google would decompose these queries into sub-queries
3. Which content currently answers which sub-queries
4. Gaps where sub-queries aren't answered
5. Multi-source optimization opportunities

Focus on queries that would require multiple hops of reasoning to answer fully.

Provide analysis in JSON format with:
- complex_queries: List of potential complex user queries
- decompositions: How each query would be broken down
- current_coverage: Which content addresses which sub-queries
- gaps: Missing sub-query content
- recommendations: Specific content to create"""

        try:
            response = self.claude.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            analysis = self.parse_claude_response(response.content[0].text)
            patterns.update(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing with Claude: {e}")
        
        return patterns
    
    def get_content_sample(self) -> List[Dict]:
        """Get a representative sample of content"""
        sample = []
        
        for node_id, data in list(self.content_graph.nodes(data=True))[:20]:
            if data['type'] in ['post', 'page']:
                sample.append({
                    'title': data['title'],
                    'type': data['type'],
                    'excerpt': data.get('excerpt', '')[:200],
                    'url': data['url']
                })
        
        return sample
    
    def parse_claude_response(self, response_text: str) -> Dict:
        """Parse Claude's response into structured data"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self.fallback_parse(response_text)
        except:
            return self.fallback_parse(response_text)
    
    def fallback_parse(self, text: str) -> Dict:
        """Fallback parsing if JSON extraction fails"""
        return {
            'complex_queries': re.findall(r'"([^"]+\?)"', text),
            'recommendations': [text],
            'gaps': []
        }
    
    def analyze_content_depth(self) -> Dict:
        """Analyze content depth and multi-hop potential"""
        logger.info("Analyzing content depth and multi-hop potential...")
        
        depth_analysis = {
            'content_scores': {},
            'hub_potential': [],
            'orphan_content': [],
            'semantic_clusters': []
        }
        
        # Calculate content depth scores
        for node_id, data in self.content_graph.nodes(data=True):
            if data['type'] in ['post', 'page']:
                score = self.calculate_content_depth(data)
                depth_analysis['content_scores'][node_id] = {
                    'title': data['title'],
                    'url': data['url'],
                    'depth_score': score,
                    'word_count': len(data.get('content', '').split()),
                    'internal_links': self.content_graph.out_degree(node_id),
                    'backlinks': self.content_graph.in_degree(node_id)
                }
        
        # Identify hub potential
        for node_id, score_data in depth_analysis['content_scores'].items():
            if score_data['internal_links'] > 5 and score_data['depth_score'] > 0.7:
                depth_analysis['hub_potential'].append(score_data)
        
        # Find orphan content
        for node_id, score_data in depth_analysis['content_scores'].items():
            if score_data['backlinks'] == 0 and score_data['internal_links'] < 2:
                depth_analysis['orphan_content'].append(score_data)
        
        # Identify semantic clusters
        depth_analysis['semantic_clusters'] = self.identify_semantic_clusters()
        
        return depth_analysis
    
    def calculate_content_depth(self, node_data: Dict) -> float:
        """Calculate a depth score for content"""
        score = 0.0
        
        # Word count factor
        word_count = len(node_data.get('content', '').split())
        if word_count > 2000:
            score += 0.3
        elif word_count > 1000:
            score += 0.2
        elif word_count > 500:
            score += 0.1
        
        # Heading structure (simplified)
        content = node_data.get('content', '')
        h2_count = content.count('<h2') + content.count('## ')
        h3_count = content.count('<h3') + content.count('### ')
        
        if h2_count > 3:
            score += 0.2
        if h3_count > 5:
            score += 0.1
        
        # Media presence
        if '<img' in content or '[gallery' in content:
            score += 0.1
        
        # Lists and structured data
        if '<ul' in content or '<ol' in content or '- ' in content:
            score += 0.1
        
        # Schema markup indicators
        if 'itemtype' in content or '@type' in content:
            score += 0.2
        
        return min(score, 1.0)
    
    def identify_semantic_clusters(self) -> List[Dict]:
        """Identify semantic content clusters using TF-IDF"""
        logger.info("Identifying semantic clusters...")
        
        # Prepare content for vectorization
        content_texts = []
        node_ids = []
        
        for node_id, data in self.content_graph.nodes(data=True):
            if data['type'] in ['post', 'page'] and data.get('content'):
                content_texts.append(data['content'])
                node_ids.append(node_id)
        
        if not content_texts:
            return []
        
        # Vectorize content
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(content_texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Identify clusters (simplified clustering)
            clusters = []
            visited = set()
            
            for i in range(len(node_ids)):
                if node_ids[i] in visited:
                    continue
                    
                cluster = {
                    'center': node_ids[i],
                    'members': [],
                    'theme': self.extract_cluster_theme(i, tfidf_matrix)
                }
                
                for j in range(len(node_ids)):
                    if similarity_matrix[i][j] > 0.3:  # Similarity threshold
                        cluster['members'].append({
                            'id': node_ids[j],
                            'similarity': float(similarity_matrix[i][j])
                        })
                        visited.add(node_ids[j])
                
                if len(cluster['members']) > 1:
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error in semantic clustering: {e}")
            return []
    
    def extract_cluster_theme(self, doc_index: int, tfidf_matrix) -> List[str]:
        """Extract theme keywords for a cluster"""
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        doc_tfidf = tfidf_matrix[doc_index].toarray()[0]
        
        # Get top 5 terms
        top_indices = doc_tfidf.argsort()[-5:][::-1]
        return [feature_names[i] for i in top_indices if doc_tfidf[i] > 0]
    
    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        logger.info("Generating optimization report...")
        
        # Fetch and analyze content
        content = self.fetch_all_content()
        self.build_content_graph(content)
        
        # Run analyses
        query_patterns = self.analyze_query_patterns()
        depth_analysis = self.analyze_content_depth()
        
        # Generate recommendations
        recommendations = self.generate_recommendations(query_patterns, depth_analysis)
        
        # Compile report
        report = {
            'site_url': self.site_url,
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_posts': len(content['posts']),
                'total_pages': len(content['pages']),
                'content_nodes': self.content_graph.number_of_nodes(),
                'internal_links': self.content_graph.number_of_edges(),
                'orphan_content': len(depth_analysis['orphan_content']),
                'hub_pages': len(depth_analysis['hub_potential']),
                'semantic_clusters': len(depth_analysis['semantic_clusters'])
            },
            'query_optimization': query_patterns,
            'content_depth': depth_analysis,
            'recommendations': recommendations,
            'action_plan': self.create_action_plan(recommendations)
        }
        
        return report
    
    def generate_recommendations(self, query_patterns: Dict, depth_analysis: Dict) -> List[Dict]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Query coverage recommendations
        if 'gaps' in query_patterns:
            for gap in query_patterns.get('gaps', []):
                recommendations.append({
                    'type': 'content_gap',
                    'priority': 'high',
                    'action': 'Create new content',
                    'details': f"Create content to answer sub-query: {gap}",
                    'impact': 'Enables multi-hop reasoning path'
                })
        
        # Orphan content recommendations
        for orphan in depth_analysis['orphan_content'][:5]:  # Top 5
            recommendations.append({
                'type': 'orphan_content',
                'priority': 'medium',
                'action': 'Add internal links',
                'details': f"Connect orphan content: {orphan['title']}",
                'url': orphan['url'],
                'impact': 'Improves content graph connectivity'
            })
        
        # Hub optimization
        for hub in depth_analysis['hub_potential'][:3]:  # Top 3
            recommendations.append({
                'type': 'hub_optimization',
                'priority': 'high',
                'action': 'Enhance hub page',
                'details': f"Optimize hub potential: {hub['title']}",
                'url': hub['url'],
                'impact': 'Strengthens multi-source selection'
            })
        
        # Semantic cluster recommendations
        for cluster in depth_analysis['semantic_clusters'][:3]:  # Top 3
            recommendations.append({
                'type': 'semantic_bridge',
                'priority': 'medium',
                'action': 'Create semantic bridges',
                'details': f"Link related content in cluster: {', '.join(cluster['theme'])}",
                'impact': 'Enables query fan-out paths'
            })
        
        return recommendations
    
    def create_action_plan(self, recommendations: List[Dict]) -> Dict:
        """Create prioritized action plan"""
        action_plan = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        for rec in recommendations:
            if rec['priority'] == 'high':
                action_plan['immediate'].append({
                    'action': rec['action'],
                    'details': rec['details'],
                    'expected_impact': rec['impact']
                })
            elif rec['priority'] == 'medium':
                action_plan['short_term'].append({
                    'action': rec['action'],
                    'details': rec['details'],
                    'expected_impact': rec['impact']
                })
            else:
                action_plan['long_term'].append({
                    'action': rec['action'],
                    'details': rec['details'],
                    'expected_impact': rec['impact']
                })
        
        return action_plan
    
    def export_report(self, report: Dict, filename: str = 'seo_analysis_report.json'):
        """Export report to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report exported to {filename}")
    
    def visualize_content_graph(self, output_file: str = 'content_graph.html'):
        """Create an interactive visualization of the content graph"""
        import pyvis.network as net
        
        # Create pyvis network
        nt = net.Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
        
        # Add nodes with different colors by type
        color_map = {
            'post': '#1f77b4',
            'page': '#ff7f0e',
            'category': '#2ca02c',
            'tag': '#d62728'
        }
        
        for node_id, data in self.content_graph.nodes(data=True):
            nt.add_node(
                node_id,
                label=data.get('title', data.get('name', str(node_id)))[:30],
                color=color_map.get(data['type'], '#gray'),
                title=data.get('url', ''),
                size=20 + self.content_graph.degree(node_id) * 2
            )
        
        # Add edges
        for source, target in self.content_graph.edges():
            nt.add_edge(source, target)
        
        # Generate HTML
        nt.save_graph(output_file)
        logger.info(f"Content graph visualization saved to {output_file}")

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WordPress Query Fan-Out SEO Analyzer')
    parser.add_argument('site_url', help='WordPress site URL')
    parser.add_argument('claude_api_key', help='Claude API key')
    parser.add_argument('--output', default='seo_report.json', help='Output file name')
    parser.add_argument('--visualize', action='store_true', help='Generate graph visualization')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = WordPressQueryFanOutAnalyzer(args.site_url, args.claude_api_key)
    
    # Generate report
    report = analyzer.generate_optimization_report()
    
    # Export report
    analyzer.export_report(report, args.output)
    
    # Generate visualization if requested
    if args.visualize:
        analyzer.visualize_content_graph()
    
    # Print summary
    print("\n" + "="*50)
    print("SEO ANALYSIS COMPLETE")
    print("="*50)
    print(f"Site: {report['site_url']}")
    print(f"Total Content Nodes: {report['summary']['content_nodes']}")
    print(f"Orphan Content: {report['summary']['orphan_content']}")
    print(f"Potential Hub Pages: {report['summary']['hub_pages']}")
    print(f"Semantic Clusters: {report['summary']['semantic_clusters']}")
    print(f"\nTop Recommendations: {len(report['recommendations'])}")
    print(f"Report saved to: {args.output}")
    
    if report['recommendations']:
        print("\nTop 3 Immediate Actions:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"{i}. {rec['action']}: {rec['details']}")

if __name__ == "__main__":
    main()
