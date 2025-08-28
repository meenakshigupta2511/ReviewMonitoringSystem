# Review Monitoring System

A system for monitoring and analyzing product reviews using sentiment analysis.

## Project Structure

```
ReviewMonitoringSystem/
├── bin/
│   ├── data_generator.py      # Generates sample review data
│   ├── sentiment_analyzer.py  # Analyzes sentiment of reviews
│   ├── database.py           # Database operations
│   └── query_database.py     # Database query utilities
├── dags/
│   └── review_monitoring_dag.py  # Airflow DAG for scheduling
├── data/
│   └── sentiment_analysis.db     # SQLite database
├── input/
│   └── generated_reviews.csv     # Input review data
├── output/
│   └── reviews_analysis.csv      # Analysis results
├── flows/
│   └── review_monitoring_flow.py # Prefect flow definition
└── requirements.txt              # Project dependencies
```

## Features

- Generate synthetic review data
- Sentiment analysis using VADER and TextBlob
- Database storage with SQLite
- CSV import/export
- Automated scheduling options
- Detailed sentiment analysis reports
- Product and reviewer analytics

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ReviewMonitoringSystem.git
cd ReviewMonitoringSystem
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python bin/database.py
```

## Usage

### Generate Sample Reviews
```bash
python bin/data_generator.py --num 100 --days 30
```

### Analyze Reviews
```bash
python bin/sentiment_analyzer.py input/generated_reviews.csv
```

### Query Results
```bash
python bin/query_database.py --recent 7
python bin/query_database.py --product "Smart Watch X1"
python bin/query_database.py --trends 30
```

## Data Format

Input CSV format:
```csv
review_text,reviewer_name,product_name,date,rating
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
