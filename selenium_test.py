import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

class FlaskAppTest(unittest.TestCase):

    def setUp(self):
        options = Options()
        options.headless = True

        geckodriver_path = '/usr/local/bin/geckodriver' 
        service = Service(geckodriver_path)
        
        self.driver = webdriver.Firefox(service=service, options=options)

    def test_register(self):
        driver = self.driver
        driver.get('http://localhost:5000/register')
        self.assertIn('Register', driver.title)

        username = driver.find_element("name", 'username')
        email = driver.find_element("name", 'email')
        password = driver.find_element("name", 'password')
        password2 = driver.find_element("name", 'password2')

        username.send_keys('testuser')
        email.send_keys('testuser@example.com')
        password.send_keys('password')
        password2.send_keys('password')
        password.send_keys(Keys.RETURN)

        self.assertIn('Log In', driver.page_source)

    def tearDown(self):
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()

