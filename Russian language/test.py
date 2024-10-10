from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def extract_info_from_shadow_dom(driver):
    script = """
    function getShadowRoot(element) {
        return element.shadowRoot;
    }
    
    function safeQuerySelector(element, selector, step) {
        try {
            const result = element.querySelector(selector);
            if (!result) {
                console.log(`Step ${step}: querySelector returned null for selector "${selector}"`);
                return null;
            }
            console.log(`Step ${step}: Successfully found element with selector "${selector}"`);
            return result;
        } catch (error) {
            console.log(`Error in step ${step}: ${error.message}`);
            return null;
        }
    }
    
    const appRoot = safeQuerySelector(document, 'body > app-root', 'appRoot');
    if (!appRoot) return {error: 'Failed at appRoot'};
    const shadowRoot1 = getShadowRoot(appRoot);
    if (!shadowRoot1) return {error: 'Failed to get shadowRoot of appRoot'};
    const main = safeQuerySelector(shadowRoot1, 'main#maincontent', 'main');
    if (!main) return {error: 'Failed at main'};
    const pageContainer = safeQuerySelector(main, 'div.page-container', 'pageContainer');
    if (!pageContainer) return {error: 'Failed at pageContainer'};
    const routerSlot = safeQuerySelector(pageContainer, 'router-slot', 'routerSlot');
    if (!routerSlot) return {error: 'Failed at routerSlot'};
    const detailsPageRouter = safeQuerySelector(routerSlot, 'details-page-router', 'detailsPageRouter');
    if (!detailsPageRouter) return {error: 'Failed at detailsPageRouter'};
    const collectionPage = safeQuerySelector(detailsPageRouter, 'collection-page', 'collectionPage');
    if (!collectionPage) return {error: 'Failed at collectionPage'};
    const shadowRoot2 = getShadowRoot(collectionPage);
    if (!shadowRoot2) return {error: 'Failed to get shadowRoot of collectionPage'};
    const pageCollection = safeQuerySelector(shadowRoot2, 'div#page-container', 'pageCollection');
    if (!pageCollection) return {error: 'Failed at pageCollection'};
    const tabManager = safeQuerySelector(pageCollection, 'tab-manager', 'tabManager');
    if (!tabManager) return {error: 'Failed at tabManager'};
    const collectionBrowserContainer = safeQuerySelector(tabManager, 'div#collection-browser-container', 'collectionBrowserContainer');
    if (!collectionBrowserContainer) return {error: 'Failed at collectionBrowserContainer'};
    const collectionBrowser = safeQuerySelector(collectionBrowserContainer, 'collection-browser', 'collectionBrowser');
    if (!collectionBrowser) return {error: 'Failed at collectionBrowser'};
    const shadowRoot3 = getShadowRoot(collectionBrowser);
    if (!shadowRoot3) return {error: 'Failed to get shadowRoot of collectionBrowser'};
    const contentContainer = safeQuerySelector(shadowRoot3, 'div#content-container.desktop', 'contentContainer');
    if (!contentContainer) return {error: 'Failed at contentContainer'};
    const rightColumn = safeQuerySelector(contentContainer, 'div#right-column', 'rightColumn');
    if (!rightColumn) return {error: 'Failed at rightColumn'};
    const infiniteScroller = safeQuerySelector(rightColumn, 'infinite-scroller.grid', 'infiniteScroller');
    if (!infiniteScroller) return {error: 'Failed at infiniteScroller'};
    const shadowRoot4 = getShadowRoot(infiniteScroller);
    if (!shadowRoot4) return {error: 'Failed to get shadowRoot of infiniteScroller'};
    const container = safeQuerySelector(shadowRoot4, 'section#container', 'container');
    if (!container) return {error: 'Failed at container'};
    const articles = container.querySelectorAll('article.cell-container');
    
    console.log(`Found ${articles.length} articles`);
    
    const results = [];
    articles.forEach((article, index) => {
        const tileDispatcher = safeQuerySelector(article, 'tile-dispatcher', `Article ${index + 1} - tileDispatcher`);
        if (tileDispatcher) {
            const shadowRoot5 = getShadowRoot(tileDispatcher);
            const hoverableContainer = safeQuerySelector(shadowRoot5, 'div#container.hoverable', `Article ${index + 1} - hoverableContainer`);
            if (hoverableContainer) {
                const link = safeQuerySelector(hoverableContainer, 'a', `Article ${index + 1} - link`);
                if (link) {
                    results.push({
                        articleIndex: index + 1,
                        href: link.href,
                        text: link.textContent.trim()
                    });
                }
            }
        }
    });
    
    return {results: results, error: null};
    """
    
    try:
        result = driver.execute_script(script)
        
        if result.get('error'):
            print(f"An error occurred: {result['error']}")
            return []
        else:
            links = result.get('results', [])
            print(f"Found {len(links)} articles")
            return links

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def save_links_to_file(links, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Index', 'URL', 'Text'])  # Write header
        for link in links:
            writer.writerow([link['articleIndex'], link['href'], link['text']])
    print(f"Links saved to {filename}")

def main():
    driver = setup_driver()
    all_articles = []
    try:
        url = 'https://archive.org/details/booksbylanguage_russian'
        driver.get(url)
        time.sleep(5)  # Wait for initial page load

        for i in range(265):  # Load 10 pages worth of content
            print(f"Extracting page {i+1}...")
            articles = extract_info_from_shadow_dom(driver)
            new_articles = [article for article in articles if article not in all_articles]
            all_articles.extend(new_articles)
            print(f"Found {len(new_articles)} new articles")

            # Scroll to load more content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Wait for new content to load

        print(f"\nTotal unique articles found: {len(all_articles)}")
        
        # Save links to a CSV file
        save_links_to_file(all_articles, 'russian_books_links.csv')

    finally:
        driver.quit()

if __name__ == "__main__":
    main()