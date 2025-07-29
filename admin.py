import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes
)
from telegram.error import TelegramError

# Enable logging (reused from bot.py)
logger = logging.getLogger(__name__)

# In-memory storage (imported from bot.py context)
user_data = {}  # This will be populated when imported by bot.py
crypto_addresses = {}  # This will be populated when imported by bot.py

def create_cancel_keyboard():
    """Create a keyboard with cancel button"""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel with options"""
    user_id = update.effective_user.id
    admin_id = context.job.data.get('admin_id') if context.job else int(context.bot_data.get('admin_id', 0))
    if not admin_id or user_id != admin_id:
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
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing action...")
    user_id = update.effective_user.id
    admin_id = context.job.data.get('admin_id') if context.job else int(context.bot_data.get('admin_id', 0))
    if not admin_id or user_id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return
    action = query.data
    if action == 'admin_list_users':
        if not user_data:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="📝 No users registered yet."
            )
            return
        users_list = """👥 **Registered Users** 👥

Below is a detailed list of all registered users:\n\n"""
        for uid, data in user_data.items():
            status = "✅ Approved" if data['approved'] else "⏳ Pending"
            bot = data['active_bot'] if data['active_bot'] else "None"
            pending_dep = f"${data['pending_deposit']:.2f}" if data['pending_deposit'] > 0 else "None"
            pending_with = f"${data['pending_withdrawal']:.2f}" if data['pending_withdrawal'] > 0 else "None"
            users_list += f"🆔 **{uid}** - {data['name']}\n" + \
                          f"📧 {data['email']}\n" + \
                          f"📱 {data['phone']}\n" + \
                          f"💰 Balance: ${data['balance']:.2f}\n" + \
                          f"📈 Deposit: ${data['deposit']:.2f}\n" + \
                          f"📊 Profit: ${data['profit']:.2f}\n" + \
                          f"📉 Withdrawal: ${data['withdrawal']:.2f}\n" + \
                          f"📊 Status: {status}\n" + \
                          f"🤖 Active Bot: {bot}\n" + \
                          f"💳 Pending Deposit: {pending_dep}\n" + \
                          f"💸 Pending Withdrawal: {pending_with}\n" + \
                          "━━━━━━━━━━━━━━━━━━━━\n"
        if len(users_list) > 4000:
            parts = [users_list[i:i+4000] for i in range(0, len(users_list), 4000)]
            for part in parts:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=part,
                    parse_mode='Markdown'
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=users_list,
                parse_mode='Markdown'
            )
    elif action in ['admin_approve_user', 'admin_approve_deposit', 'admin_approve_withdrawal',
                   'admin_update_profit', 'admin_update_crypto', 'admin_help']:
        if action == 'admin_approve_user':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter the user ID to approve (use /getid to find IDs):",
                reply_markup=create_cancel_keyboard()
            )
            context.user_data['admin_action'] = 'approve_user'
        elif action == 'admin_approve_deposit':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter: /approve <user_id> <amount>",
                reply_markup=create_cancel_keyboard()
            )
            context.user_data['admin_action'] = 'approve_deposit'
        elif action == 'admin_approve_withdrawal':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter: /approvewithdrawal <user_id> <amount>",
                reply_markup=create_cancel_keyboard()
            )
            context.user_data['admin_action'] = 'approve_withdrawal'
        elif action == 'admin_update_profit':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter: /updateprofit <user_id> <amount>",
                reply_markup=create_cancel_keyboard()
            )
            context.user_data['admin_action'] = 'update_profit'
        elif action == 'admin_update_crypto':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter: /updatecrypto <crypto_name> <address>",
                reply_markup=create_cancel_keyboard()
            )
            context.user_data['admin_action'] = 'update_crypto'
        elif action == 'admin_help':
            help_text = """🛠 **Admin Panel Guide** 🛠

Welcome to the NCW Trading Bot Admin Panel. Below are the available actions and how to use them:

👥 **List Users**

- View all registered users with details (ID, name, email, balance, etc.).
- Use the 'List Users' button or /listusers.

✅ **Approve User**

- Approve a user's account to grant access to trading features.
- Command: /approveuser <user_id>
- Example: /approveuser 123456789
- Alternatively, use the 'Approve' button in registration notifications.

💳 **Approve Deposit**

