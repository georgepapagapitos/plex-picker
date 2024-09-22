Here’s an improved version of your README for the Plex Picker project. It adds clarity, structure, and some additional information to help users understand and get started with the project more easily.

---

# Plex Picker

Plex Picker is a Django-based web application that helps users randomly select movies from their Plex library.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites
- Python 3.12 or later
- pip

### Steps

1. **Create a Virtual Environment**  
   This ensures your project dependencies are isolated.
   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment**  
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```
   On Windows:
   ```bash
   venv\Scripts\activate
   ```

3. **Install Requirements**  
   Install the necessary dependencies using pip.
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**  
   This command creates the local `db.sqlite3` database.
   ```bash
   python manage.py migrate
   ```

5. **Set Up Environment Variables**  
   Create a `.env` file from the example provided and add your secrets.
   ```bash
   cp .example.env .env
   ```

6. **Populate the Database**  
   Use the following command to sync your Plex "Movies" library and populate the database.
   ```bash
   python manage.py sync_movies
   ```

7. **Run the Development Server**  
   Start the server and navigate to [localhost:8000/picker/random-movie](http://localhost:8000/picker/random-movie) in your browser.
   ```bash
   python manage.py runserver
   ```

## Usage

Once the server is running, you can access the app via your browser. Explore the functionality by navigating to:
- [Random Movie Picker](http://localhost:8000/picker/random-movie)

## Configuration

Make sure to customize your `.env` file with the required secrets such as your Plex token and any other necessary configurations.

## Contributing

Contributions are welcome! If you have suggestions or improvements, please fork the repository and create a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Feel free to adjust any sections to better fit your project's specific details or preferences!