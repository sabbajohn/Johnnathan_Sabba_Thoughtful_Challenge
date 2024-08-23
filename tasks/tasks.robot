*** Settings ***
Documentation     Task to scrape news from a website and save the results.
Library           RPA.Robocorp.WorkItems
Library           RPA.Python

*** Tasks ***
Run News Scraper
    [Setup]     Load Work Item Variables
    Run Python Script  src/news_scraper.py

*** Keywords ***
Load Work Item Variables
    ${work_item} =  Get Input Work Item
    Set Task Variables  ${work_item}