- Confirm a user's deposit to update their balance.
- Command: /approve <user_id> <amount>
- Example: /approve 123456789 1000.50
- Alternatively, use the 'Approve' button in deposit notifications.

💸 **Approve Withdrawal**

- Process a user's withdrawal request.
- Command: /approvewithdrawal <user_id> <amount>
- Example: /approvewithdrawal 123456789 500.25
- Alternatively, use the 'Approve' button in withdrawal notifications.

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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_text,
                parse_mode='Markdown'
            )

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve deposits"""
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
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
                text=f"✅ Your deposit of ${amount:.2f} has been confirmed! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        await update.message.reply_text(f"✅ Approved ${amount:.2f} deposit for user {user_id}.")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approve <user_id> <amount>")

async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve withdrawals"""
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
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
            await update.message.reply_text("❌ Insufficient user balance.")
            return
        user_info['balance'] -= amount
        user_info['withdrawal'] += amount
        user_info['pending_withdrawal'] = 0
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Your withdrawal of ${amount:.2f} has been processed! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        await update.message.reply_text(f"✅ Approved ${amount:.2f} withdrawal for user {user_id}.")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approvewithdrawal <user_id> <amount>")

async def update_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update user profits"""
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
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
                text=f"🎉 Congratulations! You've earned ${amount:.2f} in profits from your active trading bot. Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        await update.message.reply_text(f"✅ Added ${amount:.2f} profit for user {user_id}.")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /updateprofit <user_id> <amount>")

async def update_crypto_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update crypto addresses"""
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
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
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
        await update.message.reply_text("❌ Unauthorized access.")
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
        keyboard = [
            [InlineKeyboardButton("✅ Proceed", callback_data='proceed_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Great news {user_info['name']}! Your account has been approved. You can now visit our website and use all trading features.",
                reply_markup=reply_markup
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        await update.message.reply_text(f"✅ Approved account for user {user_id} ({user_info['name']}).")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approveuser <user_id>")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list all users"""
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
        await update.message.reply_text("❌ Unauthorized access.")
        return
    if not user_data:
        await update.message.reply_text("📝 No users registered yet.")
        return
    users_list = """👥 **Registered Users** 👥

Below is a detailed list of all registered users:\n\n"""
    for uid, data in user_data.items():
        status = "✅ Approved" if data['approved'] else "⏳ Pending"
        bot = data['active_bot'] if data['active_bot'] else "None"
        pending_dep = f"${data['pending_deposit']:.2f}" if data['pending_deposit'] > 0 else "None"
        pending_with = f"${data['pending_withdrawal']:.2f}" if data['pending_withdrawal'] > 0 else "None"
        users_list += f"🆔 **{uid}** - {data['name']}\n" + \
                      f"📧 {data['email']}\n" + \
                      f"📱 {data['phone']}\n" + \
                      f"💰 Balance: ${data['balance']:.2f}\n" + \
                      f"📈 Deposit: ${data['deposit']:.2f}\n" + \
                      f"📊 Profit: ${data['profit']:.2f}\n" + \
                      f"📉 Withdrawal: ${data['withdrawal']:.2f}\n" + \
                      f"📊 Status: {status}\n" + \
                      f"🤖 Active Bot: {bot}\n" + \
                      f"💳 Pending Deposit: {pending_dep}\n" + \
                      f"💸 Pending Withdrawal: {pending_with}\n" + \
                      "━━━━━━━━━━━━━━━━━━━━\n"
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
    user_id = update.effective_user.id
    admin_id = context.bot_data.get('admin_id', 0)
    if not admin_id or user_id != int(admin_id):
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
- Alternatively, use the 'Approve' button in registration notifications.

💳 **Approve Deposit**

- Confirm a user's deposit to update their balance.
- Command: /approve <user_id> <amount>
- Example: /approve 123456789 1000.50
- Alternatively, use the 'Approve' button in deposit notifications.

💸 **Approve Withdrawal**

- Process a user's withdrawal request.
- Command: /approvewithdrawal <user_id> <amount>
- Example: /approvewithdrawal 123456789 500.25
- Alternatively, use the 'Approve' button in withdrawal notifications.

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
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def send_admin_panel(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send admin panel to admin on bot startup"""
    admin_id = context.job.data.get('admin_id', 0)
    if not admin_id:
        logger.error("Admin ID not provided in job data.")
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
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=panel_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except TelegramError as e:
        logger.error(f"Failed to send admin panel on startup: {e}")