
This program uses data from the New York Times books API and scraped data from the Google Books platform to present information about the New York Times bestsellers lists via Plotly graphs. All data is stored and processed via a SQL database.

While uncommenting line 921 will allow users to recreate a database from scratch using a date of their choosing, all test cases for the program are based on the NYT bestsellers list published on 2016-05-19. This date was chosen half at random and half because NYT bestsellers lists prior to 2017 supply the requisite 100+ records, while the bestsellers lists published post 2017 only contain records for 80 books. 

Users will need a NYT API key to run the program. It is recommend that this key be stored in a 'secrets.py' file. 
This file should be included in a .gitignore, along with any other cache files produced that contain identifying information. The .gitignore for this program should look like this: 

	secrets.py
	__pycache__
	nyt_requests.json
	google_books.json

Visualizations for this program are handled through plotly. Information for getting started with plotly can be found here: https://plot.ly/python/getting-started/

All other necessary modules are listed in the requirements.txt file. 

The code is structured as follows: 

	1. Caching for both the NYT API and scraped Google Books html is established 

	2. The NYT requests funcion is defined, along with those functions needed to scrape from Google Books - including a Google Books class definition

	3. Functions are defined to create the database using data from both sources - the get_data_build_database() function combining everything up to now

	4. Data processing is handled in the process_command function

	5. Plotly outputs are constructed via the plotly_outputs function

	6. Everything is bundled together in the interactive_prompt function that allows for command line response from users

~~ User Guide ~~
- Uncommenting line 908 [get_data_build_database() in the interactive_prompt() function] before running final_project.py for the first time will build a new database. User will be prompted to enter the date for which they would like to collect NYT bestsellers list data. Once again, the date I used for the purposes of building this program and writing test cases is 2016-05-19, but any other date may be used. Line 921 may be commented back out after the first run of the program if desired to avoid recreating a new database each time the program is run.
- After database construction is completed, the user will be prompted to enter a command. A list of available commands can be entered by typing 'help'
- Users have a choice of two main commands with various options: 'All' or '<nyt_sub_list_name>'. 'All' will present information about all of the NYT bestsellers lists at once. Entering an <nyt_sub_list_name> - i.e. 'Hardcover Nonfiction', 'Humor', 'Business Books' - will present information about that particular sublist. The options for each main command include: ratings, genres, length, pub_year, and nyt_rankings. Ratings gives you the Google Books average score, genres gives you the sublist names or subgenres, length gives you page numbers, pub_year gives you publication info, and nyt_rankings gives you bestsellers rankings info. 
- Sample commands include (case sensitive): 
	* 'All length'
	* 'All nyt_rankings'
	* 'All pub_year'
	* 'Childrens Middle Grade Paperback length'
	* 'Science genres'
	* 'Humor ratings'
- Formatted data will print to the console first, with the option to see a plotly visualization prompted next. If 'y', a user will be redirected to the relevant plotly graph in the browser. If 'n', the program will proceed. Ratings are presented on a bar graph, genres on a pie chart, length on a line graph, pub_year on a scatter plot, and nyt_rankings on a scatterplot. 
- Users can access help.txt by entering 'help' at any time. 




