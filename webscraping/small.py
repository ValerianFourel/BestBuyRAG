import json
import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException, 
    WebDriverException
)


import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging


def extract_all_reviews_across_pages(driver):
    """
    Extracts review information from all pages by handling pagination
    """
    all_pages_data = []
    page_number = 1
    first_page = True

    try:
        while True:
            logging.info(f"Processing page {page_number}")

            # Extract current page reviews
            current_page_df = extract_all_reviews_info(driver)
            logging.info(current_page_df.__len__)
            if not current_page_df.empty:
                all_pages_data.append(current_page_df)

            # Check for next page button
            try:
                next_page = driver.find_element(By.CSS_SELECTOR, "li.page.next")

                # If next button is disabled, we've reached the end
                if 'disabled' in next_page.get_attribute('class'):
                    logging.info("Reached last page")
                    break

                # Handle pagination differently for first page
                if first_page:
                    # Open in new tab
                    next_page_link = next_page.find_element(By.TAG_NAME, "a")
                    next_page_url = next_page_link.get_attribute('href')

                    # Open new tab
                    driver.execute_script(f"window.open('{next_page_url}', '_blank');")

                    # Switch to new tab
                    driver.switch_to.window(driver.window_handles[-1])
                    first_page = False
                else:
                    # Click next page
                    next_page.find_element(By.TAG_NAME, "a").click()

                    # Wait for page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "reviews-list"))
                    )

                page_number += 1

            except NoSuchElementException:
                logging.info("No more pages found")
                break

            except Exception as e:
                logging.error(f"Error navigating to next page: {e}")
                break

            # Add small delay to prevent rate limiting
            time.sleep(2)
    finally:
        # Combine all DataFrames
        final_df = pd.concat(all_pages_data, ignore_index=True)

    return final_df


def extract_all_reviews_info(driver):
    """
    Extracts information from all review items in the reviews list and returns a DataFrame
    """
    try:
        # Wait for reviews list to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "reviews-list"))
        )

        # Initialize list to store all reviews data
        all_reviews_data = []

        # Find all review items
        review_items = driver.find_elements(By.CLASS_NAME, "review-item")
        logging.info(f"Found {len(review_items)} review items")

        for index, review in enumerate(review_items, 1):
            try:
                review_data = {
                    'review_index': index,
                    'author': None,
                    'rating': None,
                    'review_title': None,
                    'verified_purchase': False,
                    'submission_date': None,
                    'ownership_duration': None,
                    'promo_consideration': False,
                    'review_text': None,
                    'image_count': 0,
                    'recommendation': False,
                    'helpful_count': 0,
                    'unhelpful_count': 0,
                    'brand_response': None,
                    'brand_response_date': None
                }

                # Extract author name
                try:
                    author_element = review.find_element(By.CSS_SELECTOR, "div.ugc-author strong")
                    review_data['author'] = author_element.text
                except:
                    pass

                # Extract rating
                try:
                    rating_element = review.find_element(By.CSS_SELECTOR, "p.visually-hidden")
                    rating_text = rating_element.text
                    review_data['rating'] = int(rating_text.split()[1])  # "Rated X out of 5 stars"
                except:
                    pass

                # Extract review title
                try:
                    title_element = review.find_element(By.CSS_SELECTOR, "h4.review-title")
                    review_data['review_title'] = title_element.text
                except:
                    pass

                # Check verified purchase
                try:
                    review_data['verified_purchase'] = bool(
                        review.find_elements(By.CSS_SELECTOR, "div.verified-purchaser-sv-wrapper")
                    )
                except:
                    pass

                # Extract submission date and ownership
                try:
                    date_element = review.find_element(
                        By.CSS_SELECTOR, 
                        "div.posted-date-ownership time.submission-date"
                    )
                    review_data['submission_date'] = date_element.get_attribute('title')

                    ownership_text = review.find_element(
                        By.CSS_SELECTOR, 
                        "div.posted-date-ownership"
                    ).text
                    if "Owned for" in ownership_text:
                        ownership_duration = ownership_text.split("Owned for")[1].split("when reviewed")[0].strip()
                        review_data['ownership_duration'] = ownership_duration
                except:
                    pass

                # Check promo consideration
                try:
                    promo_elements = review.find_elements(By.CSS_SELECTOR, "div.body-copy-sm")
                    for element in promo_elements:
                        if "promo considerations" in element.text.lower():
                            review_data['promo_consideration'] = True
                            break
                except:
                    pass

                # Extract review text
                try:
                    review_text_element = review.find_element(By.CSS_SELECTOR, "div.ugc-review-body p")
                    review_data['review_text'] = review_text_element.text
                except:
                    pass

                # Count images
                try:
                    images = review.find_elements(By.CSS_SELECTOR, "ul.gallery-preview li")
                    review_data['image_count'] = len(images)
                except:
                    pass

                # Check recommendation
                try:
                    review_data['recommendation'] = bool(
                        review.find_elements(By.CSS_SELECTOR, "svg.is-recommended-icon")
                    )
                except:
                    pass

                # Extract helpful/unhelpful counts
                try:
                    helpful_button = review.find_element(By.CSS_SELECTOR, "button.helpfulness-button")
                    review_data['helpful_count'] = int(helpful_button.text.split('(')[1].split(')')[0])

                    unhelpful_button = review.find_element(By.CSS_SELECTOR, "button.neg-feedback")
                    review_data['unhelpful_count'] = int(unhelpful_button.text.split('(')[1].split(')')[0])
                except:
                    pass

                # Extract brand response
                try:
                    brand_response_element = review.find_element(By.CSS_SELECTOR, "div.ugc-brand-response")
                    response_text = brand_response_element.find_element(
                        By.CSS_SELECTOR, 
                        "div.ugc-brand-response-body p"
                    ).text
                    review_data['brand_response'] = response_text

                    response_date = brand_response_element.find_element(
                        By.CSS_SELECTOR, 
                        "time.submission-date"
                    ).get_attribute('title')
                    review_data['brand_response_date'] = response_date
                except:
                    pass

                all_reviews_data.append(review_data)
                logging.info(f"Processed review {index}")

            except Exception as e:
                logging.error(f"Error processing review {index}: {e}")
                continue

        # Create DataFrame
        df = pd.DataFrame(all_reviews_data)

        # Convert dates to datetime
        try:
            df['submission_date'] = pd.to_datetime(df['submission_date'])
            df['brand_response_date'] = pd.to_datetime(df['brand_response_date'])
        except:
            pass

        # Save to CSV
        df.to_csv('reviews_data.csv', index=False)
        logging.info("Saved reviews data to CSV")

        return df

    except Exception as e:
        logging.error(f"Error extracting reviews: {e}")
        return pd.DataFrame()

