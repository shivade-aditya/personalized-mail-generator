import uuid
import pandas as pd
import chromadb
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Get user input for the job link
job_link = input("Please enter the job posting link: ")

# Initialize Groq Chat model
llm = ChatGroq(
    temperature=0, 
    groq_api_key='YOUR API KEY', 
    model_name="llama-3.3-70b-versatile"
)

# Load job posting from the user-provided URL
loader = WebBaseLoader(job_link)
page_data = loader.load().pop().page_content


# Define prompt template for extracting job details
prompt_extract = PromptTemplate.from_template(
    """
    ### SCRAPED TEXT FROM WEBSITE:
    {page_data}
    ### INSTRUCTION:
    The scraped text is from the career's page of a website.
    Your job is to extract the job postings and return them in JSON format containing the 
    following keys: `role`, `experience`, `skills` and `description`.
    Only return the valid JSON.
    ### VALID JSON (NO PREAMBLE):    
    """
)

# Extract job details using Groq model
chain_extract = prompt_extract | llm 
res = chain_extract.invoke(input={'page_data': page_data})

# Parse extracted JSON response
json_parser = JsonOutputParser()
json_res = json_parser.parse(res.content)

# Print extracted job details
print(json_res)

# Load portfolio data from CSV
df = pd.read_csv("my_portfolio.csv")

# Initialize Chroma client
client = chromadb.PersistentClient('vectorstore')
collection = client.get_or_create_collection(name="portfolio")

# Add portfolio items to Chroma collection
if not collection.count():
    for _, row in df.iterrows():
        collection.add(documents=row["Techstack"],
                       metadatas={"links": row["Links"]},
                       ids=[str(uuid.uuid4())])

# Query relevant portfolio links based on job skills
links = collection.query(query_texts=json_res['skills'], n_results=2).get('metadatas', [])
print(links)

# Define prompt template for generating cold email
prompt_email = PromptTemplate.from_template(
    """
    ### JOB DESCRIPTION:
    {job_description}
    
    ### INSTRUCTION:
    You are Aditya, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company dedicated to facilitating
    the seamless integration of business processes through automated tools. 
    Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
    process optimization, cost reduction, and heightened overall efficiency. 
    Your job is to write a cold email to the client regarding the job mentioned above describing the capability of AtliQ 
    in fulfilling their needs.
    Also add the most relevant ones from the following links to showcase Atliq's portfolio: {link_list}
    Remember you are Aditya, BDE at AtliQ. 
    Do not provide a preamble.
    ### EMAIL (NO PREAMBLE):
    """
)

# Generate cold email using Groq model
chain_email = prompt_email | llm
res_email = chain_email.invoke({"job_description": str(json_res), "link_list": links})

# Print generated cold email
print(res_email.content)
