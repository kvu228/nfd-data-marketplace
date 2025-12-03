"""
Utility functions for user-related operations
"""
from web3 import Web3
from db import get_demo_db
from provider import get_web3_provider
from constants import LOCAL_ENDPOINT


def get_user_display_options(include_balance: bool = True):
    """
    Get list of user display options with wallet address and balance.
    
    Args:
        include_balance: Whether to include balance in display (default: True)
    
    Returns:
        tuple: (display_options, user_data_dict)
            - display_options: List of formatted strings for selectbox
            - user_data_dict: Dict mapping display string to (uname, wallet, balance)
    """
    con = get_demo_db()
    res = con.execute("SELECT uname, wallet FROM users")
    users = res.fetchall()
    con.close()
    
    display_options = []
    user_data_dict = {}
    
    if include_balance:
        web3 = get_web3_provider(LOCAL_ENDPOINT)
        for uname, wallet in users:
            try:
                balance_wei = web3.eth.get_balance(wallet)
                balance_eth = Web3.from_wei(balance_wei, 'ether')
                display_text = f"{uname} ({wallet[:10]}...{wallet[-8:]}) - {balance_eth:.4f} ETH"
            except Exception as e:
                # Fallback if balance fetch fails
                print("Error get_balance for", wallet, ":", e)
                display_text = f"{uname} ({wallet[:10]}...{wallet[-8:]}) - N/A"
                balance_eth = 0.0
            
            display_options.append(display_text)
            user_data_dict[display_text] = (uname, wallet, balance_eth)
    else:
        for uname, wallet in users:
            display_text = f"{uname} ({wallet[:10]}...{wallet[-8:]})"
            display_options.append(display_text)
            user_data_dict[display_text] = (uname, wallet, 0.0)
    
    return display_options, user_data_dict


def get_user_from_display(selected_display: str, user_data_dict: dict):
    """
    Extract username from selected display option.
    
    Args:
        selected_display: The selected display string from selectbox
        user_data_dict: Dict from get_user_display_options()
    
    Returns:
        str: Username (uname)
    """
    if selected_display in user_data_dict:
        return user_data_dict[selected_display][0]
    # Fallback: try to extract username if format is unexpected
    return selected_display.split(' ')[0]

