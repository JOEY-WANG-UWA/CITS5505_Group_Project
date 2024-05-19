import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

class FlaskAppTest(unittest.TestCase):

    def setUp(self):
        options = ChromeOptions()
        options.headless = True

        chromedriver_path = '/usr/local/bin/chromedriver'
        service = ChromeService(executable_path=chromedriver_path)
        
        self.driver = webdriver.Chrome(service=service, options=options)

    def test_register(self):
        driver = self.driver
        driver.get('http://localhost:5000/register')
        self.assertIn('Register', driver.title)

        username = driver.find_element(By.NAME, 'username')
        email = driver.find_element(By.NAME, 'email')
        password = driver.find_element(By.NAME, 'password')
        password2 = driver.find_element(By.NAME, 'password2')
        location = driver.find_element(By.NAME, 'location')

        username.send_keys('testuser')
        email.send_keys('testuser@example.com')
        password.send_keys('password')
        password2.send_keys('password')
        location.send_keys('au')
        location.send_keys(Keys.RETURN)

        # Add a wait to ensure the form submission is processed
        driver.implicitly_wait(10)

        # Print the page source for debugging
        print(driver.page_source)

        # Check if there are any error messages on the page
        error_elements = driver.find_elements(By.CLASS_NAME, 'form-error')
        for error in error_elements:
            print("Form error:", error.text)

        # Assert that we are on the login page or that 'Log In' is present
        self.assertIn('Log In', driver.page_source, "The 'Log In' text was not found in the page source after form submission.")

    def tearDown(self):
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()
