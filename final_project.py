import requests
import json
import sqlite3
from bs4 import BeautifulSoup
import plotly.plotly as py
from secrets import *

# published_date = 2016-05-19
## NEW YORK TIMES CACHING ##############################################################################
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


## GOOGLE BOOKS CACHING ##############################################################################
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


## NYT REQUESTS FUNCTION ##############################################################################
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

## GOOGLE BOOKS CLASS #########################################################################
class GoogleBook():
    def __init__(self, title, author, avg_rtng, num_reviews, description, publisher, published_year, isbn_13, length, subjects):
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


## GOOGLE BOOKS REQUESTS FUNCTION #######################################################################
def get_isbn_nums(published_date): #pub date
    with open(NYT_REQUESTS_CACHE, 'r') as f:
         data = json.load(f)
         results = data[get_nyt_data(published_date)] #put generic pub date later

         isbn_nums = []
         for item in results['results']['lists']:
             for book in item['books']:
                 isbn = (book['title'].lower(), book['author'], book['primary_isbn13'])
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

                            google_book = GoogleBook(title, author, avg_rtng, num_reviews, description, publisher, published_year, isbn[2], length, subjects)
                            google_books.append(google_book)

                        # print(second_crawl_div, isbn, book_url)
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


                        google_book = GoogleBook(title, author, avg_rtng, num_reviews, description, publisher, published_year, isbn[2], length, subjects)
                        google_books.append(google_book)
        except:
            baseurl = "https://www.google.com/search?tbm=bks&q="
            initial_page_text = make_request_using_cache(baseurl + isbn[0].replace(' ', '+') + '+' + isbn[1].replace(' ', '+'))
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

                            google_book = GoogleBook(title, author, avg_rtng, num_reviews, description, publisher, published_year, isbn[2], length, subjects)
                            google_books.append(google_book)

                        # print(second_crawl_div, isbn, book_url)
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


                        google_book = GoogleBook(title, author, avg_rtng, num_reviews, description, publisher, published_year, isbn[2], length, subjects)
                        google_books.append(google_book)

    return google_books


# google_books = scrape_google_books_data(2016-05-19)
# print(len(google_books)) # 99 vs. the 210 it should be LMAO KILL ME
# google_books = scrape_google_books_data()
# for item in google_books:
#     print(item.avg_rtng, item.num_reviews)

## DATABASE CREATION ##############################################################################
DBNAME = 'nyt_bestsellers.db'
try:
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
except Error as e:
    print(e)

def init_db(db_name):
    # try:
    #     statement = """
    #         SELECT COUNT(*) FROM 'New York Times Bestsellers'
    #     """
    #     cur.execute(statement)
    #     table_exists = True
    # except:
    #     table_exists = False

    # if table_exists == True:
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

    # if table_exists == False:
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
                        'PulicationYear' INTEGER,
                        'Length(Pages)' INTEGER,
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
        google_book_insertion = [google_book.title.lower(), google_book.author, google_book.avg_rtng, google_book.num_reviews, google_book.published_year, google_book.length, google_book.subjects, google_book.isbn_13]

        statement = 'INSERT INTO "GoogleBooksData" '
        statement += 'VALUES (NULL, NULL, ?, ?, ?, ?, ?, ?, ?, ?)'

        cur.execute(statement, google_book_insertion)
        conn.commit()


    conn.close()

def update_relations_google_books(): #the query works in sql but not when i run my program???
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

# published_date = input("Enter date(YYYY-MM-DD): ")
# get_nyt_data(published_date) #2016-05-19
# init_db(DBNAME)
# insert_nyt_data(published_date)

# if __name__ == "__main__":
#     published_date = input("Enter date(YYYY-MM-DD): ")
#     google_books = scrape_google_books_data(published_date)
#     for book in google_books:
#         print(book.author, book.isbn_13)
#     print(len(get_isbn_nums(published_date)))
#     print(len(google_books))

if __name__ == "__main__":
    #get date to use
    published_date = input("Enter date(YYYY-MM-DD): ")
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
