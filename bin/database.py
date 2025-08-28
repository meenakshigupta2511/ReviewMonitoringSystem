import sqlite3
from datetime import datetime
import os

from contextlib import contextmanager

class Database:
    def __init__(self):
        # Create database in the project's root directory
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.db_path = os.path.join(db_dir, "sentiment_analysis.db")
        self.create_tables()
    
    @contextmanager
    def conn(self):
        """Context manager for database connections"""
        connection = sqlite3.connect(self.db_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def create_tables(self):
        """Create the necessary database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            # Create reviewers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviewers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')

            # Create reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_text TEXT NOT NULL,
                    reviewer_id INTEGER,
                    product_id INTEGER,
                    rating FLOAT,
                    review_date DATE,
                    sentiment TEXT,
                    confidence FLOAT,
                    vader_score FLOAT,
                    textblob_polarity FLOAT,
                    subjectivity FLOAT,
                    sentiment_rating_agreement TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (reviewer_id) REFERENCES reviewers (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            conn.commit()

    def get_or_create_product(self, product_name):
        """Get product ID or create new product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO products (name) VALUES (?)', (product_name,))
            cursor.execute('SELECT id FROM products WHERE name = ?', (product_name,))
            return cursor.fetchone()[0]

    def get_or_create_reviewer(self, reviewer_name):
        """Get reviewer ID or create new reviewer"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO reviewers (name) VALUES (?)', (reviewer_name,))
            cursor.execute('SELECT id FROM reviewers WHERE name = ?', (reviewer_name,))
            return cursor.fetchone()[0]

    def save_review(self, review_data):
        """Save a review and its sentiment analysis to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create product and reviewer
            product_id = self.get_or_create_product(review_data['product_name'])
            reviewer_id = self.get_or_create_reviewer(review_data['reviewer_name'])

            # Insert review data
            cursor.execute('''
                INSERT INTO reviews (
                    review_text, reviewer_id, product_id, rating, review_date,
                    sentiment, confidence, vader_score, textblob_polarity,
                    subjectivity, sentiment_rating_agreement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                review_data['review_text'],
                reviewer_id,
                product_id,
                review_data['rating'],
                review_data['date'],
                review_data['sentiment'],
                review_data['confidence'],
                review_data['vader_score'],
                review_data['textblob_polarity'],
                review_data['subjectivity'],
                review_data['sentiment_rating_agreement']
            ))

            conn.commit()
            return cursor.lastrowid

    def get_reviews_by_product(self, product_name):
        """Get all reviews for a specific product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, rv.name as reviewer_name, p.name as product_name
                FROM reviews r
                JOIN reviewers rv ON r.reviewer_id = rv.id
                JOIN products p ON r.product_id = p.id
                WHERE p.name = ?
                ORDER BY r.review_date DESC
            ''', (product_name,))
            return cursor.fetchall()

    def get_product_sentiment_summary(self, product_name):
        """Get sentiment summary for a specific product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_reviews,
                    AVG(rating) as avg_rating,
                    SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) as neutral_count,
                    AVG(vader_score) as avg_vader_score,
                    AVG(confidence) as avg_confidence
                FROM reviews r
                JOIN products p ON r.product_id = p.id
                WHERE p.name = ?
            ''', (product_name,))
            return cursor.fetchone()