# Example usage:
def process_reviews_page(driver):
    """Process the reviews page and return DataFrame of all reviews"""
    try:
        # Extract all reviews
        reviews_df = extract_all_reviews_info(driver)

        # Print summary
        if not reviews_df.empty:
            print("\nReviews Summary:")
            print(f"Total reviews: {len(reviews_df)}")
            print(f"Average rating: {reviews_df['rating'].mean():.2f}")
            print(f"Verified purchases: {reviews_df['verified_purchase'].sum()}")
            print(f"Reviews with images: {(reviews_df['image_count'] > 0).sum()}")
            print(f"Reviews with brand response: {reviews_df['brand_response'].notna().sum()}")

        return reviews_df

    except Exception as e:
        logging.error(f"Error processing reviews page: {e}")
        return pd.DataFrame()


def extract_price_info(driver):
    """
    Extracts price information from the webpage and returns it as a Pandas DataFrame.
    """
    try:
        # Wait for the pricing container to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flex.gvpc-price-1-2505-2"))
        )

        # Find the pricing container
        price_container = driver.find_element(By.CLASS_NAME, "flex.gvpc-price-1-2505-2")

        # Extract the main price
        try:
            price = price_container.find_element(By.CSS_SELECTOR, "div[data-testid='customer-price'] span[aria-hidden='true']").text
        except:
            price = None

        # Extract savings information
        try:
            savings = price_container.find_element(By.CSS_SELECTOR, "div[data-testid='savings']").text
        except:
            savings = None

        # Extract the comparable value
        try:
            comp_value = price_container.find_element(By.CSS_SELECTOR, "div[data-testid='regular-price'] span[aria-hidden='true']").text
        except:
            comp_value = None
        
        return price , savings , comp_value

    except Exception as e:
        logging.error(f"Error extracting price info: {e}")
        return pd.DataFrame(columns=["Price", "Savings", "Comparable Value"])

