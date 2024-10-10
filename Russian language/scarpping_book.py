import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def check_full_text(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body.navia.ia-module.tiles.responsive')))
        #time.sleep(20)

        script = """
        function safeQuerySelector(element, selector, step) {
            try {
                const result = element.querySelector(selector);
                if (!result) {
                    console.log(`Step ${step}: querySelector returned null for selector "${selector}"`);
                    return null;
                }
                return result;
            } catch (error) {
                console.log(`Error in step ${step}: ${error.message}`);
                return null;
            }
        }
        
        const body = document.querySelector('body.navia.ia-module.tiles.responsive');
        if (!body) return false;
        const wrap = safeQuerySelector(body, 'div#wrap', 'wrap');
        if (!wrap) return false;
        const main = safeQuerySelector(wrap, 'main#maincontent', 'main');
        if (!main) return false;
        const containerOuters = main.querySelectorAll('div.container.container-ia.width-max.relative-row-wrap');
        if (containerOuters.length >= 2) {
            //return containerOuters.length
            const containerOuter = containerOuters[1]; // Get the second element (index 1)    
        if (!containerOuter) return false;
        const containerInner = safeQuerySelector(containerOuter, 'div.container.container-ia', 'containerInner');
        if (!containerInner) return false;
        const row = safeQuerySelector(containerInner, 'div.relative-row.row', 'row');
        if (!row) return false;
        const col = safeQuerySelector(row, 'div.col-sm-4.thats-right.item-details-archive-info', 'col');
        if (!col) return false;
        const section = safeQuerySelector(col, 'section.boxy.item-download-options', 'section');
        if (!section) return false;
        const formatGroups = section.querySelectorAll('div.format-group');
        for (let link of formatGroups){
            const fullTextLinks = link.querySelector('a.format-summary.download-pill');
            //return fullTextLinks.textContent.trim().toLowerCase().includes('chocr')
            if (fullTextLinks !== null){
                if (fullTextLinks.textContent.trim().toLowerCase().includes('full text')) {
                    return fullTextLinks.href;  // Return the full text link
            }
            }
        }

        if (!formatGroup) return false;
        return false;}
        """

        return driver.execute_script(script)

    except Exception as e:
        logger.error(f"An error occurred while checking {url}: {e}")
        return False

def extract_full_text(driver, full_text_url):
    try:
        driver.get(full_text_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body.navia')))

        script = """
        function safeQuerySelector(element, selector, step) {
            try {
                const result = element.querySelector(selector);
                if (!result) {
                    console.log(`Step ${step}: querySelector returned null for selector "${selector}"`);
                    return null;
                }
                return result;
            } catch (error) {
                console.log(`Error in step ${step}: ${error.message}`);
                return null;
            }
        }
        
        const body = document.querySelector('body.navia');
        if (!body) return false;
        const wrap = safeQuerySelector(body, 'div#wrap', 'wrap');
        if (!wrap) return false;
        const main = safeQuerySelector(wrap, 'main#maincontent', 'main');
        if (!main) return false;
        const container = safeQuerySelector(main, 'div.container.container-ia', 'container');
        if (!container) return false;
        const preElement = safeQuerySelector(container, 'pre', 'pre');
        if (!preElement) return false;

        return preElement.innerText;  // Return the text content of the <pre> element
        """

        return driver.execute_script(script)

    except Exception as e:
        logger.error(f"An error occurred while checking {full_text_url}: {e}")
        return None

def main():
    driver = setup_driver()
    try:
        # Read the CSV file
        df = pd.read_csv('russian_books_links.csv')[7830:]
        
        #full_text_links = []

        for index, row in df.iterrows():
            url = row['URL']
            logger.info(f"Checking {url} for Full Text link...")
            full_text_url = check_full_text(driver, url)
            print(full_text_url)
            '''if isinstance(full_text_url, str): 
                print(full_text_url) # Print error message if row was not found
            else:
                for child in full_text_url:
                    print(f"Tag Name: {child['tagName']}, Inner Text: {child['innerText']}")'''
            if full_text_url:
                logger.info(f"Full Text found for {url}: {full_text_url}")
                #full_text_links.append(full_text_url)

                full_text = extract_full_text(driver, full_text_url)
                if full_text:
                    # Save the extracted text to a file
                    filename = f"full_text_{index}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    logger.info(f"Text saved to {filename}")
                    print(index)

            time.sleep(2)  # Wait between requests to avoid overloading the server

        #file_number = 0
        # Extract text from each Full Text link and save to a file
        '''for full_text_url in full_text_links:
            logger.info(f"Extracting text from {full_text_url}...")
            full_text = extract_full_text(driver, full_text_url)
            if full_text:
                # Save the extracted text to a file
                filename = f"full_text_{file_number}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                logger.info(f"Text saved to {filename}")
            file_number += 1'''

    finally:
        driver.quit()

if __name__ == "__main__":
    main()