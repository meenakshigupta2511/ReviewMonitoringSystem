@echo off
cd /d "%~dp0"
python bin/data_generator.py --num 20 --days 1
python bin/sentiment_analyzer.py input/generated_reviews.csv
