from collections import defaultdict

from flask import Flask, render_template, request, flash, redirect
from neo4j import GraphDatabase, basic_auth

app = Flask(__name__)

# Establish connection to Neo4j database
driver = GraphDatabase.driver(uri='neo4j+s://8cf36790.databases.neo4j.io', auth=basic_auth("neo4j", "F5r1MYLjlnJJu0Jcthk9FO9PE4agbEMjMDhbDxQ7DBY"))
session = driver.session()

@app.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', default=1, type=int)
    page_size = 8
    if request.method == 'POST':
        search_term = request.form.get('search_term')

        # Constructing dynamic Cypher query based on user input
        query = """
        MATCH (b:Blog)-[:BELONGS_TO]->(category:Category)
        MATCH (b)-[:BELONGS_TO_REGION]->(region:Region)
        MATCH (b)-[:HAS_RELEVANCE]->(relevance:Relevance)
        MATCH (b)-[:TARGETS]->(target:TargetAudience)
        WHERE b.name = $search_term OR category.name = $search_term OR region.name = $search_term OR relevance.name = $search_term OR target.name = $search_term
        RETURN b.name AS name, b.url AS url, category.name AS category, 
               b.publish_date AS publish_date, b.expire_date AS expire_date, 
               region.name AS region, relevance.name AS relevance, 
               collect(target.name) AS target_audience
        ORDER BY b.name
        SKIP $skip
        LIMIT $limit
        """
        data = session.run(query, search_term=search_term, skip=(page - 1) * page_size, limit=page_size)

        blogs = process_data(data)

        return render_template('index.html', blogs=blogs, page=page, page_size=page_size)
    else:
        query = """
        MATCH (b:Blog)-[:BELONGS_TO]->(category:Category)
        MATCH (b)-[:BELONGS_TO_REGION]->(region:Region)
        MATCH (b)-[:HAS_RELEVANCE]->(relevance:Relevance)
        MATCH (b)-[:TARGETS]->(target:TargetAudience)
        RETURN b.name AS name, b.url AS url, category.name AS category, b.publish_date AS publish_date,
                b.expire_date AS expire_date, region.name AS region, relevance.name AS relevance,
                collect(target.name) AS target_audience
        ORDER BY b.name
        SKIP $skip
        LIMIT $limit
        """
        data = session.run(query, skip=(page - 1) * page_size, limit=page_size)

        blogs = process_data(data)


        return render_template('index.html', blogs=blogs, page=page, page_size=page_size)

def process_data(data):
    blogs = []
    for record in data:
        blog = {
            "name": record["name"],
            "url": record["url"],
            "publish_date": record["publish_date"],
            "expire_date": record["expire_date"],
            "category": record["category"],
            "region": record["region"],
            "relevance": record["relevance"], 
            "target_audience": record["target_audience"]
        }

        if isinstance(blog["relevance"], list) and len(blog["relevance"]) > 1:
            blog["relevance"] = ", ".join(blog["relevance"])  # Join multiple relevance values with commas

        if isinstance(blog["target_audience"], list) and len(blog["target_audience"]) > 1:
            blog["target_audience"] = ", ".join(blog["target_audience"])  # Join multiple target audience values with commas

        blogs.append(blog)

    return blogs

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80,debug=True)
