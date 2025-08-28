import csv
import random
from datetime import datetime, timedelta
import os

class ReviewDataGenerator:
    def __init__(self):
        self.products = [
            "Smart Watch X1", "Smart Watch X2", "Fitness Tracker Pro",
            "Wireless Earbuds", "Smart Speaker", "Gaming Headset"
        ]
        
        self.reviewer_first_names = [
            "John", "Jane", "Mike", "Sarah", "David", "Emily",
            "James", "Lisa", "Robert", "Maria", "Michael", "Emma"
        ]
        
        self.reviewer_last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
            "Miller", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson"
        ]
        
        self.positive_templates = [
            "This {product} is amazing! {feature}",
            "Excellent product! {feature}",
            "Really happy with my {product}. {feature}",
            "Best purchase ever! {feature}",
            "Highly recommend this {product}. {feature}"
        ]
        
        self.negative_templates = [
            "Disappointed with this {product}. {issue}",
            "Not worth the money. {issue}",
            "Would not recommend. {issue}",
            "Poor quality {product}. {issue}",
            "Save your money. {issue}"
        ]
        
        self.neutral_templates = [
            "This {product} is okay. {mixed}",
            "Average product. {mixed}",
            "Could be better but works fine. {mixed}",
            "Decent {product} for the price. {mixed}",
            "Not great, not terrible. {mixed}"
        ]
        
        self.positive_features = [
            "Great battery life and comfortable to wear.",
            "The features are intuitive and work perfectly.",
            "Build quality is outstanding.",
            "Customer service was excellent.",
            "Performance exceeds expectations."
        ]
        
        self.negative_issues = [
            "Battery life is terrible.",
            "Stopped working after a few days.",
            "Poor build quality and unreliable.",
            "Customer service was unhelpful.",
            "Not worth the premium price."
        ]
        
        self.mixed_comments = [
            "Some features work well, others need improvement.",
            "Good features but battery life could be better.",
            "Nice design but a bit expensive.",
            "Works as intended but nothing special.",
            "Basic functionality is good but lacks advanced features."
        ]

    def generate_review(self, sentiment_bias=None):
        """Generate a single review with specified sentiment bias"""
        product = random.choice(self.products)
        reviewer_name = f"{random.choice(self.reviewer_first_names)} {random.choice(self.reviewer_last_names)}"
        
        # Determine sentiment based on bias or randomly
        if sentiment_bias:
            sentiment = sentiment_bias
        else:
            sentiment = random.choices(['positive', 'negative', 'neutral'], weights=[0.6, 0.3, 0.1])[0]
        
        # Generate review text based on sentiment
        if sentiment == 'positive':
            template = random.choice(self.positive_templates)
            detail = random.choice(self.positive_features)
            rating = random.randint(4, 5)
        elif sentiment == 'negative':
            template = random.choice(self.negative_templates)
            detail = random.choice(self.negative_issues)
            rating = random.randint(1, 2)
        else:
            template = random.choice(self.neutral_templates)
            detail = random.choice(self.mixed_comments)
            rating = 3
        
        review_text = template.format(
            product=product,
            feature=detail,
            issue=detail,
            mixed=detail
        )
        
        return {
            'review_text': review_text,
            'reviewer_name': reviewer_name,
            'product_name': product,
            'rating': rating
        }

    def generate_dataset(self, num_reviews, start_date=None, end_date=None):
        """Generate a dataset of reviews with dates"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        date_range = (end_date - start_date).days
        reviews = []
        
        for _ in range(num_reviews):
            review = self.generate_review()
            # Generate random date within range
            random_days = random.randint(0, date_range)
            review_date = start_date + timedelta(days=random_days)
            review['date'] = review_date.strftime('%Y-%m-%d')
            reviews.append(review)
        
        # Sort by date
        reviews.sort(key=lambda x: x['date'])
        return reviews

    def save_to_csv(self, reviews, output_file):
        """Save generated reviews to CSV file"""
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['review_text', 'reviewer_name', 'product_name', 'date', 'rating'])
            writer.writeheader()
            writer.writerows(reviews)

def main():
    generator = ReviewDataGenerator()
    
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Generate sample review data')
    parser.add_argument('--num', type=int, default=100,
                       help='Number of reviews to generate (default: 100)')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days in the past to generate reviews for (default: 30)')
    args = parser.parse_args()
    
    # Generate reviews
    start_date = datetime.now() - timedelta(days=args.days)
    reviews = generator.generate_dataset(args.num, start_date)
    
    # Save to file in input directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "generated_reviews.csv")
    generator.save_to_csv(reviews, output_file)
    print(f"Generated {args.num} reviews and saved to: {output_file}")

if __name__ == "__main__":
    main()