def extract_product_info_from_reviews(driver):
    """
    Extract product information from reviews tab and return the 5 key values
    """
    try:
        # Wait for product info container to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-info-container"))
        )

        # Find product info container
        product_info = driver.find_element(By.CLASS_NAME, "product-info-container")

        # Extract product name
        try:
            product_name = product_info.find_element(
                By.CSS_SELECTOR, 
                "h2.product-title a"
            ).text
        except:
            product_name = None

        # Initialize model and SKU values
        model1 = None
        model2 = None
        sku = None
        number = None

        # Extract model and SKU information
        try:
            model_sku_dl = product_info.find_element(By.CSS_SELECTOR, "dl.model-and-sku")
            dt_elements = model_sku_dl.find_elements(By.TAG_NAME, "dt")
            dd_elements = model_sku_dl.find_elements(By.TAG_NAME, "dd")
            for dd in dd_elements:
                logging.info(dd.text)  # This will print the text inside each <dd> tag
            

        except Exception as e:
            logging.error(f"Error extracting model/SKU info: {e}")

        return product_name, dd_elements[0].text, dd_elements[2].text

    except Exception as e:
        logging.error(f"Error extracting product info from reviews: {e}")
        return None, None, None

def find_and_process_sku_items(driver, sku_skip=160):
    """Find all SKU items and process their links, maintaining a single DataFrame"""
    try:
        # Create empty DataFrames with desired columns
        df = pd.DataFrame(columns=['name', 'model', 'sku_model', 'price', 'savings', 'comp_value'])
        all_reviews_df = pd.DataFrame()
        sku_count = 0

        while True:  # Main pagination loop
            # Wait for SKU items to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]"))
            )

            # Find all elements with IDs containing 'shop-sku-list-item'
            sku_items = driver.find_elements(By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]")
            logging.info(f"Found {len(sku_items)} SKU items on current page")
            sku_count += len(sku_items)

                    # Skip processing if we haven't reached the skip count
            if sku_count <= sku_skip:
                # Go directly to pagination section
                try:
                    # Check if next button is disabled
                    next_button_disabled = driver.find_elements(
                        By.CSS_SELECTOR, 
                        ".footer-pagination .sku-list-page-next.disabled"
                    )

                    if next_button_disabled:
                        logging.info("Reached last page, ending pagination loop")
                        break

                    # Click next page button
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((
                            By.CSS_SELECTOR, 
                            ".footer-pagination .sku-list-page-next"
                        ))
                    )
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    logging.info("Navigated to next page")
                    continue  # Skip rest of loop and start next iteration
                except Exception as e:
                    logging.error(f"Error during pagination: {e}")
                    break
            
            # Process each SKU item on current page
            for index, sku_item in enumerate(sku_items, 1):
                
                try:
                    # Find first link only
                    links = sku_item.find_elements(By.TAG_NAME, "a")
                    if links:
                        href = links[0].get_attribute('href')
                        if href:
                            # Open product page in new tab
                            driver.execute_script(f"window.open('{href}', '_blank');")
                            product_tab = driver.window_handles[-1]
                            driver.switch_to.window(product_tab)
                            time.sleep(2)

                            try:
                                # Find and click reviews link
                                reviews_link = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((
                                        By.XPATH, 
                                        "//a[contains(text(), 'See All Customer Reviews')]"
                                    ))
                                )
                                reviews_url = reviews_link.get_attribute('href')

                                # Open reviews in new tab
                                driver.execute_script(f"window.open('{reviews_url}', '_blank');")
                                reviews_tab = driver.window_handles[-1]
                                driver.switch_to.window(reviews_tab)
                                time.sleep(2)

                                # Extract product info
                                name, model, sku = extract_product_info_from_reviews(driver)
                                price, savings, comp_value = extract_price_info(driver)
                                df_reviews = extract_all_reviews_across_pages(driver)

                                # Add new row to DataFrame
                                new_row = pd.DataFrame({
                                    'name': [name],
                                    'model': [model],
                                    'sku_model': [sku],
                                    'price': [price],
                                    'savings': [savings],
                                    'comp_value': [comp_value]
                                })
                                df = pd.concat([df, new_row], ignore_index=True)

                                # Save current state of DataFrame
                                df.to_csv(f'products_data_v2_skipped{sku_skip}.csv', index=False)
                                logging.info(f"Updated DataFrame with item {index}")

                                # Add product info to reviews
                                names = [name] * len(df_reviews)
                                models = [model] * len(df_reviews)
                                df_reviews.insert(0, 'product_name', names)
                                df_reviews.insert(1, 'product_model', models)
                                all_reviews_df = pd.concat([all_reviews_df, df_reviews], ignore_index=True)
                                all_reviews_df.to_csv(f'all_products_reviews_v2_skipped{sku_skip}.csv', index=False)
                                logging.info(f"Saved complete reviews data with {len(all_reviews_df)} entries")

                                # Close reviews tab
                                driver.close()

                            except Exception as e:
                                logging.error(f"Error processing reviews for item {index}: {e}")

                            # Close product tab
                            driver.switch_to.window(product_tab)
                            driver.close()

                            # Return to main window
                            driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    logging.error(f"Error processing SKU item {index}: {e}")
                    continue

            # Check for next page button
            try:
                # Check if next button is disabled
                next_button_disabled = driver.find_elements(
                    By.CSS_SELECTOR, 
                    ".footer-pagination .sku-list-page-next.disabled"
                )

                if next_button_disabled:
                    logging.info("Reached last page, ending pagination loop")
                    break

                # Click next page button
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, 
                        ".footer-pagination .sku-list-page-next"
                    ))
                )
                next_button.click()
                time.sleep(2)  # Wait for page to load
                logging.info("Navigated to next page")

            except Exception as e:
                logging.error(f"Error during pagination: {e}")
                break

        return df

    except Exception as e:
        logging.error(f"Error finding SKU items: {e}")
        return pd.DataFrame()


