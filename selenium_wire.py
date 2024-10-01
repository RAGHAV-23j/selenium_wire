import sys
import time
import numpy as np
import cv2 as cv
# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains 
import os
import time
from PIL import Image
import requests
import re
import pytesseract

# Set up download directory
save_folder = os.path.join(os.getcwd(), 'downloaded_pdfs')
if not os.path.exists(save_folder):
	os.makedirs(save_folder)

# Configure Chrome options
chrome_options = Options()
prefs = {
	"download.default_directory": save_folder,  # Specify the directory for downloads
	"download.prompt_for_download": False,  # Disable the prompt for download
	"download.directory_upgrade": True,  # Enable downloading in a specified directory
	"plugins.always_open_pdf_externally": False,  # Always open PDFs externally (download instead of open)
	"safebrowsing.enabled": True  # Enable safe browsing to prevent download blocking
}
chrome_options.add_experimental_option("prefs", prefs)

# Specify the path where your ChromeDriver is located and use Service in Selenium 4
chrome_driver_path = '/usr/bin/chromedriver'  # Update with the correct path
service = Service(chrome_driver_path)

# Launch the WebDriver with Selenium 4
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the website
driver.get('https://judgments.ecourts.gov.in')
# actions = ActionChains(driver)

valid_captcha = False

