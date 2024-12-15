from flask import Flask, jsonify, request, abort, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tax_payments.db'
db = SQLAlchemy(app)
# After initializing your SQLAlchemy (db)
migrate = Migrate(app, db)
class TaxPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    tax_rate = db.Column(db.Float, nullable=False, default=0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/payments/calculate_tax', methods=['POST'])
def calculate_tax():
    data = request.get_json()
    print("Received data:", data)  # Debug print

    try:
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        tax_rate = float(data['tax_rate'])  # Already in percentage
        print("Extracted Tax Rate:", tax_rate)
    except (ValueError, TypeError, KeyError) as e:
        print("Error processing input:", e)  # Debug print
        abort(400, description="Invalid input")

    payments = TaxPayment.query.filter_by(due_date=due_date).all()
    
    print("Payments for due date:", payments)  # Debug print

    total_amount = sum(payment.amount for payment in payments if payment.amount is not None)
    print("Total amount:", total_amount)  # Debug print

    tax_due = total_amount * (tax_rate / 100)  # Convert percentage to decimal for calculation
    print("Tax due:", tax_due)  # Debug print

    tax_rate = sum(payment.tax_rate for payment in payments if payment.tax_rate is not None)/len(payments)

    return jsonify({'total_amount': total_amount, 'tax_rate': tax_rate, 'tax_due': float(total_amount)*float(tax_rate)}), 200

    
@app.route('/payments/due_date/<due_date>', methods=['GET'])
def get_payments_by_due_date(due_date):
    try:
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    payments = TaxPayment.query.filter_by(due_date=due_date_obj).all()
    total_amount = sum(payment.amount for payment in payments)
    tax_rate = 0.06 # You might want to calculate or fetch this value dynamically

    tax_due = total_amount * tax_rate

    return jsonify({
        'payments': [{
            'id': payment.id,
            'company': payment.company,
            'amount': payment.amount,
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'status': payment.status,
            'due_date': payment.due_date.isoformat() if payment.due_date else None,
            'tax_rate': payment.tax_rate
        } for payment in payments],
        'total_amount': total_amount,
        'tax_rate': tax_rate,
        'tax_due': tax_due
    })


@app.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = TaxPayment.query.get_or_404(payment_id)
    return jsonify({
        'id': payment.id,
        'company': payment.company,
        'amount': payment.amount,
        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
        'status': payment.status,
        'due_date': payment.due_date.isoformat() if payment.due_date else None,
        'tax_rate': payment.tax_rate
    })


@app.route('/payments', methods=['GET'])
def get_payments():
    payments = TaxPayment.query.all()
    return jsonify([{
        'id': payment.id,
        'company': payment.company,
        'amount': payment.amount,
        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
        'status': payment.status,
        'due_date': payment.due_date.isoformat() if payment.due_date else None,
        'tax_rate': payment.tax_rate
    } for payment in payments])

@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    new_payment = TaxPayment(
        company=data['company'],
        amount=data['amount'],
        payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d') if data['payment_date'] else None,
        status=data['status'],
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
        tax_rate=data.get('tax_rate', 0)  # Default to 0 if not provided
    )
    db.session.add(new_payment)
    db.session.commit()
    return jsonify({'id': new_payment.id}), 201


@app.route('/payments/<int:payment_id>', methods=['PUT'])
def update_payment(payment_id):
    payment = TaxPayment.query.get_or_404(payment_id)
    data = request.get_json()
    payment.company = data['company']
    payment.amount = data['amount']
    payment.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d') if data['payment_date'] else None
    payment.status = data['status']
    payment.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
    payment.tax_rate = data.get('tax_rate', payment.tax_rate)  # Update tax_rate if provided
    db.session.commit()
    return jsonify({'message': 'Payment updated'}), 200

@app.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    payment = TaxPayment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    return jsonify({'message': 'Payment deleted'}), 200

@app.route('/payments/due_date/<due_date>', methods=['GET'])
def filter_payments_by_due_date(due_date):
    payments = TaxPayment.query.filter_by(due_date=datetime.strptime(due_date, '%Y-%m-%d')).all()
    return jsonify([{
        'id': payment.id,
        'company': payment.company,
        'amount': payment.amount,
        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
        'status': payment.status,
        'due_date': payment.due_date.isoformat() if payment.due_date else None,
        'tax_rate': payment.tax_rate
        
    } for payment in payments])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



