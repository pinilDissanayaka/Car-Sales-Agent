from typing import Dict, Optional
from pydantic import BaseModel
from langchain_core.tools import tool

class CarPricing(BaseModel):
    model: str
    msrp: float
    min_price: float
    dealer_cost: float
    current_incentives: float = 0
    days_in_inventory: int = 0

# Sample pricing database (in real implementation, this would come from a database)
car_pricing_db: Dict[str, CarPricing] = {
    "2024_camry": CarPricing(
        model="2024 Toyota Camry",
        msrp=27000.00,
        min_price=24500.00,
        dealer_cost=23000.00,
        current_incentives=1500.00,
        days_in_inventory=45
    ),
    "2024_accord": CarPricing(
        model="2024 Honda Accord",
        msrp=28000.00,
        min_price=25500.00,
        dealer_cost=24000.00,
        current_incentives=1000.00,
        days_in_inventory=30
    )
}

@tool
def get_negotiation_strategy(model_id: str, customer_offer: float) -> str:
    """
    Get negotiation strategy based on the car model and customer's offer.
    Args:
        model_id: The car model identifier (e.g., "2024_camry")
        customer_offer: The customer's offered price
    """
    if model_id not in car_pricing_db:
        return "Car model not found in database."
    
    car = car_pricing_db[model_id]
    msrp = car.msrp
    min_price = car.min_price
    dealer_cost = car.dealer_cost
    incentives = car.current_incentives
    days_in_inventory = car.days_in_inventory
    
    # Calculate target price based on various factors
    inventory_discount = 0
    if days_in_inventory > 60:
        inventory_discount = 1000
    elif days_in_inventory > 30:
        inventory_discount = 500
    
    target_price = min_price - inventory_discount - incentives
    margin = customer_offer - dealer_cost
    
    # Generate negotiation strategy
    if customer_offer >= target_price:
        return (
            f"ACCEPT OFFER: Customer offer of ${customer_offer:,.2f} is acceptable. "
            f"Deal provides ${margin:,.2f} in margin. Proceed with closing the deal and "
            f"highlight included features and warranty options."
        )
    
    elif customer_offer >= min_price:
        return (
            f"COUNTER OFFER: Customer offer of ${customer_offer:,.2f} is close. "
            f"Counter with ${target_price:,.2f} and emphasize current incentives "
            f"worth ${incentives:,.2f}. Highlight value features and limited-time offers."
        )
    
    elif customer_offer >= dealer_cost:
        suggested_counter = min_price - (incentives / 2)
        return (
            f"NEGOTIATE: Customer offer of ${customer_offer:,.2f} is below minimum. "
            f"Counter with ${suggested_counter:,.2f}. Emphasize market value, "
            f"vehicle quality, and available incentives. Consider offering additional services."
        )
    
    else:
        return (
            f"EDUCATE: Customer offer of ${customer_offer:,.2f} is too low. "
            f"Explain market value (MSRP: ${msrp:,.2f}), highlight vehicle features, "
            f"and demonstrate value proposition. Provide market comparison data."
        )

@tool
def calculate_payment_options(
    model_id: str,
    sale_price: float,
    down_payment: float = 0,
    trade_in_value: float = 0,
    credit_score: Optional[int] = None,
    term_months: int = 60
) -> str:
    """
    Calculate monthly payment options based on the negotiated price and terms.
    Args:
        model_id: The car model identifier
        sale_price: The negotiated sale price
        down_payment: Down payment amount
        trade_in_value: Trade-in value
        credit_score: Customer's credit score
        term_months: Loan term in months
    """
    # Base interest rates (would come from external service in real implementation)
    if credit_score is None:
        interest_rate = 0.05  # Default rate
    elif credit_score >= 720:
        interest_rate = 0.029
    elif credit_score >= 680:
        interest_rate = 0.039
    elif credit_score >= 620:
        interest_rate = 0.049
    else:
        interest_rate = 0.069
    
    # Calculate loan amount
    loan_amount = sale_price - down_payment - trade_in_value
    
    # Calculate monthly payment (simple calculation - real world would be more complex)
    monthly_rate = interest_rate / 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    
    # Calculate total cost
    total_cost = monthly_payment * term_months
    total_interest = total_cost - loan_amount
    
    return (
        f"Payment Options for {car_pricing_db[model_id].model}:\n"
        f"Sale Price: ${sale_price:,.2f}\n"
        f"Down Payment: ${down_payment:,.2f}\n"
        f"Trade-in Value: ${trade_in_value:,.2f}\n"
        f"Loan Amount: ${loan_amount:,.2f}\n"
        f"Term: {term_months} months\n"
        f"Interest Rate: {interest_rate:.1%}\n"
        f"Monthly Payment: ${monthly_payment:.2f}\n"
        f"Total Interest: ${total_interest:,.2f}\n"
        f"Total Cost: ${total_cost:,.2f}"
    )