while not valid_captcha:
	time.sleep(2)

	try:
		captcha_element = driver.find_element(By.ID, "captcha_image")  # Updated to Selenium 4 format (captcha_image_pdf)
		# print(captcha_element.get_attribute('outerHTML'))
		# Get the location and size of the CAPTCHA image
		location = captcha_element.location
		size = captcha_element.size
		# print(location)
		# print(size)

		# Take a screenshot of the entire page
		screenshot_path = 'screenshot.png'
		driver.save_screenshot(screenshot_path)
		print(f'Screenshot saved as {screenshot_path}')

		# Load the screenshot image using PIL (Pillow)
		image = Image.open(screenshot_path)

		# Define the coordinates for cropping (left, top, right, bottom)
		left = location['x']
		top = location['y']
		right = left + size['width']
		bottom = top + size['height']

		# Crop the image to get only the CAPTCHA
		captcha_image = image.crop((left, top, right, bottom))
		captcha_image_path = 'cropped_captcha.png'
		captcha_image.save(captcha_image_path)

		print(f"CAPTCHA image cropped and saved as {captcha_image_path}")

		# Process the CAPTCHA image using OpenCV and Tesseract (same as before)
		image_path = 'cropped_captcha.png'
		img_cv = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
		_, img_bin = cv.threshold(img_cv, 150, 255, cv.THRESH_BINARY_INV)
		kernel = np.ones((1, 1), np.uint8)
		img_lines_removed = cv.morphologyEx(img_bin, cv.MORPH_OPEN, kernel, iterations=2)
		img_blur = cv.medianBlur(img_lines_removed, 3)
		img_inverted = cv.bitwise_not(img_blur)
		processed_image_path = 'processed_image_no_cross.png'
		cv.imwrite(processed_image_path, img_inverted)

		img_pil = Image.fromarray(cv.bitwise_not(img_inverted))
		captcha_text = pytesseract.image_to_string(processed_image_path, config='--psm 6')

		# Process the extracted text to solve the CAPTCHA
		input_string = captcha_text.replace(' ', '').strip()
		match = re.match(r'(\d+)([\+\-x\/])(\d+)', input_string)

		if match:
			num1 = int(match.group(1))
			operator = match.group(2)
			num2 = int(match.group(3))

			if operator == '+':
				result = num1 + num2
			elif operator == '-':
				result = num1 - num2
			elif operator == 'x':
				result = num1 * num2
			elif operator == '/':
				result = num1 / num2
			else:
				result = None

			print(f"Result of {num1} {operator} {num2} = {result}")
		else:
			print("Invalid CAPTCHA format.")
			driver.get('https://judgments.ecourts.gov.in') 
			result = None

		if result is not None:
			captcha_hit = driver.find_element(By.ID, "captcha")  # Updated to Selenium 4 format (captchapdf)
			captcha_hit.send_keys(int(result))

			driver.find_element(By.ID, "main_search").click() #<input type="button" href="" class="btn btn-success btn-sm col-auto" value="submit" onclick="get_pdf_dtls(9,&quot;undefined&quot;,&quot;2024_8_1_7&quot;,2024);">

			try:
				time.sleep(3)
				# Check for error messages related to CAPTCHA
				error_message = driver.find_element(By.CLASS_NAME, 'alert-danger-cust')
				# time.sleep(3)

				if error_message.is_displayed():
					print("Invalid captcha, refreshing the page...")
					driver.get('https://judgments.ecourts.gov.in')  # Refresh the page if there's an error
					continue
				else:
					print("Captcha entered successfully!")

					# Wait for the button to be clickable
				for j in range(3684):
					driver.execute_script("window.scrollTo(0, 0);")
					time.sleep(5)
					current_scroll = 0
					scroll_increment = 200  # Change this value to scroll by a different amount
					outer_iterations = 10 
					pdf_list=[]
					for i in range(10):

						try:
							try:
								# Wait for modal backdrops to disappear if present
								WebDriverWait(driver, 10).until(
									EC.invisibility_of_element((By.CSS_SELECTOR, '.modal-backdrop'))
								)
							except:
								pass

							# Wait for the button to be clickable
							button = WebDriverWait(driver, 10).until(
								EC.element_to_be_clickable((By.ID, f'link_{i}'))
							)
							button.click()  # Click the button
							time.sleep(2)
							try:
								# Try to find the captcha image element using XPATH
								captcha_element = driver.find_element(By.XPATH, "//img[@class='captcha_play_image' and @height='32' and @width='32' and @alt='Play CAPTCHA Audio']")

								# If the element is found, take a screenshot
								# if captcha_element:
								#     # timestamp = time.strftime("%Y%m%d-%H%M%S")  # Get a timestamp for the file name
								#     screenshot_name = "time_outscreenshot.png"
								#     driver.save_screenshot(screenshot_name)
								#     print(f"Screenshot saved as {screenshot_name}")
								#     # input("Press Enter after solving the CAPTCHA manually...")
								if captcha_element:

									valid_captcha = False

									while not valid_captcha:
										time.sleep(2)

										try:
											captcha_element = driver.find_element(By.ID, "captcha_image_pdf")  # Updated to Selenium 4 format (captcha_image_pdf)
											# print(captcha_element.get_attribute('outerHTML'))
											# Get the location and size of the CAPTCHA image
											locationn = captcha_element.location
											sizee = captcha_element.size
											# print(locationn)
											# print(sizee)
											locationn['y']=100
											# print(locationn)

											# Take a screenshot of the entire page
											screenshot_name = 'time_outscreenshot.png'
											driver.save_screenshot(screenshot_name)
											print(f'Screenshot saved as {screenshot_name}')
											time.sleep(2)

											# Load the screenshot image using PIL (Pillow)
											imagee = Image.open(screenshot_name)

											# Define the coordinates for cropping (left, top, right, bottom)
											left = locationn['x']
											top = locationn['y']
											right = left + sizee['width']
											bottom = top + sizee['height']

											# Crop the image to get only the CAPTCHA
											captcha_imagee = imagee.crop((left, top, right, bottom))
											captcha_image_path = 'cropped_captcha_pdf.png'
											captcha_imagee.save(captcha_image_path)

											print(f"CAPTCHA image cropped and saved as {captcha_image_path}")
											time.sleep(2)

											# Process the CAPTCHA image using OpenCV and Tesseract (same as before)
											image_path = 'cropped_captcha_pdf.png'
											img_cv = cv.imread(image_path, cv.IMREAD_GRAYSCALE)
											_, img_bin = cv.threshold(img_cv, 150, 255, cv.THRESH_BINARY_INV)
											kernel = np.ones((1, 1), np.uint8)
											img_lines_removed = cv.morphologyEx(img_bin, cv.MORPH_OPEN, kernel, iterations=2)
											img_blur = cv.medianBlur(img_lines_removed, 3)
											img_inverted = cv.bitwise_not(img_blur)
											processed_image_path = 'processed_image_no_cross_pdf.png'
											cv.imwrite(processed_image_path, img_inverted)

											img_pil = Image.fromarray(cv.bitwise_not(img_inverted))
											captcha_text = pytesseract.image_to_string(processed_image_path, config='--psm 6')

											# Process the extracted text to solve the CAPTCHA
											input_string = captcha_text.replace(' ', '').strip()
											match = re.match(r'(\d+)([\+\-x\/])(\d+)', input_string)

											if match:
												num1 = int(match.group(1))
												operator = match.group(2)
												num2 = int(match.group(3))

												if operator == '+':
													result = num1 + num2
												elif operator == '-':
													result = num1 - num2
												elif operator == 'x':
													result = num1 * num2
												elif operator == '/':
													result = num1 / num2
												else:
													result = None

												print(f"Result of {num1} {operator} {num2} = {result}")
											else:
												print("Invalid CAPTCHA format.")
												captcha_hit = driver.find_element(By.ID, "captchapdf")  # Updated to Selenium 4 format (captchapdf)
												captcha_hit.clear()
												captcha_hit.send_keys(1000)
												# submit_button = driver.find_element(By.XPATH, '//input[@value="submit" and @class="btn btn-success btn-sm col-auto"]')
												submit_button = driver.find_element(By.CSS_SELECTOR, 'input.btn.btn-success.btn-sm.col-auto[value="submit"]')
												# Click the button
												time.sleep(2)
												submit_button.click()
												time.sleep(3)
												try:
													# Switch to the alert
													alert = driver.switch_to.alert

													# Print the alert text (optional)
													print(alert.text)

													# Accept the alert (this simulates pressing "Enter")
													alert.accept()  # This clicks "OK" or "Enter" on the pop-up
													
													print("Alert accepted successfully.")
													continue

												except Exception as e:
													print(f"No alert found: {e}")
													break 

											if result is not None:
												captcha_hit = driver.find_element(By.ID, "captchapdf")  # Updated to Selenium 4 format (captchapdf)
												captcha_hit.clear()
												captcha_hit.send_keys(int(result))
												time.sleep(2)
												# submit_button = driver.find_element(By.XPATH, '//input[@value="submit" and @class="btn btn-success btn-sm col-auto"]')
												submit_button = driver.find_element(By.CSS_SELECTOR, 'input.btn.btn-success.btn-sm.col-auto[value="submit"]')
												# Click the button
												submit_button.click()
												time.sleep(3)
												# driver.find_element(By.ID, "main_search").click() #<input type="button" href="" class="btn btn-success btn-sm col-auto" value="submit" onclick="get_pdf_dtls(9,&quot;undefined&quot;,&quot;2024_8_1_7&quot;,2024);">
												# Using XPath to find the button based on its "value" attribute
												try:
													# Switch to the alert
													alert = driver.switch_to.alert

													# Print the alert text (optional)
													print(alert.text)

													# Accept the alert (this simulates pressing "Enter")
													alert.accept()  # This clicks "OK" or "Enter" on the pop-up
													
													print("Alert accepted successfully.")
													continue

												except Exception as e:
													print(f"No alert found: {e}")
													break 

												# try:
												#     time.sleep(3)
												#     # Check for error messages related to CAPTCHA
												#     error_message = driver.find_element(By.CLASS_NAME, 'alert-danger-cust')
												#     # time.sleep(3)

												#     if error_message.is_displayed():
												#         print("Invalid captcha, refreshing the page...")
												#         driver.get('https://judgments.ecourts.gov.in')  # Refresh the page if there's an error
												#         continue
												#     else:
										except:
											pass		#         print("Captcha entered successfully!")                                                                                                           

							except:
								pass
								
							time.sleep(3)
							# Check for captured requests by Selenium Wire for the PDF URL
							pdf_url = None
							
							for request in driver.requests:
								# print(request.url,'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
								if request.response and 'application/pdf' in request.response.headers.get('Content-Type', ''):
									pdf_url = request.url  # Get the URL of the PDF
									# print(pdf_url,'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
									# print()
									if pdf_url not in pdf_list:
										pdf_list.append(pdf_url)
									# print(f"PDF URL: {pdf_url}")
									# break  # Exit the loop after finding the PDF URL
									# print('*******************************************************')
									# print(pdf_list)

							if pdf_list is None:
								print("PDF URL not found.")
							else:
								selenium_cookies = driver.get_cookies()
								session = requests.Session()
								for cookie in selenium_cookies:
									session.cookies.set(cookie['name'], cookie['value'])
								response = session.get(pdf_list[-1])

								# print(response.content)
								print(response.status_code)
								if response.status_code == 200 and response.headers.get('Content-Type') == 'application/pdf':
									pdf_filename = os.path.join(save_folder, pdf_url.split("/")[-1])  # Get the filename from the URL
									with open(pdf_filename, 'wb') as f:
										f.write(response.content)
									print(f"Downloaded PDF: {pdf_filename}")
								else:
									print(f"Failed to download PDF. Status Code: {response.status_code}")
									html_filename = os.path.join(save_folder, 'error_page.html')
									with open(html_filename, 'wb') as f:
										f.write(response.content)
									print(f"Error page saved to {html_filename} for debugging.")
									# driver.execute_script("window.open(arguments[0], '_blank');", pdf_url)
									# driver.get(pdf_url)


								# Switch to the new tab (the last one)
								# driver.switch_to.window(driver.window_handles[-1])

								# Optionally wait for a moment to allow the PDF to load
								time.sleep(2)  # Wait for the PDF to load; adjust as needed




								try:
								# Wait for the modal close button to be clickable
									close_button = WebDriverWait(driver, 10).until(
										EC.element_to_be_clickable((By.ID, 'modal_close'))
									)
									close_button.click()  # Click the close button
									print("Modal closed successfully.")
									time.sleep(5)

									driver.execute_script(f"window.scrollTo(0, {current_scroll + scroll_increment});")
									current_scroll += scroll_increment  # Update the current scroll position
									print(f"Scrolled down to {current_scroll} pixels.")
									print(i,'*******')
									if i==9:
										time.sleep(1)                         
										print('clicking to next <<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
										print()
										driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		
										# Wait for new content to load
										time.sleep(2)

										# Check if the next button is present
										try:
											next_button = driver.find_element(By.CLASS_NAME, 'next')  # Adjust class name as needed
											if next_button.is_displayed():  # Check if it's visible
												print("Next button is visible and ready to click.")
												next_button.click()  # Click the next button
												print("Clicked the next button.")
												break  # Exit the loop after clicking
										except Exception:
											print("Next button not yet visible, scrolling again.")

									# current_scroll = 0
									# scroll_increment = 200  # Change this value to scroll by a different amount
									
									# # Scroll down after closing the modal
									# while True:
									#     # Scroll the page down
									#     driver.execute_script(f"window.scrollTo(0, {current_scroll + scroll_increment});")
									#     current_scroll += scroll_increment
										
									#     # Check if you are at the bottom of the page
									#     if current_scroll >= driver.execute_script("return document.body.scrollHeight"):
									#         print("Reached the bottom of the page.")
									#         break  # Exit the loop if you've reached the bottom

									#     # Wait for a short period to see the scrolling effect
									#     time.sleep(1)  # Adjust as needed for a smoother scroll effect
								except Exception as e:
									print(f"Error locating or clicking the close button: {e}")
								time.sleep(5)


							# You can download the PDF automatically using the Chrome options you set earlier
							# The PDF should start downloading automatically due to your options

							# Close the new tab if needed
							# driver.close()  # Close the PDF tab

							# Switch back to the original tab
							# driver.switch_to.window(driver.window_handles[0])
					
						except Exception as e:
							print(f"Error locating button or handling click: {e}")


			except Exception as e:
				print(f"Error checking for CAPTCHA or processing: {e}")
				next_button = WebDriverWait(driver, 10).until(
					EC.element_to_be_clickable((By.CLASS_NAME, 'next'))
				)
				next_button.click()




	except Exception as e:
		print(f"Error: {e}")
		# time.sleep(15)
		driver.quit()
		break
# time.sleep(14)
driver.quit()
