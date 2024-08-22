#Importação de Bibliotecas

import json
import os
from datetime import datetime

import yfinance as yf

from crewai import Agent, Task, Crew, Process

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

import streamlit as st


#Criando Yahoo Finance Tool

def fetch_stock_price(ticket):
    stock = yf.download(ticket, start="2023-08-08", end="2024-08-08")
    return stock

yahoo_finance_tool = Tool(
    name = "Yahoo Finance Tool",
    description = "Fetches stocks prices for {ticket} from the last year about a specific company from Yahoo Finance API",
    func= lambda ticket: fetch_stock_price(ticket)
)


# In[4]:


#Importando OpenaAI LLM - GPT

os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
llm = ChatOpenAI(model="gpt-3.5-turbo")


# In[5]:


stockPriceAnalyst = Agent(
    role="Senior stock price Analyst",
    goal="Find the {ticket} stock price and analyses trends",
    backstory=""" You're highly experienced in analysing the price of 
    an especific stock and make predictions about its future. """,
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    allow_delegation = False,
    tools=[yahoo_finance_tool]
)


# In[6]:


getStockPrice = Task(
    description="Analyse the stock {ticket} price history and create a trend analyses of up, down or sideways",
    agent=stockPriceAnalyst,
    expected_output=""" Specify the current trend stock price - up, down or sideways.
    eg. stock= 'AAPL, price UP' """
)


# In[7]:


#Importando Duck Duck Go Tool

search_tool = DuckDuckGoSearchResults(backend='news', num_results=10)


# In[8]:


newsAnalyst = Agent(
    role="Stock News Analyst",
    goal=""" Create a short summary of the market news related to the stock {ticket} company. 
    Specify the current trend - up, down or sideways with the news context. 
    For each request stock asset, specify a number between 0 and 100, where 0 is extreme fear and 100 is extreme greed. """,
    backstory=""" You're a highly experienced in analysing the market trends and news, having tracked assets for more than 10 years.
    You're also master level analysts in the traditional markets and have deep understanding about human psychology. 
    You understand news, theirs titles and informations, but you look at those with a health dose of skepticism.
    You consider also the source of the news articles. """,
    verbose=True,
    llm=llm,
    max_iter=10,
    memory=True,
    allow_delegation = False,
    tools=[search_tool]
)


# In[9]:


getNews = Task(
    description=f"""Take the stock and always include BTC to it (if not request).
    Use the search tool to search each one individually.
    The current date is {datetime.now()}.
    Compose the results into a helpful report""",
    agent=newsAnalyst,
    expected_output="""A summary of the overall market and one sentence summary for each request asset.
    Include a fear/greed score for each asset based on the news. Use format:
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE>"""
)


# In[10]:


stockAnalystWriter = Agent(
    role="Senior Stock Analyst Writer",
    goal=""" Analyze the trends, price and news and write an insightfull compelling and informative 3 paragraph long newsletter based on the stock report and price trend. """,
    backstory=""" You're widely accepted as the best stock analyst in the market.
    You understand complex concepts and create compelling stories and narratives that resonate with wider audiences.
    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental analysis.
    You're able to hold multiple opinions when analysing anything. """,
    verbose=True,
    llm=llm,
    max_iter=5,
    memory=True,
    allow_delegation = True
)


# In[11]:


writeAnalysis = Task(
    description=""" Use the stock price trend and the stock news report to create an analysis and write the newsletter about the {ticket} company that is brief and highlishts the most important points.
    Focus on the stock price, news and fear/greed score. What are the near future considerations?
    Include the previous analysis of stock trend and news summary. """,
    agent=stockAnalystWriter,
    expected_output=""" An eloquent 3 paragraphs newsletter formatted as markdown in an easy readable manner. It should contain: 
    - 3 bullets executive summary
    - Introduction - set the overall picture and spike up the interest
    - Main part provides the meat of the analysis including the news summary and fear/greed scores.
    - Summary - key facts and concrete future trend prediction - up, down or sideways. """,
    context = [getStockPrice, getNews]
)


# In[12]:


crew = Crew(
    agents = [stockPriceAnalyst, newsAnalyst, stockAnalystWriter],
    tasks = [getStockPrice, getNews, writeAnalysis],
    verbose = 2,
    process = Process.hierarchical,
    full_output = True,
    share_crew = False,
    manager_llm = llm,
    max_iter=15
)

# results = crew.kickoff(inputs={'ticket': 'KO'})

with st.sidebar:
    st.header('Enter the Stock to Research')

    with st.form(key='research_form'):
        topic = st.text_input("Select the ticket")
        submit_button = st.form_submit_button(label = "Run Research")

if submit_button:
    if not topic:
        st.error("Please fill the ticket field")
    else:
        results = crew.kickoff(inputs={'ticket': topic})

        st.subheader("Results for {ticket} stock:")
        st.write(results['final_output'])