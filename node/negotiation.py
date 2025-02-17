from typing import  Optional
from langchain_core.tools import tool
from database.models import Cars
from database.database import session
from utils import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


@tool
def get_negotiation_strategy(id: int, customer_offer: float) -> str:
    """
    Generate a negotiation strategy based on the customer offer and car details.

    Args:
        id (int): The car model identifier
        customer_offer (float): The customer's offer price

    Returns:
        str: The negotiation strategy
    """
    # Get the car details
    car = session.query(Cars).filter(Cars.id == id).first()

    # Extract the minimum and market price
    min_price = car.min_price
    market_price = car.market_price
    print(f"min_price: {min_price}, market_price: {market_price}")
    # Generate negotiation strategy
    if customer_offer > market_price:
        pass
    elif customer_offer >= min_price:
        # Accept the offer
        strategy = (
            f"ACCEPT OFFER: Customer offer of ${customer_offer:,.2f} is acceptable. "
            f"Deal provides ${customer_offer:,.2f} in margin. Proceed with closing the deal and "
            f"highlight included features and warranty options."
        )
    else:
        # Educate the customer on the market value
        strategy = (
            f"EDUCATE: Customer offer of ${customer_offer:,.2f} is too low. "
            f"Explain market value (MSRP: ${market_price:,.2f}), highlight vehicle features, "
            f"and demonstrate value proposition. Provide market comparison data."
        )

    # Use LLM to generate the negotiation strategy

    negotiation_prompt_template = """
    Take the following negotiation strategy and rewrite it into a conversational that feels natural to a customer.
    consider you in the chat flow.
        Strategy: {STRATEGY}
    Ensure the response is:
        Clear and concise – Avoid jargon and overly technical terms.
        Friendly and engaging – Use a warm and professional tone.
        Persuasive but not pushy – Focus on value rather than just price.
        No greetings – The response should flow naturally in an ongoing conversation.
        Make the response feel like it’s coming from a helpful, knowledgeable salesperson who wants the best deal for the customer.
    """

    negotiation_prompt = ChatPromptTemplate.from_template(negotiation_prompt_template)

    negotiation_chain = (
        {"STRATEGY": RunnablePassthrough()} |
        negotiation_prompt |
        llm |
        StrOutputParser()
    )

    strategy = negotiation_chain.invoke({"STRATEGY": strategy})
    
    return strategy




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