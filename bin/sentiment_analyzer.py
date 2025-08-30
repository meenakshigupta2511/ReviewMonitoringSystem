import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
import csv
import sys
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any
from database import Database

@dataclass
class Review:
    review_text: str
    reviewer_name: str
    product_name: str
    date: str
    rating: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        return cls(
            review_text=data.get('review_text', ''),
            reviewer_name=data.get('reviewer_name', ''),
            product_name=data.get('product_name', ''),
            date=data.get('date', ''),
            rating=float(data.get('rating', 0))
        )

# Download required NLTK data
try:
    nltk.download('vader_lexicon')
    nltk.download('punkt')
except:
    print("Note: NLTK downloads failed. If this is the first run, please ensure you have internet connection.")

def clean_text(text):
    # Remove special characters and extra whitespace
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def get_detailed_sentiment(review):
    # Initialize analyzers
    sia = SentimentIntensityAnalyzer()
    
    # Clean the text
    cleaned_review = clean_text(review)
    
    # Get VADER sentiment scores
    vader_scores = sia.polarity_scores(review)  # Use original review for VADER
    
    # Get TextBlob sentiment
    blob = TextBlob(cleaned_review)
    textblob_polarity = blob.sentiment.polarity
    textblob_subjectivity = blob.sentiment.subjectivity
    
    # Combine both analyses
    compound_score = vader_scores['compound']
    
    # Calculate weighted sentiment score (giving more weight to VADER)
    weighted_score = (compound_score * 0.7) + (textblob_polarity * 0.3)
    
    # Determine sentiment with confidence levels
    if abs(weighted_score) < 0.1:
        sentiment = "Neutral"
        confidence = abs(weighted_score) * 5  # Scale up for better readability
    else:
        if weighted_score > 0:
            sentiment = "Positive"
        else:
            sentiment = "Negative"
        confidence = min(abs(weighted_score) * 100, 100)  # Convert to percentage
    
    return {
        'sentiment': sentiment,
        'confidence': round(confidence, 2),
        'details': {
            'vader_compound': round(compound_score, 3),
            'textblob_polarity': round(textblob_polarity, 3),
            'subjectivity': round(textblob_subjectivity, 3)
        }
    }

def process_reviews(reviews):
    if isinstance(reviews, str):
        # Single review
        result = get_detailed_sentiment(reviews)
        print(f"\nReview: {reviews}")
        print(f"Sentiment: {result['sentiment']} (Confidence: {result['confidence']}%)")
        print("Detailed Scores:")
        print(f"- VADER Compound Score: {result['details']['vader_compound']}")
        print(f"- TextBlob Polarity: {result['details']['textblob_polarity']}")
        print(f"- Subjectivity: {result['details']['subjectivity']}")
        print("-" * 50)
    elif isinstance(reviews, list):
        # List of reviews
        for i, review in enumerate(reviews, 1):
            result = get_detailed_sentiment(review)
            print(f"\nReview #{i}: {review}")
            print(f"Sentiment: {result['sentiment']} (Confidence: {result['confidence']}%)")
            print("Detailed Scores:")
            print(f"- VADER Compound Score: {result['details']['vader_compound']}")
            print(f"- TextBlob Polarity: {result['details']['textblob_polarity']}")
            print(f"- Subjectivity: {result['details']['subjectivity']}")
            print("-" * 50)