def find_and_process_sku_items_old(driver):
    """Find all SKU items and process their links, maintaining a single DataFrame"""
    try:
        # Create empty DataFrame with desired columns
        df = pd.DataFrame(columns=['name', 'model', 'sku_model','price' , 'savings','comp_value'])
        all_reviews_df = pd.DataFrame()

        # Wait for any SKU items to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]"))
        )

        # Find all elements with IDs containing 'shop-sku-list-item'
        sku_items = driver.find_elements(By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]")
        logging.info(f"Found {len(sku_items)} SKU items")

# At the start of your script, before the loop, create an empty DataFrame to store all reviews
        all_reviews_df = pd.DataFrame()

        # Process each SKU item
        for index, sku_item in enumerate(sku_items, 1):
            try:
                # Find first link only
                links = sku_item.find_elements(By.TAG_NAME, "a")
                if links:
                    href = links[0].get_attribute('href')
                    if href:
                        # Open product page in new tab
                        driver.execute_script(f"window.open('{href}', '_blank');")
                        product_tab = driver.window_handles[-1]
                        driver.switch_to.window(product_tab)
                        time.sleep(2)

                        try:
                            # Find and click reviews link
                            reviews_link = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((
                                    By.XPATH, 
                                    "//a[contains(text(), 'See All Customer Reviews')]"
                                ))
                            )
                            reviews_url = reviews_link.get_attribute('href')

                            # Open reviews in new tab
                            driver.execute_script(f"window.open('{reviews_url}', '_blank');")
                            reviews_tab = driver.window_handles[-1]
                            driver.switch_to.window(reviews_tab)
                            time.sleep(2)

                            # Extract product info
                            name, model, sku = extract_product_info_from_reviews(driver)
                            price , savings , comp_value = extract_price_info(driver)
                            df_reviews =extract_all_reviews_across_pages(driver)
                            # Add new row to DataFrame
                            new_row = pd.DataFrame({
                                'name': [name],
                                'model': [model],
                                'sku_model': [sku], 'price' :[price] , 'savings':[savings] , 'comp_value': [comp_value]
                                
                            })
                            df = pd.concat([df, new_row], ignore_index=True)

                            # Save current state of DataFrame
                            df.to_csv('products_data_v2.csv', index=False)
                            logging.info(f"Updated DataFrame with item {index}")

                                                        # Inside your loop:
                            # Create copies of name and model values as lists with same length as df_reviews
                            names = [name] * len(df_reviews)
                            models = [model] * len(df_reviews)

                            # Add the product name and model columns to df_reviews
                            df_reviews.insert(0, 'product_name', names)  # Insert at position 0 (first column)
                            df_reviews.insert(1, 'product_model', models)  # Insert at position 1 (second column)

                            # Concatenate with the main reviews DataFrame
                            all_reviews_df = pd.concat([all_reviews_df, df_reviews], ignore_index=True)

                            # After the loop ends, save the complete DataFrame
                            all_reviews_df.to_csv('all_products_reviews_v2.csv', index=False)
                            logging.info(f"Saved complete reviews data with {len(all_reviews_df)} entries")


                            # Close reviews tab
                            driver.close()

                        except Exception as e:
                            logging.error(f"Error processing reviews for item {index}: {e}")

                        # Close product tab
                        driver.switch_to.window(product_tab)
                        driver.close()

                        # Return to main window
                        driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                logging.error(f"Error processing SKU item {index}: {e}")
                continue

        return df

    except Exception as e:
        logging.error(f"Error finding SKU items: {e}")
        return pd.DataFrame()



