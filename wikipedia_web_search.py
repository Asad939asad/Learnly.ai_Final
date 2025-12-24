import requests

def get_wikipedia_summary(topic):
    url = "https://en.wikipedia.org/w/api.php"
    
    # REQUIRED: Wikipedia blocks requests without a unique User-Agent
    headers = {
        "User-Agent": "AgenticAIProject/1.0 (asadirfan358@example.com)" 
    }
    
    # 1. First, search for the page
    search_params = {
        "action": "opensearch",
        "search": topic,
        "limit": 1,
        "format": "json"
    }
    
    # Pass 'headers=headers' here
    response = requests.get(url, params=search_params, headers=headers)
    
    # Debugging: Check if request was successful
    if response.status_code != 200:
        return f"Error: API returned status code {response.status_code}"
        
    try:
        search_data = response.json()
    except requests.exceptions.JSONDecodeError:
        print("Raw Response Text:", response.text) # Print the error page to see why it failed
        return "Failed to parse JSON. See raw response above."

    if not search_data[1]:
        return "No results found."
    
    title = search_data[1][0]
    
    # 2. Get the summary
    summary_params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": title,
        "exintro": True,
        "explaintext": True
    }
    
    # Pass 'headers=headers' here too
    summary_response = requests.get(url, params=summary_params, headers=headers).json()
    
    pages = summary_response["query"]["pages"]
    page_id = next(iter(pages))
    summary = pages[page_id].get("extract", "No summary available.")
    
    return f"Title: {title}\nSummary: {summary}"

# Usage
print(get_wikipedia_summary("elon musk"))