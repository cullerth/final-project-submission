import requests
import json
import sqlite3
from bs4 import BeautifulSoup
import plotly.plotly as py
from secrets import *
import plotly.plotly as py
import plotly.graph_objs as go

# published_date = 2016-05-19
## NEW YORK TIMES CACHING ######################################################
NYT_REQUESTS_CACHE = 'nyt_requests.json'
try:
    requests_cache = open(NYT_REQUESTS_CACHE, 'r')
    requests_cache_contents = requests_cache.read()
    NYT_CACHE_DICTION = json.loads(requests_cache_contents)
    requests_cache.close()
except:
    NYT_CACHE_DICTION = {}

def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)


## GOOGLE BOOKS CACHING ########################################################
GOOGLE_BOOKS_CACHE = 'google_books.json'
try:
    google_cache = open(GOOGLE_BOOKS_CACHE, 'r')
    google_cache_contents = google_cache.read()
    GOOGLE_CACHE_DICT = json.loads(google_cache_contents)
    google_cache.close()
except:
    GOOGLE_CACHE_DICT = {}

def get_unique_key(url):
  return url

def make_request_using_cache(url):
    unique_ident = get_unique_key(url)

    if unique_ident in GOOGLE_CACHE_DICT:
        print("Getting cached data...")
        return GOOGLE_CACHE_DICT[unique_ident]
    else:
        print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        GOOGLE_CACHE_DICT[unique_ident] = resp.text
        dumped_json_cache = json.dumps(GOOGLE_CACHE_DICT)
        fw = open(GOOGLE_BOOKS_CACHE,"w")
        fw.write(dumped_json_cache)
        fw.close() # Close the open file
        return GOOGLE_CACHE_DICT[unique_ident]


