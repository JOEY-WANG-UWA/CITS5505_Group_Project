# Orange Book Web Application

## Description
The Orange Book web application is a platform designed to capture and share the positive energy and beautiful lives of the youth in this era. Users can create an account and log in to share their experiences through text and image posts. The application also allows users to update profiles, follow or unfollow other users, search and more. It aims to foster a supportive and inspiring community where young people can connect and celebrate their achievements and everyday moments.

## Group Members
| UWA ID     | Name            | GitHub Username  |
|------------|-----------------|------------------|
| 23853193   | Lingzi Huangfu  | LizzzzHFFF       |
| 23806063   | Yuxiao Shi      | Rita2023         |
| 23956788   | Zihan Zhang     | Zihan-Zhang810   |
| 23191783   | Jiandong Wang   | JOEY-WANG-UWA    |

## Instructions for Launching the Application
To launch the application, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/JOEY-WANG-UWA/CITS5505_Group_Project.git
    cd CITS5505_Group_Project
    ```

2. **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required dependencies**:
    ```bash
    cd microblog
    pip install -r requirements1.txt
    ```

4. **Run the application**:
    ```bash
    cd app
    flask run
    ```

The application will be accessible at `http://localhost:5000`.

## Instructions for Running the Tests
To run the tests for the application, follow these steps:

1. **Ensure the virtual environment is activated**:
    ```bash
    source venv/bin/activate
    ```
2. **Run the tests using pytest**:
    ```bash
    python -m unittest unit.py
    python -m unittest selenium_test.py
    ```
### Test account:
- **Username:** `susan`
- **password:** `susan`
    
