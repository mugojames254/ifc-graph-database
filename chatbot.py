import json
import requests
from neo4j import GraphDatabase


class IFCChatBot:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, ollama_url="http://localhost:11434"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.ollama_url = ollama_url
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def query_database(self, cypher_query):
        """Execute Cypher query on Neo4j database"""
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]
    
    def get_database_schema(self):
        """Get database schema information"""
        queries = {
            "node_types": "CALL db.labels()",
            "relationship_types": "CALL db.relationshipTypes()",
            "element_types": "MATCH (e:Element) RETURN DISTINCT e.type AS element_type, COUNT(*) AS count ORDER BY count DESC"
        }
        
        schema_info = {}
        for key, query in queries.items():
            schema_info[key] = self.query_database(query)
        
        return schema_info
    
    def call_ollama(self, prompt):
        """Send prompt to local Ollama Llama 3.1 model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error calling Llama model: {str(e)}"
    
    def generate_cypher_query(self, user_question):
        """Generate Cypher query based on user question"""
        schema = self.get_database_schema()
        
        prompt = f"""You are a Cypher query generator for a Neo4j database containing IFC building model data.

Database Schema:
- Node types: {[item['label'] for item in schema['node_types']]}
- Relationship types: {[item['relationshipType'] for item in schema['relationship_types']]}
- Element types available: {[f"{item['element_type']} ({item['count']} items)" for item in schema['element_types']]}

Node structure:
- Project: id, name, type
- Element: id, name, guid, type, objectType
- Structure: id, name, type
- Metadata: timestamp, element_count, filtered_types

Relationships:
- (Project)-[:CONTAINS]->(Element)
- (Structure)-[:CONTAINS]->(Element)

User question: "{user_question}"

Generate ONLY a Cypher query that answers this question. Return just the query without explanation or formatting."""

        return self.call_ollama(prompt)
    
    def format_response(self, user_question, query_result):
        """Format the query result into a natural language response"""
        prompt = f"""Based on the following database query results, provide a clear and concise answer to the user's question.

User question: "{user_question}"

Query results:
{json.dumps(query_result, indent=2)}

Provide a natural language response that directly answers the question. Be specific with numbers and details from the data."""

        return self.call_ollama(prompt)
    
    def chat(self, user_question):
        """Main chat function"""
        print(f"\nUser: {user_question}")
        print("Bot: Generating query...")
        
        # Generate Cypher query
        cypher_query = self.generate_cypher_query(user_question).strip()
        print(f"Generated query: {cypher_query}")
        
        try:
            # Execute query
            query_result = self.query_database(cypher_query)
            print(f"Query returned {len(query_result)} results")
            
            # Format response
            if query_result:
                response = self.format_response(user_question, query_result)
            else:
                response = "No data found matching your query."
            
            print(f"Bot: {response}")
            return response
            
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            print(f"Bot: {error_msg}")
            return error_msg
    
    def close(self):
        """Close database connection"""
        self.driver.close()


def main():
    # Configuration
    neo4j_uri = "bolt://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "4central"
    
    # Initialize chatbot
    chatbot = IFCChatBot(neo4j_uri, neo4j_user, neo4j_password)
    
    print("IFC Graph Database Chatbot initialized!")
    print("Ask questions about your building model. Type 'quit' to exit.")
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            if user_input:
                chatbot.chat(user_input)
    
    except KeyboardInterrupt:
        print("\nGoodbye!")
    
    finally:
        chatbot.close()


if __name__ == "__main__":
    main()