def validate_date(date_str: str) -> str:
    """Validate and format date string"""
    try:
        # Try to parse the date (accepts various formats)
        parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try another common format
            parsed_date = datetime.strptime(date_str.strip(), "%m/%d/%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            return date_str  # Return as-is if parsing fails

def validate_rating(rating_str: str) -> float:
    """Validate and convert rating to float (1-5 scale)"""
    try:
        rating = float(rating_str)
        return max(1.0, min(5.0, rating))  # Clamp between 1 and 5
    except ValueError:
        return 0.0  # Default rating if invalid

def read_reviews_from_file(file_path):
    """
    Read reviews from a CSV file with specified fields:
    - Review Text
    - Reviewer Name
    - Product Name
    - Date
    - Rating
    """
    reviews = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Verify required fields
            required_fields = {'review_text', 'reviewer_name', 'product_name', 'date', 'rating'}
            missing_fields = required_fields - set(csv_reader.fieldnames)
            
            if missing_fields:
                print(f"Error: Missing required fields: {missing_fields}")
                print("Required CSV headers: review_text, reviewer_name, product_name, date, rating")
                return []
            
            for row in csv_reader:
                # Validate and clean data
                cleaned_row = {
                    'review_text': row['review_text'].strip(),
                    'reviewer_name': row['reviewer_name'].strip(),
                    'product_name': row['product_name'].strip(),
                    'date': validate_date(row['date']),
                    'rating': validate_rating(row['rating'])
                }
                
                if cleaned_row['review_text']:  # Only add if review text is not empty
                    reviews.append(Review.from_dict(cleaned_row))
        
        return reviews
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return []

def save_analysis_results(reviews_with_sentiment, output_file=None):
    """
    Save the analysis results to both database and optionally to a CSV file
    """
    # Initialize database
    db = Database()
    
    try:
        # Save to database
        for review_obj, analysis in reviews_with_sentiment:
            # Calculate sentiment-rating agreement
            sentiment_score = analysis['details']['vader_compound']
            normalized_rating = (review_obj.rating - 1) / 4  # Convert 1-5 scale to 0-1
            rating_sentiment = (normalized_rating * 2) - 1  # Convert to -1 to 1 scale
            agreement = "Yes" if (sentiment_score >= 0 and rating_sentiment >= 0) or \
                              (sentiment_score < 0 and rating_sentiment < 0) else "No"
            
            # Prepare review data for database
            review_data = {
                'review_text': review_obj.review_text,
                'reviewer_name': review_obj.reviewer_name,
                'product_name': review_obj.product_name,
                'date': review_obj.date,
                'rating': review_obj.rating,
                'sentiment': analysis['sentiment'],
                'confidence': analysis['confidence'],
                'vader_score': analysis['details']['vader_compound'],
                'textblob_polarity': analysis['details']['textblob_polarity'],
                'subjectivity': analysis['details']['subjectivity'],
                'sentiment_rating_agreement': agreement
            }
            
            # Save to database
            db.save_review(review_data)
        
        print("\nAnalysis results saved to database successfully!")
        
        # Optionally save to CSV file
        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow([
                    'Review Text', 'Reviewer Name', 'Product Name', 'Date', 'Rating',
                    'Sentiment', 'Confidence', 'VADER_Score', 'TextBlob_Polarity', 
                    'Subjectivity', 'Sentiment vs Rating Agreement'
                ])
                
                # Write data
                for review_obj, analysis in reviews_with_sentiment:
                    # Calculate sentiment-rating agreement
                    sentiment_score = analysis['details']['vader_compound']
                    normalized_rating = (review_obj.rating - 1) / 4
                    rating_sentiment = (normalized_rating * 2) - 1
                    agreement = "Yes" if (sentiment_score >= 0 and rating_sentiment >= 0) or \
                                      (sentiment_score < 0 and rating_sentiment < 0) else "No"
                    
                    writer.writerow([
                        review_obj.review_text,
                        review_obj.reviewer_name,
                        review_obj.product_name,
                        review_obj.date,
                        review_obj.rating,
                        analysis['sentiment'],
                        f"{analysis['confidence']}%",
                        analysis['details']['vader_compound'],
                        analysis['details']['textblob_polarity'],
                        analysis['details']['subjectivity'],
                        agreement
                    ])
            print(f"Analysis results also saved to: {output_file}")
            
            # Print product summary
            product_names = {review_obj.product_name for review_obj, _ in reviews_with_sentiment}
            for product_name in product_names:
                summary = db.get_product_sentiment_summary(product_name)
                if summary:
                    print(f"\nProduct Summary for {product_name}:")
                    print(f"Total Reviews: {summary[0]}")
                    print(f"Average Rating: {summary[1]:.2f}/5")
                    print(f"Sentiment Distribution:")
                    print(f"- Positive: {summary[2]}")
                    print(f"- Negative: {summary[3]}")
                    print(f"- Neutral: {summary[4]}")
                    print(f"Average Sentiment Score: {summary[5]:.3f}")
                    print(f"Average Confidence: {summary[6]:.2f}%")
    
    except Exception as e:
        print(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    print("Enhanced Sentiment Analyzer")
    print("=" * 50)
    
    # Command line arguments
    if len(sys.argv) > 1:
        # File mode
        input_file = sys.argv[1]
            
        print(f"\nReading reviews from: {input_file}")
        
        reviews = read_reviews_from_file(input_file)
        if reviews:
            print(f"\nFound {len(reviews)} reviews to analyze.")
            
            # Store results for saving to file
            results = []
            for review_obj in reviews:
                sentiment = get_detailed_sentiment(review_obj.review_text)
                results.append((review_obj, sentiment))
                
                # Print analysis
                print("\nReview Details:")
                print(f"Text: {review_obj.review_text}")
                print(f"Reviewer: {review_obj.reviewer_name}")
                print(f"Product: {review_obj.product_name}")
                print(f"Date: {review_obj.date}")
                print(f"Rating: {review_obj.rating}/5")
                print(f"Sentiment: {sentiment['sentiment']} (Confidence: {sentiment['confidence']}%)")
                print("Detailed Scores:")
                print(f"- VADER Compound Score: {sentiment['details']['vader_compound']}")
                print(f"- TextBlob Polarity: {sentiment['details']['textblob_polarity']}")
                print(f"- Subjectivity: {sentiment['details']['subjectivity']}")
                print("-" * 50)
            
            # Prepare output file path
            output_filename = os.path.basename(input_file)
            output_base = os.path.splitext(output_filename)[0]
            output_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", f"{output_base}_analysis.csv")
            
            # Save results to database and optionally to file
            save_analysis_results(results, output_file)
    
    else:
        # Interactive mode
        print("\nNo input file provided. Running in interactive mode.")
        print("Example reviews:")
        sample_reviews = [
            "This product is absolutely amazing! I couldn't be happier with my purchase.",
            "The quality is okay, but the price is a bit high for what you get.",
            "While there are some minor issues, overall I'm satisfied with the service.",
            "Unfortunately, this was a complete waste of money. Very disappointing.",
            "The product has both good and bad aspects, but it serves its purpose.",
        ]
        
        process_reviews(sample_reviews)
        
        print("\nEnter your own reviews for analysis (press Ctrl+C to exit)")
        try:
            while True:
                user_review = input("\nEnter a review: ").strip()
                if user_review:
                    process_reviews(user_review)
        except KeyboardInterrupt:
            print("\n\nThank you for using the Enhanced Sentiment Analyzer!")
