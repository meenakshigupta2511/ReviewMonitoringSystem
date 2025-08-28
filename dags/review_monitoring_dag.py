from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from bin.data_generator import ReviewDataGenerator
from bin.sentiment_analyzer import read_reviews_from_file, get_detailed_sentiment, save_analysis_results
from bin.database import Database

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def generate_daily_reviews():
    """Generate new review data"""
    generator = ReviewDataGenerator()
    
    # Generate 20 reviews for today
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now()
    reviews = generator.generate_dataset(20, start_date, end_date)
    
    # Save to file
    output_file = os.path.join(project_root, "input", "daily_reviews.csv")
    generator.save_to_csv(reviews, output_file)
    return output_file

def analyze_reviews():
    """Analyze the generated reviews"""
    input_file = os.path.join(project_root, "input", "daily_reviews.csv")
    
    # Read and analyze reviews
    reviews = read_reviews_from_file(input_file)
    if reviews:
        results = []
        for review_obj in reviews:
            sentiment = get_detailed_sentiment(review_obj.review_text)
            results.append((review_obj, sentiment))
        
        # Save results
        output_file = os.path.join(project_root, "output", "daily_analysis.csv")
        save_analysis_results(results, output_file)
        
        return len(results)
    return 0

# Create the DAG
with DAG(
    'review_monitoring_pipeline',
    default_args=default_args,
    description='Daily review generation and sentiment analysis pipeline',
    schedule_interval='0 0 * * *',  # Run daily at midnight
    start_date=datetime(2025, 8, 27),
    catchup=False,
    tags=['reviews', 'sentiment']
) as dag:
    
    # Task 1: Clean up old files
    cleanup = BashOperator(
        task_id='cleanup_old_files',
        bash_command=f'rm -f {project_root}/input/daily_reviews.csv {project_root}/output/daily_analysis.csv',
        dag=dag
    )
    
    # Task 2: Generate new reviews
    generate_reviews = PythonOperator(
        task_id='generate_reviews',
        python_callable=generate_daily_reviews,
        dag=dag
    )
    
    # Task 3: Analyze reviews
    analyze = PythonOperator(
        task_id='analyze_reviews',
        python_callable=analyze_reviews,
        dag=dag
    )
    
    # Define task dependencies
    cleanup >> generate_reviews >> analyze
