from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Sample data for our APIs
about_us_data = {
    "title": "About Our Grocery Delivery Service",
    "mission": "To provide fresh, high-quality groceries to your doorstep with unmatched convenience and reliability.",
    "history": "Founded in 2020, we started as a small local delivery service and have grown to serve thousands of customers across multiple cities.",
    "team": [
        {
            "name": "John Doe",
            "position": "CEO & Founder",
            "bio": "John has over 15 years of experience in retail and e-commerce."
        },
        {
            "name": "Jane Smith",
            "position": "Head of Operations",
            "bio": "Jane ensures that all deliveries are made on time and with care."
        },
        {
            "name": "Mike Johnson",
            "position": "Chief Technology Officer",
            "bio": "Mike leads our tech team to create seamless online shopping experiences."
        }
    ],
    "values": [
        "Customer Satisfaction",
        "Quality Products",
        "Timely Delivery",
        "Environmental Responsibility"
    ]
}

contact_us_data = {
    "title": "Contact Us",
    "description": "We're here to help! Reach out to us through any of the following channels:",
    "email": "support@grocerydelivery.com",
    "phone": "+1 (555) 123-4567",
    "hours": "Monday to Friday: 8am - 8pm, Saturday and Sunday: 9am - 6pm",
    "address": {
        "street": "123 Grocery Lane",
        "city": "Fresh City",
        "state": "FC",
        "zip": "12345"
    },
    "social_media": {
        "facebook": "facebook.com/grocerydelivery",
        "twitter": "twitter.com/grocerydelivery",
        "instagram": "instagram.com/grocerydelivery"
    },
    "faq": [
        {
            "question": "How do I track my order?",
            "answer": "You can track your order by logging into your account and visiting the 'Orders' section."
        },
        {
            "question": "What is your return policy?",
            "answer": "If you're not satisfied with any product, you can return it within 24 hours of delivery."
        },
        {
            "question": "Do you deliver to my area?",
            "answer": "We currently deliver to most major cities. Enter your zip code on our homepage to check availability."
        }
    ]
}

@app.route('/api/about-us', methods=['GET'])
def about_us():
    return jsonify(about_us_data)

@app.route('/api/contact-us', methods=['GET'])
def contact_us():
    return jsonify(contact_us_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Run on port 5001 to avoid conflict with Django