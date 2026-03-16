import uuid
import random
from datetime import datetime

class PaymentService:
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
    
    def initialize_payment(self, email, amount, reference, metadata=None):
        """Initialize a payment - simulated version"""
        if self.simulation_mode:
            # Simulate payment initialization
            print(f"\n{'='*50}")
            print(f"SIMULATED PAYMENT INITIALIZATION")
            print(f"Email: {email}")
            print(f"Amount: N{amount:,.2f}")
            print(f"Reference: {reference}")
            print(f"{'='*50}\n")
            
            # Return a simulated response
            return {
                'status': True,
                'data': {
                    'authorization_url': f"/payment/simulate/{reference}",
                    'reference': reference,
                    'amount': amount
                }
            }
        else:
            # Real Paystack implementation would go here
            pass
    
    def verify_payment(self, reference):
        """Verify a payment - simulated version"""
        if self.simulation_mode:
            # Simulate random success/failure (80% success rate)
            is_success = random.random() < 0.8
            
            if is_success:
                return {
                    'status': True,
                    'data': {
                        'status': 'success',
                        'reference': reference,
                        'amount': 5000,  # Sample amount
                        'paid_at': datetime.now().isoformat(),
                        'channel': 'card',
                        'customer': {
                            'email': 'customer@example.com'
                        }
                    }
                }
            else:
                return {
                    'status': True,
                    'data': {
                        'status': 'failed',
                        'reference': reference,
                        'message': 'Payment failed'
                    }
                }
        else:
            # Real Paystack implementation
            pass
