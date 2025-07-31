Trading Bot
A Telegram bot designed to facilitate cryptocurrency trading operations, including deposits, withdrawals, and trading bot activation. The bot supports multiple cryptocurrencies (Bitcoin, Ethereum, USDT, XRP, XLM, BNB, Solana) and provides a user-friendly interface for managing investments. It includes admin features for approving transactions and managing user data.
Features

User Registration: Collects user details (name, email, phone) for account setup.
Deposit Management: Supports deposits in multiple cryptocurrencies with automatic clipboard copying for wallet addresses.
Withdrawal Options: Allows withdrawals via cryptocurrency or bank transfer.
Trading Bots: Offers multiple trading strategies with configurable profit rates.
Admin Controls: Admins can approve deposits/withdrawals, update profits, manage crypto addresses, and view user data.
Error Handling: Robust logging and error messages for reliable operation.

Prerequisites

Python 3.8+
A Telegram bot token from BotFather
A Telegram user ID for admin access
Dependencies listed in requirements.txt

Installation

Clone the Repository:
git clone https://github.com/Ghost-tech-ng/Telegram-Trading-Bot-.git
cd Telegram-Trading-Bot-


Set Up a Virtual Environment (optional but recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Set Environment Variables:Create a .env file in the project root with the following:
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_admin_telegram_user_id


Directory Structure:Ensure the following files are in the project root:
Telegram-Trading-Bot-/
├── bot.py
├── admin.py
├── storage.py
├── requirements.txt
├── .env



Usage

Run the Bot:
python bot.py


Interact with the Bot:

Start the bot in Telegram by sending /start.
Register with your name, email, and phone number.
Use the main menu to:
Deposit funds in supported cryptocurrencies.
Withdraw funds via crypto or bank transfer.
Activate trading bots with different strategies.
Refresh balance or visit the website.


Admins can use commands like /adminpanel, /listusers, /approve, etc., for management.


Admin Commands:

/adminpanel: Access the admin control panel.
/listusers: View all registered users.
/approve <user_id> <amount>: Approve a deposit.
/approvewithdrawal <user_id> <amount>: Approve a withdrawal.
/updateprofit <user_id> <amount>: Update user profit.
/updatecrypto <crypto> <address>: Update cryptocurrency wallet addresses.
/adminhelp: View admin command help.
/sendlogin <user_id>: Send login details to a user.



Supported Cryptocurrencies

Bitcoin (BTC)
Ethereum (ETH)
USDT
XRP
XLM
BNB
Solana (SOL)

Notes

Clipboard Copying: The bot attempts to copy wallet addresses to the clipboard using JavaScript. This feature may not work in all Telegram clients (e.g., mobile apps). A plain text address is always provided for manual copying.
Security: Ensure the .env file is not committed to GitHub (add it to .gitignore). Never share your bot token or admin user ID publicly.
Logging: The bot logs events and errors to the console for debugging. Check logs for troubleshooting.

Requirements
Create a requirements.txt file with:
python-telegram-bot==20.7
python-dotenv==1.0.0

Contributing

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Commit your changes (git commit -m 'Add your feature').
Push to the branch (git push origin feature/your-feature).
Create a Pull Request.

License
This project is licensed under the MIT License.
Contact
For issues or feature requests, open a GitHub issue or contact the project maintainer.