from prefect import flow, task
from datetime import datetime, timedelta
import os
from bin.data_generator import ReviewDataGenerator
from bin.sentiment_analyzer import read_reviews_from_file, get_detailed_sentiment, save_analysis_results

@task
def generate_reviews():
    generator = ReviewDataGenerator()
    start_date = datetime.now() - timedelta(days=1)
    reviews = generator.generate_dataset(20, start_date)
    
    output_file = os.path.join("input", "daily_reviews.csv")
    generator.save_to_csv(reviews, output_file)
    return output_file

@task
def analyze_reviews(input_file):
    reviews = read_reviews_from_file(input_file)
    if reviews:
        results = []
        for review_obj in reviews:
            sentiment = get_detailed_sentiment(review_obj.review_text)
            results.append((review_obj, sentiment))
        
        output_file = os.path.join("output", "daily_analysis.csv")
        save_analysis_results(results, output_file)
        return len(results)
    return 0

@flow(name="Review Monitoring Pipeline")
def review_monitoring_pipeline():
    input_file = generate_reviews()
    analyze_reviews(input_file)

if __name__ == "__main__":
    review_monitoring_pipeline()