def find_and_process_sku_items_old(driver):
    """Find all SKU items and process their links"""
    try:
        # Wait for any SKU items to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]"))
        )

        # Find all elements with IDs containing 'shop-sku-list-item'
        sku_items = driver.find_elements(By.XPATH, "//*[contains(@id, 'shop-sku-list-item')]")

        logging.info(f"Found {len(sku_items)} SKU items")

        # Process each SKU item
        for index, sku_item in enumerate(sku_items, 1):
            try:
                # Find all links within the SKU item
                links = sku_item.find_elements(By.TAG_NAME, "a")

                for link_index, link in enumerate(links):
                    try:
                        # Get the href attribute
                        href = link.get_attribute('href')
                        if href:
                            # Open product page in new tab
                            driver.execute_script(f"window.open('{href}', '_blank');")

                            # Switch to the new tab
                            product_tab = driver.window_handles[-1]
                            driver.switch_to.window(product_tab)

                            # Wait for page to load
                            time.sleep(2)

                            try:
                                # Wait for and find the "See All Customer Reviews" link
                                reviews_link = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((
                                        By.XPATH, 
                                        "//a[contains(text(), 'See All Customer Reviews')]"
                                    ))
                                )

                                # Get the reviews link URL
                                reviews_url = reviews_link.get_attribute('href')

                                # Open reviews in another new tab
                                driver.execute_script(f"window.open('{reviews_url}', '_blank');")

                                # Switch to reviews tab
                                reviews_tab = driver.window_handles[-1]
                                driver.switch_to.window(reviews_tab)
                                extract_product_info_from_reviews(driver)

                                # Wait for reviews page to load
                                time.sleep(2)

                                # Take screenshot of reviews page
                                screenshot_name = f"sku_item_{index}_link_{link_index}_reviews.png"
                                driver.save_screenshot(screenshot_name)
                                logging.info(f"Saved reviews screenshot: {screenshot_name}")

                                # Close reviews tab
                                driver.close()

                            except Exception as e:
                                logging.error(f"Error processing reviews for item {index}: {e}")

                            # Switch back to product tab and close it
                            driver.switch_to.window(product_tab)
                            driver.close()

                            # Switch back to main window
                            driver.switch_to.window(driver.window_handles[0])
                        continue

                    except Exception as e:
                        logging.error(f"Error processing link {link_index} in SKU item {index}: {e}")
                        continue

            except Exception as e:
                logging.error(f"Error processing SKU item {index}: {e}")
                continue

    except Exception as e:
        logging.error(f"Error finding SKU items: {e}")
        return False

    return True


def find_product_list_id(driver):
    """
    Find all IDs containing 'shop-product-list' and return the unique one if it exists
    """
    try:
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Get all elements with an ID
        elements_with_id = driver.find_elements(By.XPATH, "//*[@id]")

        # Extract IDs and filter for those containing 'shop-product-list'
        product_list_ids = []
        for element in elements_with_id:
            element_id = element.get_attribute('id')
            if element_id and 'shop-product-list' in element_id:
                product_list_ids.append(element_id)

        # Print all found IDs
        logging.info("Found IDs containing 'shop-product-list':")
        for id_found in product_list_ids:
            logging.info(f"- {id_found}")

        # Check if there's exactly one matching ID
        if len(product_list_ids) == 1:
            logging.info(f"Found unique product list ID: {product_list_ids[0]}")
            return product_list_ids[0]
        elif len(product_list_ids) > 1:
            logging.warning(f"Found multiple product list IDs: {product_list_ids}")
            return product_list_ids[0]
        else:
            logging.warning("No product list IDs found")
            return None

    except Exception as e:
        logging.error(f"Error finding product list ID: {e}")
        return None



