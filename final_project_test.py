import unittest
from final_project import *

class TestDatabase(unittest.TestCase):

    def test_nyt_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT ListName FROM NewYorkTimesBestsellers'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn((('Hardcover Fiction',)), result_list)
        self.assertGreaterEqual(len(result_list), 80)

        sql = '''
            SELECT ListName, Title, Author, ISBN_13, [Rank]
            FROM NewYorkTimesBestsellers
            WHERE ListName='Combined Print and E-Book Nonfiction'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        #print(result_list)
        self.assertEqual(len(result_list), 5)
        self.assertEqual(len(result_list[0]), 5)

        conn.close()

    def test_googlebooks_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT BookTitle, BookAuthor
            FROM GoogleBooksData
            WHERE ISBN_13="9780812993547"
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Between the World and Me', 'Ta-Nehisi Coates'), result_list)
        self.assertEqual(len(result_list), 2)

        sql = '''
            SELECT AverageRating, NumberOfReviews
            FROM GoogleBooksData
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 210)

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT ListName, BookTitle, BookAuthor, NYT.ISBN_13, GBD.ISBN_13
            FROM NewYorkTimesBestsellers AS NYT
            JOIN GoogleBooksData AS GBD
            ON NYT.Id=GBD.Id
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(result_list[0][3], result_list[0][4])

        conn.close()

class TestAllSearch(unittest.TestCase):

    def test_all_search(self):
        results = process_command('All ratings')
        self.assertEqual(results[0][1], 'Grit: The Power of Passion and PerseveranceTCDC (Teaching and Curriculum Development Centre)')

        results = process_command('All genres')
        self.assertEqual(results[-1][0], 'Young Adult Paperback')

        results = process_command('All length')
        self.assertIn(('Humor', 'Yes Please', 'Amy Poehler', 352), results)

        results = process_command('All pub_year')
        self.assertIn(('Culture', 'The Bad-Ass Librarians of Timbuktu: And Their Race to Save the World’s Most Precious Manuscripts', 'Joshua Hammer', 2016, 'Simon & Schuster', 0), results)

        results = process_command('All nyt_ranking')
        self.assertEqual(len(results[15]), 7)

class TestListNameSearch(unittest.TestCase):

    def test_company_search(self):
        results = process_command('Business Books ratings')
        self.assertIn('Shoe Dog', results[1][1])

        results = process_command('Animals genres')
        self.assertIn('Nature', results[2][3])

        results = process_command('Religion Spirituality and Faith pub_year')
        self.assertIn(1997, results[0])

        results = process_command('Childrens Middle Grade Paperback nyt_rankings')
        self.assertEqual(len(results[4]), 7)


unittest.main()