## NYT REQUESTS FUNCTION #######################################################
def get_nyt_data(published_date):
    baseurl = "https://api.nytimes.com/svc/books/v3/lists/overview.json"
    params_diction = {}
    params_diction["api_key"] = NYT_KEY
    params_diction["published_date"] = published_date
    unique_ident = params_unique_combination(baseurl,params_diction)
    if unique_ident in NYT_CACHE_DICTION:
        print("Getting cached data...")
        return unique_ident
    else:
        print("Making a request for new data...")
        resp = requests.get(baseurl, params_diction)
        #print(resp.status_code)
        NYT_CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(NYT_CACHE_DICTION)
        fw = open(NYT_REQUESTS_CACHE,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return unique_ident

## GOOGLE BOOKS CLASS ##########################################################
class GoogleBook():
    def __init__(self, title, author, avg_rtng, num_reviews, description,
    publisher, published_year, isbn_13, length, subjects):
        self.title = title
        self.author = author
        self.avg_rtng = avg_rtng
        self.num_reviews = num_reviews
        self.description = description
        self.publisher = publisher
        self.published_year = published_year
        self.isbn_13 = isbn_13
        self.length = length
        self.subjects = subjects

    def __str__(self):
        return self.title +  ' by ' + self.author + ' - Synopsis: ' + self.description


## GOOGLE BOOKS REQUESTS FUNCTION ##############################################
def get_isbn_nums(published_date): #pub date
    with open(NYT_REQUESTS_CACHE, 'r') as f:
         data = json.load(f)
         results = data[get_nyt_data(published_date)]

         isbn_nums = []
         for item in results['results']['lists']:
             for book in item['books']:
                 isbn = (book['title'].lower(), book['author'],
                 book['primary_isbn13'])
                 isbn_nums.append(isbn)

    return isbn_nums #[0:22] #for testing purposes

#element 23 doesnt work a tag

# isbn_nums = get_isbn_nums()
# print(len(isbn_nums)) #210

def scrape_google_books_data(published_date): #pub date
    google_books = []



    for isbn in get_isbn_nums(published_date):
        try:
            baseurl = "https://www.google.com/search?tbo=p&tbm=bks&q=isbn:"
            initial_page_text = make_request_using_cache(baseurl + isbn[2])
            first_page_soup = BeautifulSoup(initial_page_text, 'html.parser')
            first_crawl_div = first_page_soup.find(class_ = 'r')
            book_url_tag = first_crawl_div('a')
            if book_url_tag == None:
                print(isbn)
            else:
                for item in book_url_tag:
                    book_title = item.text.strip()
                    book_url = item['href']
                    second_pg_text = make_request_using_cache(book_url)
                    second_pg_soup = BeautifulSoup(second_pg_text, 'html.parser')
                    second_crawl_div = second_pg_soup.find(id = 'sidebar-atb-link')
                    if second_crawl_div != None:
                        for item in second_crawl_div:
                            about_book_url = second_crawl_div['href']
                            third_pg_txt = make_request_using_cache(about_book_url)
                            third_pg_soup = BeautifulSoup(third_pg_txt, 'html.parser')

                            avg_rtng_div = third_pg_soup.find(class_ = 'reviewaggregate hreview-aggregate')
                            avg_rtng_closer = avg_rtng_div.find(class_ = 'gb-star-on goog-inline-block rating')
                            if avg_rtng_closer != None:
                                avg_rtng = avg_rtng_closer.find(class_ = 'value-title')['title']
                                num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                                num_reviews = num_reviews_div.find(class_ = 'count').text.strip()
                            else:
                                avg_rtng = 0
                                num_reviews = 0

                            num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                            num_reviews = num_reviews_div.find(class_ = 'count').text.strip()

                            description_tag = third_pg_soup.find(id = 'synopsistext')
                            if description_tag != None:
                                description = description_tag.text.strip()
                            else:
                                description = "Synopsis not provided."

                            metadata_table = third_pg_soup.find(id = 'metadata_content_table')
                            table_rows = metadata_table.find_all('tr')
                            for tr in table_rows:
                                table_cells = tr.find_all('td')
                                if table_cells[0].text.strip() == 'Title':
                                    title = table_cells[1].text.strip()

                                if table_cells[0].text.strip() == 'Author':
                                    author = table_cells[1].text.strip()
                                elif table_cells[0].text.strip() == 'Authors':
                                    author = table_cells[1].text.strip()

                                if table_cells[0].text.strip() == 'Publisher':
                                    publisher = table_cells[1].text.strip()[:-6]
                                    published_year = table_cells[1].text.strip()[-4:]
                                if table_cells[0].text.strip() == 'ISBN':
                                    isbn_13 = table_cells[1].text.strip()[-13:]
                                if table_cells[0].text.strip() == 'Length':
                                    length = table_cells[1].text.strip()[:-6]
                                if table_cells[0].text.strip() == 'Subjects':
                                    subjects = table_cells[1].text.strip()
                                    subjects = subjects.replace(' / ', ', ')
                                    subjects = subjects.replace('›', ',')

                            google_book = GoogleBook(title, author, avg_rtng,
                            num_reviews, description, publisher, published_year,
                            isbn[2], length, subjects)
                            google_books.append(google_book)

                    else:
                        avg_rtng_div = second_pg_soup.find(class_ = 'reviewaggregate hreview-aggregate')
                        avg_rtng_closer = avg_rtng_div.find(class_ = 'gb-star-on goog-inline-block rating')
                        if avg_rtng_closer != None:
                            avg_rtng = avg_rtng_closer.find(class_ = 'value-title')['title']
                            num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                            num_reviews = num_reviews_div.find(class_ = 'count').text.strip()
                        else:
                            avg_rtng = 0
                            num_reviews = 0

                        description_tag = third_pg_soup.find(id = 'synopsistext')
                        if description_tag != None:
                            description = description_tag.text.strip()
                        else:
                            description = "Synopsis not provided."

                        metadata_table = second_pg_soup.find(id = 'metadata_content_table')
                        table_rows = metadata_table.find_all('tr')
                        for tr in table_rows:
                            table_cells = tr.find_all('td')
                            if table_cells[0].text.strip() == 'Title':
                                title = table_cells[1].text.strip()

                            if table_cells[0].text.strip() == 'Author':
                                author = table_cells[1].text.strip()
                            elif table_cells[0].text.strip() == 'Authors':
                                author = table_cells[1].text.strip()

                            if table_cells[0].text.strip() == 'Publisher':
                                publisher = table_cells[1].text.strip()[:-6]
                                published_year = table_cells[1].text.strip()[-4:]
                            if table_cells[0].text.strip() == 'ISBN':
                                isbn_13 = table_cells[1].text.strip()[-13:]
                            if table_cells[0].text.strip() == 'Length':
                                length = table_cells[1].text.strip()[:-6]
                            if table_cells[0].text.strip() == 'Subjects':
                                subjects = table_cells[1].text.strip()
                                subjects = subjects.replace(' / ', ', ')
                                subjects = subjects.replace('›', ',')


                        google_book = GoogleBook(title, author, avg_rtng,
                        num_reviews, description, publisher, published_year,
                        isbn[2], length, subjects)
                        google_books.append(google_book)
        except:
            baseurl = "https://www.google.com/search?tbm=bks&q="
            initial_page_text = make_request_using_cache(baseurl +
            isbn[0].replace(' ', '+') + '+' + isbn[1].replace(' ', '+'))
            first_page_soup = BeautifulSoup(initial_page_text, 'html.parser')
            first_crawl_div = first_page_soup.find(class_ = 'r')
            book_url_tag = first_crawl_div('a')
            if book_url_tag == None:
                print(isbn)
            else:
                for item in book_url_tag:
                    book_title = item.text.strip()
                    book_url = item['href']
                    second_pg_text = make_request_using_cache(book_url)
                    second_pg_soup = BeautifulSoup(second_pg_text, 'html.parser')
                    second_crawl_div = second_pg_soup.find(id = 'sidebar-atb-link')
                    if second_crawl_div != None:
                        for item in second_crawl_div:
                            about_book_url = second_crawl_div['href']
                            third_pg_txt = make_request_using_cache(about_book_url)
                            third_pg_soup = BeautifulSoup(third_pg_txt, 'html.parser')

                            avg_rtng_div = third_pg_soup.find(class_ = 'reviewaggregate hreview-aggregate')
                            avg_rtng_closer = avg_rtng_div.find(class_ = 'gb-star-on goog-inline-block rating')
                            if avg_rtng_closer != None:
                                avg_rtng = avg_rtng_closer.find(class_ = 'value-title')['title']
                                num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                                num_reviews = num_reviews_div.find(class_ = 'count').text.strip()
                            else:
                                avg_rtng = 0
                                num_reviews = 0

                            num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                            num_reviews = num_reviews_div.find(class_ = 'count').text.strip()

                            description_tag = third_pg_soup.find(id = 'synopsistext')
                            if description_tag != None:
                                description = description_tag.text.strip()
                            else:
                                description = "Synopsis not provided."

                            metadata_table = third_pg_soup.find(id = 'metadata_content_table')
                            table_rows = metadata_table.find_all('tr')
                            for tr in table_rows:
                                table_cells = tr.find_all('td')
                                if table_cells[0].text.strip() == 'Title':
                                    title = table_cells[1].text.strip()

                                if table_cells[0].text.strip() == 'Author':
                                    author = table_cells[1].text.strip()
                                elif table_cells[0].text.strip() == 'Authors':
                                    author = table_cells[1].text.strip()

                                if table_cells[0].text.strip() == 'Publisher':
                                    publisher = table_cells[1].text.strip()[:-6]
                                    published_year = table_cells[1].text.strip()[-4:]
                                if table_cells[0].text.strip() == 'ISBN':
                                    isbn_13 = table_cells[1].text.strip()[-13:]
                                if table_cells[0].text.strip() == 'Length':
                                    length = table_cells[1].text.strip()[:-6]
                                if table_cells[0].text.strip() == 'Subjects':
                                    subjects = table_cells[1].text.strip()
                                    subjects = subjects.replace(' / ', ', ')
                                    subjects = subjects.replace('›', ',')

                            google_book = GoogleBook(title, author, avg_rtng,
                            num_reviews, description, publisher, published_year,
                            isbn[2], length, subjects)
                            google_books.append(google_book)

                    else:
                        avg_rtng_div = second_pg_soup.find(class_ = 'reviewaggregate hreview-aggregate')
                        avg_rtng_closer = avg_rtng_div.find(class_ = 'gb-star-on goog-inline-block rating')
                        if avg_rtng_closer != None:
                            avg_rtng = avg_rtng_closer.find(class_ = 'value-title')['title']
                            num_reviews_div = avg_rtng_div.find(class_ = 'num-ratings')
                            num_reviews = num_reviews_div.find(class_ = 'count').text.strip()
                        else:
                            avg_rtng = 0
                            num_reviews = 0

                        description_tag = third_pg_soup.find(id = 'synopsistext')
                        if description_tag != None:
                            description = description_tag.text.strip()
                        else:
                            description = "Synopsis not provided."

                        metadata_table = second_pg_soup.find(id = 'metadata_content_table')
                        table_rows = metadata_table.find_all('tr')
                        for tr in table_rows:
                            table_cells = tr.find_all('td')
                            if table_cells[0].text.strip() == 'Title':
                                title = table_cells[1].text.strip()

                            if table_cells[0].text.strip() == 'Author':
                                author = table_cells[1].text.strip()
                            elif table_cells[0].text.strip() == 'Authors':
                                author = table_cells[1].text.strip()

                            if table_cells[0].text.strip() == 'Publisher':
                                publisher = table_cells[1].text.strip()[:-6]
                                published_year = table_cells[1].text.strip()[-4:]
                            if table_cells[0].text.strip() == 'ISBN':
                                isbn_13 = table_cells[1].text.strip()[-13:]
                            if table_cells[0].text.strip() == 'Length':
                                length = table_cells[1].text.strip()[:-6]
                            if table_cells[0].text.strip() == 'Subjects':
                                subjects = table_cells[1].text.strip()
                                subjects = subjects.replace(' / ', ', ')
                                subjects = subjects.replace('›', ',')


                        google_book = GoogleBook(title, author, avg_rtng,
                        num_reviews, description, publisher, published_year,
                        isbn[2], length, subjects)
                        google_books.append(google_book)

    return google_books

## DATABASE CREATION ###########################################################
DBNAME = 'nyt_bestsellers.db'
try:
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
except Error as e:
    print(e)

def init_db(db_name):
    statement = """
        DROP TABLE IF EXISTS 'NewYorkTimesBestsellers'
    """
    cur.execute(statement)
    conn.commit()

    statement = """
        DROP TABLE IF EXISTS 'GoogleBooksData'
    """
    cur.execute(statement)
    conn.commit()

    create_nyt_table = """
                CREATE TABLE 'NewYorkTimesBestsellers' (
                    'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                    'BestSellersDate' TEXT,
                    'PublishedDate' TEXT,
                    'ListName' TEXT,
                    'Title' TEXT,
                    'Author' TEXT,
                    'ISBN_13' TEXT,
                    'Publisher' TEXT,
                    'Rank' INTEGER,
                    'RankLastWeek' INTEGER,
                    'WeeksOnList' INTEGER,
                    'BookReviewLink' TEXT
                );
            """

    create_google_books_table = """
                    CREATE TABLE 'GoogleBooksData' (
                        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                        'BookId' INTEGER,
                        'BookTitle' TEXT,
                        'BookAuthor' TEXT,
                        'AverageRating' REAL,
                        'NumberOfReviews' INTEGER,
                        'PublicationYear' INTEGER,
                        'BookLength' INTEGER,
                        'Subjects' TEXT,
                        'ISBN_13' TEXT
                    );
                """
    cur.execute(create_nyt_table)
    cur.execute(create_google_books_table)
    conn.commit()

def insert_nyt_data(published_date):
    with open(NYT_REQUESTS_CACHE, 'r') as f:
         data = json.load(f)
         results = data[get_nyt_data(published_date)]

         conn = sqlite3.connect(DBNAME)
         cur = conn.cursor()

         bestsellers_date = results['results']['bestsellers_date']
         published_date = results['results']['published_date']
         for item in results['results']['lists']:
             list_name = item['list_name']
             for book in item['books']:
                 book_insertion = [bestsellers_date, published_date, list_name, book['title'].lower(), book['author'], book['primary_isbn13'], book['publisher'], book['rank'],  book['rank_last_week'], book['weeks_on_list'], book['book_review_link']]

                 statement = 'INSERT INTO "NewYorkTimesBestsellers" '
                 statement += 'VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'

                 cur.execute(statement, book_insertion)
                 conn.commit()

         conn.close()

def insert_google_books_data(published_date):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    books_list = scrape_google_books_data(published_date)
    for google_book in books_list:
        google_book_insertion = [google_book.title, google_book.author, google_book.avg_rtng, google_book.num_reviews, google_book.published_year, google_book.length, google_book.subjects, google_book.isbn_13]

        statement = 'INSERT INTO "GoogleBooksData" '
        statement += 'VALUES (NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?)'

        cur.execute(statement, google_book_insertion)
        conn.commit()


    conn.close()

def update_relations_google_books():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    update_google_books_statement = """
    UPDATE GoogleBooksData
    SET BookId = (
          SELECT Id
          FROM NewYorkTimesBestsellers
          WHERE NewYorkTimesBestsellers.ISBN_13 = GoogleBooksData.ISBN_13
    ) """

    cur.execute(update_google_books_statement)
    conn.commit()
    conn.close()

def get_data_build_database():
    #get date to use
    published_date = input("Enter date(YYYY-MM-DD): ") #2016-05-19 #2018-03-11
    #make nyt_times request for date
    get_nyt_data(published_date)
    #create database and table
    init_db(DBNAME)
    #insert nyt data into table
    insert_nyt_data(published_date)
    #insert google books data into table
    insert_google_books_data(published_date)
    #update google books table with relations
    update_relations_google_books()

# get_data_build_database()

## Data Processing #############################################################
def process_command(command):
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except Error as e:
        print(e)

    list_options = ["Young Adult Paperback", "Young Adult Hardcover",
    "Young Adult E-Book", "Travel", "Trade Fiction Paperback", "Sports",
    "Series Books", "Science", "Religion Spirituality and Faith", "Relationships",
    "Race and Civil Rights", "Picture Books", "Paperback Nonfiction",
    "Paperback Graphic Books", "Mass Market Paperback", "Manga",
    "Humor", "Health", "Hardcover Political Books", "Hardcover Nonfiction",
    "Hardcover Graphic Books", "Hardcover Fiction", "Games and Activities",
    "Food and Fitness", "Fashion Manners and Customs", "Family",
    "Expeditions Disasters and Adventures", "Espionage", "Education",
    "E-Book Nonfiction", "E-Book Fiction", "Culture", "Crime and Punishment",
    "Combined Print and E-Book Fiction", "Combined Print and E-Book Nonfiction",
    "Childrens Middle Grade Paperback", "Childrens Middle Grade Hardcover",
    "Childrens Middle Grade E-Book", "Celebrities", "Business Books", "Animals",
    "Advice How-To and Miscellaneous"]

    if 'ratings' in command:
        db_query = """
        SELECT ListName, BookTitle, BookAuthor, [Rank], AverageRating, NumberOfReviews
        FROM NewYorkTimesBestsellers AS NYT
        JOIN GoogleBooksData AS GBD
        ON NYT.Id=GBD.Id
        """
        if 'All' in command:
            db_query += "ORDER BY AverageRating DESC "
        else:
            for item in list_options:
                if item in command:
                    db_query += "WHERE ListName=" + "'" + item + "'" + " ORDER BY AverageRating DESC "
        # print(db_query)
        cur.execute(db_query)
        results = cur.fetchall()

    if 'genres' in command:
        db_query = """
        SELECT ListName, BookTitle, BookAuthor, Subjects
        FROM NewYorkTimesBestsellers AS NYT
        JOIN GoogleBooksData AS GBD
        ON NYT.Id=GBD.Id
        """
        if 'All' in command:
            db_query += "ORDER BY ListName "
        else:
            for item in list_options:
                if item in command:
                    db_query += "WHERE ListName=" + "'" + item + "'" + " ORDER BY ListName "
        # print(db_query)
        cur.execute(db_query)
        results = cur.fetchall()

    if 'length' in command:
        db_query = """
        SELECT ListName, BookTitle, BookAuthor, BookLength
        FROM NewYorkTimesBestsellers AS NYT
        JOIN GoogleBooksData AS GBD
        ON NYT.Id=GBD.Id
        """
        if 'All' in command:
            db_query += "ORDER BY BookLength ASC "
        else:
            for item in list_options:
                if item in command:
                    db_query += "WHERE ListName=" + "'" + item + "'" + " ORDER BY BookLength ASC "
        # print(db_query)
        cur.execute(db_query)
        results = cur.fetchall()

    if 'pub_year' in command:
        db_query = """
        SELECT ListName, BookTitle, BookAuthor, PublicationYear, Publisher, WeeksOnList
        FROM NewYorkTimesBestsellers AS NYT
        JOIN GoogleBooksData AS GBD
        ON NYT.Id=GBD.Id
        """
        if 'All' in command:
            db_query += "ORDER BY PublicationYear ASC "
        else:
            for item in list_options:
                if item in command:
                    db_query += "WHERE ListName=" + "'" + item + "'" + " ORDER BY PublicationYear ASC "
        # print(db_query)
        cur.execute(db_query)
        results = cur.fetchall()

    if 'nyt_ranking' in command:
        db_query = """
        SELECT ListName, BookTitle, BookAuthor, BestSellersDate, [Rank], RankLastWeek, WeeksOnList
        FROM NewYorkTimesBestsellers AS NYT
        JOIN GoogleBooksData AS GBD
        ON NYT.Id=GBD.Id
        """
        if 'All' in command:
            db_query += "ORDER BY [Rank] Desc "
        else:
            for item in list_options:
                if item in command:
                    db_query += "WHERE ListName=" + "'" + item + "'" + " ORDER BY [Rank] DESC "
        # print(db_query)
        cur.execute(db_query)
        results = cur.fetchall()

    return results

# process_command('All nyt_ranking')

def plotly_outputs(command):
    results = process_command(command)
    if 'ratings' in command:
        if 'All' in command:
            x_vals_book_title_author = []
            y_vals_google_books_rtng = []
            num_google_books_reviews_nyt_ranking = []

            for book in results:
                x_vals_book_title_author.append(book[1][:25] + '... by: ' + book[2])
                y_vals_google_books_rtng.append(book[4])
                num_google_books_reviews_nyt_ranking.append(book[1][:25] + '... by: ' + book[2] + '<br>' + 'Rating based on ' + str(book[5]) + ' reviews. NYT Bestsellers Ranking = ' + str(book[3]))

            trace0 = go.Bar(
                x= x_vals_book_title_author,
                y= y_vals_google_books_rtng,
                text = num_google_books_reviews_nyt_ranking,
                hoverinfo = 'text',
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.5,
                        )
                    ),
                    opacity=0.6
                )

            data = [trace0]
            layout = go.Layout(
                    title='Google Books Ratings. <br>Hover for Title, Author, # of Reviews & NYT Bestsellers Ranking',
                    xaxis=dict(
                        tickfont=dict(
                            size=14,
                            color='rgb(107, 107, 107)'
                        )
                    ),
                    yaxis=dict(
                        title='Rating',
                        titlefont=dict(
                            size=16,
                            color='rgb(107, 107, 107)'
                        ),
                        tickfont=dict(
                            size=14,
                            color='rgb(107, 107, 107)'
                        )
                    ),
                    legend=dict(
                        x=0,
                        y=1.0,
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    barmode='group',
                    bargap=0.15,
                    bargroupgap=0.1
            )

            fig = go.Figure(data=data, layout=layout)
            return py.plot(fig, filename='style-bar')

        else:
            x_vals_book_title_author = []
            y_vals_google_books_rtng = []
            num_google_books_reviews_nyt_ranking = []

            for book in results:
                x_vals_book_title_author.append(book[1][:25] + '... <br>by: ' + book[2])
                y_vals_google_books_rtng.append(book[4])
                num_google_books_reviews_nyt_ranking.append('Rating based on ' + str(book[5]) + ' reviews. NYT Bestsellers Ranking = ' + str(book[3]))

            trace0 = go.Bar(
                x= y_vals_google_books_rtng,
                y= x_vals_book_title_author,
                orientation = 'h',
                text = num_google_books_reviews_nyt_ranking,
                hoverinfo = 'text',
                marker=dict(
                    color='rgb(158,202,225)',
                    line=dict(
                        color='rgb(8,48,107)',
                        width=1.5,
                        )
                    ),
                    opacity=0.6
                )

            data = [trace0]
            layout = go.Layout(
                    title='Google Books Ratings. <br>Hover for # of Reviews <br>& NYT Bestsellers Ranking',
                    autosize=False,
                    width=500,
                    height=500,
                    margin=go.Margin(
                        l=200,
                        r=10,
                        b=100,
                        t=100,
                        pad=4
                        )
                    )

            fig = go.Figure(data=data, layout=layout)
            return py.plot(fig, filename='text-hover-bar')

    if 'genres' in command:
        if 'All' in command:
            list_name_labels_values = []
            list_name_values = []
            subject_name_labels = []
            subject_name_values = []

            for book in results:

                # list_name_labels_values.append()
# ListName, BookTitle, BookAuthor, Subjects
            # labels = ['Oxygen','Hydrogen','Carbon_Dioxide','Nitrogen']
            # values = [4500,2500,1053,500]
            #
            # trace = go.Pie(labels=labels, values=values)
            #
            # py.iplot([trace], filename='basic_pie_chart')
        else:
            pass

plotly_outputs('All ratings')

def load_help_text():
    pass

def interactive_prompt():
    pass

# if __name__ == "__main__":
#     interactive_prompt()