def click_link(driver):
    try:
        # Wait for the link to be clickable
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "us-link"))
        )
        # Click the link
        link.click()

    except Exception as e:
        logging.error(f"Error clicking link: {e}")
        # Optionally save screenshot
        driver.save_screenshot("error_clicking_link.png")

def process_urls(page_range):
    """Generate URLs for BestBuy pages"""
    base_url = "https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat311200050005&cp={}&id=pcat17071&iht=n&ks=960&list=y&sc=Global&st=categoryid%24pcmcat311200050005&type=page&usc=All%20Categories"

    for page_num in range(1, page_range + 1):
        yield page_num, base_url.format(page_num)

def scrape_product_data(driver, url, page_num):
    """Scrape product data from a single page"""
    products_data = []

    try:
        logging.info(f"Processing page {page_num}: {url}")
        driver.get(url)

        # Wait for product list to load
        wait = WebDriverWait(driver, 15)
        click_link(driver)
        productList = find_product_list_id(driver)
        logging.info(productList)
        find_and_process_sku_items(driver)




        product_list = wait.until(
            EC.presence_of_element_located((By.ID, productList))
        )
        
        logging.info(product_list)

        # Scroll to load all content
        for i in range(3):
            driver.execute_script(
                f"window.scrollTo(0, document.body.scrollHeight * {(i + 1) / 3});"
            )
            time.sleep(1)

        # Find all product items
        products = driver.find_elements(By.CSS_SELECTOR, "li.sku-item")

        for product in products:
            try:
                product_data = {
                    'name': 'N/A',
                    'price': 'N/A',
                    'model': 'N/A',
                    'sku': 'N/A',
                    'url': 'N/A',
                    'rating': 'N/A',
                    'availability': 'N/A',
                    'page_number': page_num
                }

                # Safe element extraction with explicit waits
                try:
                    product_data['name'] = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h4.sku-header"))
                    ).text.strip()
                except (TimeoutException, NoSuchElementException):
                    pass

                try:
                    product_data['price'] = product.find_element(
                        By.CSS_SELECTOR, "div.priceView-hero-price"
                    ).text.strip()
                except NoSuchElementException:
                    pass

                try:
                    product_data['model'] = product.find_element(
                        By.CSS_SELECTOR, "span.sku-value"
                    ).text.strip()
                except NoSuchElementException:
                    pass

                try:
                    product_data['sku'] = product.get_attribute('data-sku')
                except:
                    pass

                try:
                    product_data['url'] = product.find_element(
                        By.CSS_SELECTOR, "a.image-link"
                    ).get_attribute('href')
                except NoSuchElementException:
                    pass

                try:
                    product_data['rating'] = product.find_element(
                        By.CSS_SELECTOR, "span.c-reviews-v4"
                    ).get_attribute('aria-label')
                except NoSuchElementException:
                    pass

                try:
                    product_data['availability'] = product.find_element(
                        By.CSS_SELECTOR, "span.fulfillment-fulfillment-summary"
                    ).text.strip()
                except NoSuchElementException:
                    pass

                products_data.append(product_data)
                logging.info(f"Scraped product: {product_data['name']}")

            except Exception as e:
                logging.error(f"Error extracting product data: {e}")
                continue

    except Exception as e:
        logging.error(f"Error processing page {page_num}: {e}")
        try:
            driver.save_screenshot(f"error_page_{page_num}.png")
        except:
            pass

    return products_data

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Set up the GeckoDriver path
    geckodriver_path = "/usr/local/bin/geckodriver"

    # Set up Firefox options
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.log.level = "trace"

    # Set up the Firefox service
    firefox_service = FirefoxService(executable_path=geckodriver_path)

    all_products = []

    try:
        # Create a single driver instance
        driver = webdriver.Firefox(service=firefox_service, options=firefox_options)

        # Process each page
        for page_num, url in process_urls(18):  # 18 pages total
            products_data = scrape_product_data(driver, url, page_num)
            all_products.extend(products_data)

            # Add delay between pages
            time.sleep(3)

        # Save results to JSON file
        output_file = 'bestbuy_phones.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)

        logging.info(f"Scraping completed. Total products: {len(all_products)}")
        logging.info(f"Results saved to {output_file}")

    except Exception as e:
        logging.error(f"Critical error: {e}")

    finally:
        # Cleanup
        try:
            driver.quit()
            logging.info("Browser closed successfully")
        except Exception as e:
            logging.error(f"Error closing browser: {e}")

if __name__ == "__main__":
    main()
