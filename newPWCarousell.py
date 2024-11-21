'''
Do comparison for dictionary(newly scraped) and the csv, check if there are new items and
then we append to the csv file. 

If there is a new data, send it through telegram bot. can run as polling for the 
telegram bot

do an ss at every stage so in case there is a crash, we have the last seen reason 
for crash


'''



from playwright.sync_api import Playwright, sync_playwright, expect
import csv
from bs4 import BeautifulSoup
import time
from datetime import datetime
from random import randint

def run(playwright: Playwright) -> None:
    listOfSearches2b = ['y15', 'krr', 'rxz', 'aerox', 'y16', 'nmax', 'burgman']
    # listOfSearches2b = ['y15', 'krr']
    # listOfSearches2a = ['cb400x', 'super 4']
    
    # Date Configuration
    now = datetime.now()
    dateTimeNow = now.strftime("%d-%m-%Y %H:%M:%S")

    # Website search
    websiteLink = "https://www.carousell.sg"
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(websiteLink)
    toggle = True
    for searchItem in listOfSearches2b:
        print(f"Running Search for {searchItem} at {dateTimeNow}")
        page.get_by_placeholder("Search for an item").click()
        page.get_by_placeholder("Search for an item").fill(searchItem)
        page.get_by_role("button", name=f"{searchItem} in Class 2B").click() # Search button
        page.get_by_role("button", name="Sort:Best Match").click()
        page.get_by_text("Recent").click()
        if toggle:
            page.get_by_role("button", name="Condition").click()
            page.locator("label").filter(has_text="Used").locator("rect").click()
            toggle = False
    
        # Wait for the page to fully load
        time.sleep(10)

        # Extract page content as HTML
        html_content = page.content()
        ''' # For Debugging
        # Save the HTML content to a text file
        with open(f"page_content_{searchItem}.txt", "w", encoding="utf-8") as file:
            file.write(html_content)
        '''
        soup = BeautifulSoup(html_content, "html.parser")
        keys = ['Date', 'Username', 'Name', 'Before Price', 'After Price', 'Link', 'filtered_link']
        data = {key: [] for key in keys}
        links = soup.find_all("a")
        # print(links)
        for link in links:
            data['Date'].append(dateTimeNow)
            href = link.get("href")
            
            if href[:3] == "/u/":
                userName = href[3:].split("/")[0]
                data['Username'].append(userName)
            
            if href[:3] == "/p/":  # Ensure there is an href attribute
                saveLink = websiteLink + href.str.replace(r'\?.*$', '', regex=True)
                try:
                    productName, price = link.get_text().split("S$")
                    # print("Name: ", productName)
                    # print("Price: S$", price)
                    # print("link: ", href)
                    data['Name'].append(productName)
                    data['Before Price'].append("Not Slashed")
                    data['After Price'].append(price)
                    data['Link'].append(saveLink)
                except ValueError:
                    productName, price, beforePrice = link.get_text().split("S$")
                    # print("Name: ", productName)
                    # print("Price Before: ", beforePrice)
                    # print("Price Discounted: S$", price)
                    # print("link: ", href)
                    data['Name'].append(productName)
                    data['Before Price'].append(beforePrice)
                    data['After Price'].append(price)
                    data['Link'].append(saveLink)
            file_name = f'{searchItem}.csv'
        # print(data)
        # Here, the dictionary is complete. I want to compare with csv
        appendToCsv(data, file_name)

    # ---------------------
    context.close()
    browser.close()
    print("------------------------------Done search------------------------------------")


def runCarousellSearch():
    with sync_playwright() as playwright:
        run(playwright)

def appendToCsv(data: dict, file_name: str):
    # Open the file in append mode and create it if it doesn't exist
    with open(file_name, 'a', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # If the file is empty, write the headers first
        if file.tell() == 0:  # Check if the file is empty
            writer.writerow(data.keys())  # Write dictionary keys as headers
        
        # Write the rows (transpose the dictionary values to rows)
        rows = zip(*data.values())
        writer.writerows(rows)  

def compareDictToCsv(data: dict, file_name: str):
    scraped_csv = file_name
    scraped_df = pd.read_csv(scraped_csv)
    scraped_df['Link'] = scraped_df['Link'].str.extract(r'/p/([^/?]+)')
    
    old_csv = 'rxz.csv'
    old_df = pd.read_csv(old_csv)
    old_df['Link'] = old_df['Link'].str.extract(r'/p/([^/?]+)')
    
    new_links = scraped_df[~scraped_df['Link'].isin(old_df['Link'])]

def runMainProgram():
    prevDay = 0

    # Timing Configurations
    morningCheck = 11 # Morning check at 11 am
    afternoonCheck = 15 # Afternoon check at 3 pm
    nightCheck = 21 # Night check at 9 pm
    lateNightCheck = 2 # Late Check at 2 am

    while True:
        now = datetime.now()
        dateTimeNow = now.strftime("%d-%m-%Y %H:%M:%S")
        day = int(now.strftime("%d"))
        hour = int(now.strftime("%H"))

        if prevDay != day:
            print(f"New Day: {dateTimeNow}")
            prevDay = day
            dailyCheck = [morningCheck, afternoonCheck, nightCheck, lateNightCheck]

        if hour in dailyCheck:
            runCarousellSearch()
            dailyCheck.remove(hour)

        # Run every 1 hour from end search
        time.sleep(3600)

runMainProgram()