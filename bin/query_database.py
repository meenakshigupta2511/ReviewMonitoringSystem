from database import Database
import argparse
from datetime import datetime, timedelta

def print_table_format(headers, rows):
    """Print data in a nicely formatted table"""
    if not rows:
        print("No results found.")
        return

    # Calculate column widths
    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]
    
    # Create format string
    row_format = " | ".join(f"{{:{width}}}" for width in widths)
    separator = "-" * (sum(widths) + len(widths) * 3)
    
    # Print headers
    print(separator)
    print(row_format.format(*headers))
    print(separator)
    
    # Print rows
    for row in rows:
        print(row_format.format(*[str(item) for item in row]))
    print(separator)
    print()

def get_recent_reviews(db, days=7):
    """Get reviews from the last N days"""
    with db.conn() as conn:
        cursor = conn.cursor()
        date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT 
                r.review_date,
                rev.name as reviewer,
                p.name as product,
                r.rating,
                r.sentiment,
                r.confidence,
                substr(r.review_text, 1, 50) || '...' as review_preview
            FROM reviews r
            JOIN reviewers rev ON r.reviewer_id = rev.id
            JOIN products p ON r.product_id = p.id
            WHERE r.review_date >= ?
            ORDER BY r.review_date DESC
        ''', (date_limit,))
        rows = cursor.fetchall()
        
        headers = ['Date', 'Reviewer', 'Product', 'Rating', 'Sentiment', 'Confidence', 'Review Preview']
        print(f"\nRecent reviews (last {days} days):")
        print_table_format(headers, rows)

def get_product_analysis(db, product_name):
    """Get detailed analysis for a specific product"""
    with db.conn() as conn:
        cursor = conn.cursor()
        
        # Get summary statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_reviews,
                ROUND(AVG(rating), 2) as avg_rating,
                ROUND(AVG(confidence), 2) as avg_confidence,
                SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) as neutral_count
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            WHERE p.name = ?
        ''', (product_name,))
        stats = cursor.fetchone()
        
        if not stats or stats[0] == 0:
            print(f"No reviews found for product: {product_name}")
            return
        
        print(f"\nProduct Analysis for: {product_name}")
        print("=" * 50)
        print(f"Total Reviews: {stats[0]}")
        print(f"Average Rating: {stats[1]}/5")
        print(f"Average Confidence: {stats[2]}%")
        print("\nSentiment Distribution:")
        print(f"Positive: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
        print(f"Negative: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
        print(f"Neutral:  {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")
        
        # Get recent reviews
        cursor.execute('''
            SELECT 
                r.review_date,
                rev.name as reviewer,
                r.rating,
                r.sentiment,
                substr(r.review_text, 1, 50) || '...' as review_preview
            FROM reviews r
            JOIN reviewers rev ON r.reviewer_id = rev.id
            JOIN products p ON r.product_id = p.id
            WHERE p.name = ?
            ORDER BY r.review_date DESC
            LIMIT 5
        ''', (product_name,))
        rows = cursor.fetchall()
        
        print("\nMost Recent Reviews:")
        headers = ['Date', 'Reviewer', 'Rating', 'Sentiment', 'Review Preview']
        print_table_format(headers, rows)

def get_reviewer_history(db, reviewer_name):
    """Get review history for a specific reviewer"""
    with db.conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                r.review_date,
                p.name as product,
                r.rating,
                r.sentiment,
                r.confidence,
                substr(r.review_text, 1, 50) || '...' as review_preview
            FROM reviews r
            JOIN reviewers rev ON r.reviewer_id = rev.id
            JOIN products p ON r.product_id = p.id
            WHERE rev.name = ?
            ORDER BY r.review_date DESC
        ''', (reviewer_name,))
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No reviews found for reviewer: {reviewer_name}")
            return
            
        print(f"\nReview history for: {reviewer_name}")
        headers = ['Date', 'Product', 'Rating', 'Sentiment', 'Confidence', 'Review Preview']
        print_table_format(headers, rows)

def get_sentiment_trends(db, days=30):
    """Get sentiment trends over time"""
    with db.conn() as conn:
        cursor = conn.cursor()
        date_limit = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT 
                date(r.review_date) as review_date,
                COUNT(*) as total_reviews,
                ROUND(AVG(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) * 100, 1) as positive_percentage,
                ROUND(AVG(rating), 2) as avg_rating
            FROM reviews r
            WHERE r.review_date >= ?
            GROUP BY date(r.review_date)
            ORDER BY review_date DESC
        ''', (date_limit,))
        rows = cursor.fetchall()
        
        print(f"\nSentiment trends (last {days} days):")
        headers = ['Date', 'Total Reviews', 'Positive %', 'Avg Rating']
        print_table_format(headers, rows)

def main():
    parser = argparse.ArgumentParser(description='Query the Review Monitoring System Database')
    parser.add_argument('--recent', type=int, metavar='DAYS', 
                       help='Show recent reviews from the last N days')
    parser.add_argument('--product', type=str, metavar='NAME',
                       help='Show analysis for a specific product')
    parser.add_argument('--reviewer', type=str, metavar='NAME',
                       help='Show review history for a specific reviewer')
    parser.add_argument('--trends', type=int, metavar='DAYS',
                       help='Show sentiment trends over the last N days')
    
    args = parser.parse_args()
    db = Database()
    
    if len(sys.argv) == 1:
        # No arguments provided, show help
        parser.print_help()
        return

    if args.recent:
        get_recent_reviews(db, args.recent)
    
    if args.product:
        get_product_analysis(db, args.product)
    
    if args.reviewer:
        get_reviewer_history(db, args.reviewer)
    
    if args.trends:
        get_sentiment_trends(db, args.trends)

if __name__ == "__main__":
    import sys
    main()
