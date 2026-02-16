import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

# Enable logging
logger = logging.getLogger(__name__)

def create_cancel_keyboard():
    """Create a keyboard with cancel button"""
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='cancel')]]
    return InlineKeyboardMarkup(keyboard)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel with options"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    logger.info(f"Admin panel accessed - user_id: {user_id}, admin_id: {admin_id}")
    
    if not admin_id or user_id != admin_id:
        logger.warning(f"Unauthorized access attempt - user_id: {user_id}, admin_id: {admin_id}")
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    panel_text = """🛠 **NCW Trading Bot Admin Panel** 🛠

Welcome to the admin control center. Manage users, transactions, and system settings below."""
    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data='admin_list_users')],
        [InlineKeyboardButton("✅ Approve User", callback_data='admin_approve_user')],
        [InlineKeyboardButton("💳 Approve Deposit", callback_data='admin_approve_deposit')],
        [InlineKeyboardButton("💸 Approve Withdrawal", callback_data='admin_approve_withdrawal')],
        [InlineKeyboardButton("❌ Reject Withdrawal", callback_data='admin_reject_withdrawal')],
        [InlineKeyboardButton("📈 Update Profit", callback_data='admin_update_profit')],
        [InlineKeyboardButton("💎 Update Stake Balance", callback_data='admin_update_stake')],
        [InlineKeyboardButton("🔒 Update Locked Stake", callback_data='admin_update_locked')],
        [InlineKeyboardButton("🪙 Update Crypto Address", callback_data='admin_update_crypto')],
        [InlineKeyboardButton("📩 Send Login Details", callback_data='admin_send_login')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='admin_help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(panel_text, reply_markup=reply_markup, parse_mode='Markdown')

async def cancel_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel admin action"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Action cancelled.")

async def approve_pending_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve a selected pending user"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return
    
    try:
        target_user_id = int(query.data.split('_')[-1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info or not user_info.get('name'):
            await query.edit_message_text("❌ User not found.")
            return
        
        if user_info.get('approved', False):
            await query.edit_message_text(
                f"✅ User {user_info['name']} (ID: {target_user_id}) is already approved!"
            )
            return
        
        # Approve user
        user_info['approved'] = True
        db.save_user(target_user_id, user_info)
        
        # Update admin message
        await query.edit_message_text(
            f"""✅ **User Approved Successfully!**

👤 **Name:** {user_info['name']}
🆔 **User ID:** {target_user_id}
📧 **Email:** {user_info.get('email', 'N/A')}
📱 **Phone:** {user_info.get('phone', 'N/A')}

The user has been notified and can now access the bot.""",
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
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=menu_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            # mark user as in the main menu conversation
            user_data_store = context.application.dispatcher.user_data
            user_store = user_data_store.setdefault(target_user_id, {})
            user_store['conversation_state'] = 'MAIN_MENU'
            user_store['_in_conversation'] = True
            logger.info(f"Sent approval notification and main menu to user {target_user_id}")
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id} of approval: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ User approved but failed to send notification: {e}"
            )
        
    except (ValueError, IndexError) as e:
        logger.error(f"Error approving pending user: {e}")
        await query.edit_message_text("❌ Invalid user selection.")
    
async def show_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of pending users for approval"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return
    
    from database import db
    user_data = db.get_all_users()
    
    # Filter pending users
    pending_users = {uid: data for uid, data in user_data.items() if not data.get('approved', False)}
    
    if not pending_users:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ No pending users to approve. All users are already approved!"
        )
        return
    
    # Create buttons for each pending user
    keyboard = []
    for uid, data in pending_users.items():
        user_display = f"{data.get('name', 'N/A')} - ID: {uid}"
        keyboard.append([InlineKeyboardButton(
            f"👤 {user_display}", 
            callback_data=f'approve_pending_user_{uid}'
        )])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data='cancel_admin_action')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👥 **Pending Users**\n\nSelect a user to approve:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel button actions"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Unauthorized access."
        )
        return
    
    action = query.data
    
    if action == 'admin_list_users':
        from database import db
        user_data = db.get_all_users()
        
        if not user_data:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="📭 No users registered yet."
            )
            return
        
        users_list = """👥 **Registered Users** 👥\n\n"""
        for uid, data in user_data.items():
            status = "✅ Approved" if data.get('approved', False) else "⏳ Pending"
            bot = data.get('active_bot', 'None') if data.get('active_bot') else "None"
            pending_dep = f"${data.get('pending_deposit', 0):.2f}" if data.get('pending_deposit', 0) > 0 else "None"
            pending_with = f"${data.get('pending_withdrawal', 0):.2f}" if data.get('pending_withdrawal', 0) > 0 else "None"
            
            users_list += (
                f"🆔 **{uid}** - {data.get('name', 'N/A')}\n"
                f"📧 {data.get('email', 'N/A')}\n"
                f"📱 {data.get('phone', 'N/A')}\n"
                f"💰 Balance: ${data.get('balance', 0):.2f}\n"
                f"📈 Deposit: ${data.get('deposit', 0):.2f}\n"
                f"📊 Profit: ${data.get('profit', 0):.2f}\n"
                f"📉 Withdrawal: ${data.get('withdrawal', 0):.2f}\n"
                f"📊 Status: {status}\n"
                f"🤖 Active Bot: {bot}\n"
                f"💳 Pending Deposit: {pending_dep}\n"
                f"💸 Pending Withdrawal: {pending_with}\n"
                "━━━━━━━━━━━━━━━━━━━\n"
            )
        
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
    
    
    elif action == 'admin_approve_user':  # NEW CASE
        await show_pending_users(update, context)

    elif action == 'admin_approve_deposit':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /approve <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_approve_withdrawal':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /approvewithdrawal <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_reject_withdrawal':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /rejectwithdrawal <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        
    elif action == 'admin_update_stake':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /updatestake <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        
    elif action == 'admin_update_locked':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /updatelocked <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_update_profit':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /updateprofit <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
        
    elif action == 'admin_release_stake':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /releasestake <user_id> <amount>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_update_crypto':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /updatecrypto <crypto_name> <address>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_send_login':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter: /sendlogin <user_id> <username> <password>",
            reply_markup=create_cancel_keyboard()
        )
    
    elif action == 'admin_help':
        help_text = """🛠 **Admin Panel Guide** 🛠

Welcome to the NCW Trading Bot Admin Panel. Below are the available commands:

👥 /listusers - List all registered users
💳 /approve <user_id> <amount> - Approve a deposit
💸 /approvewithdrawal <user_id> <amount> - Approve a withdrawal
❌ /rejectwithdrawal <user_id> <amount> - Reject a withdrawal
📈 /updateprofit <user_id> <amount> - Update user's profit
🪙 /updatecrypto <crypto> <address> - Update crypto address
📩 /sendlogin <user_id> <username> <password> - Send login details to user
ℹ️ /adminhelp - Show this help message"""
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_text,
            parse_mode='Markdown'
        )

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve deposits"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /approve <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            logger.error(f"User {target_user_id} not found for deposit approval")
            await update.message.reply_text(f"❌ User {target_user_id} not found. Use /listusers to see registered users.")
            return
        
        user_info['balance'] = user_info.get('balance', 0) + amount
        user_info['deposit'] = user_info.get('deposit', 0) + amount
        user_info['pending_deposit'] = 0
        
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ Your deposit of ${amount:.2f} has been confirmed! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
            logger.info(f"Notified user {target_user_id} of deposit approval for ${amount:.2f}")
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        await update.message.reply_text(f"✅ Approved ${amount:.2f} deposit for user {target_user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approve <user_id> <amount>")

async def approve_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to approve withdrawals"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /approvewithdrawal <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found. Use /listusers to see registered users.")
            return
        
        if amount > user_info.get('balance', 0):
            await update.message.reply_text("❌ Insufficient user balance.")
            return
        
        user_info['balance'] = user_info.get('balance', 0) - amount
        user_info['withdrawal'] = user_info.get('withdrawal', 0) + amount
        user_info['pending_withdrawal'] = 0
        
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ Your withdrawal of ${amount:.2f} has been processed! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        await update.message.reply_text(f"✅ Approved ${amount:.2f} withdrawal for user {target_user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /approvewithdrawal <user_id> <amount>")

async def reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to reject withdrawals"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /rejectwithdrawal <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found. Use /listusers to see registered users.")
            return
        
        # Clear pending withdrawal without changing balance
        user_info['pending_withdrawal'] = 0
        
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ Your withdrawal request of ${amount:.2f} has been rejected by the admin. Please contact support for more information.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        await update.message.reply_text(f"❌ Rejected ${amount:.2f} withdrawal for user {target_user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /rejectwithdrawal <user_id> <amount>")

async def update_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update user's staked balance"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updatestake <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found.")
            return
            
        # Update staked balance
        current_stake = user_info.get('staked_balance', 0.0)
        user_info['staked_balance'] = current_stake + amount
        
        # Ensure non-negative
        if user_info['staked_balance'] < 0:
            user_info['staked_balance'] = 0.0
            
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📈 **Staked Balance Updated**\n\nYour staked balance has been updated by ${amount:.2f}.\nNew Staked Balance: ${user_info['staked_balance']:.2f}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Staking Dashboard", callback_data='stake')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
            
        await update.message.reply_text(f"✅ Updated staked balance for user {target_user_id}.\nNew Balance: ${user_info['staked_balance']:.2f}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Usage: /updatestake <user_id> <amount>")

async def release_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to release locked stake to available balance"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /releasestake <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found.")
            return
            
        locked = user_info.get('locked_stake_balance', 0.0)
        
        if amount > locked:
             await update.message.reply_text(f"❌ Amount exceeds locked balance (${locked:.2f}).")
             return

        # Move funds: Locked -> Balance
        user_info['locked_stake_balance'] = locked - amount
        user_info['balance'] += amount
            
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🔓 **Stake Released**\n\nYour stake of ${amount:.2f} has been released and added to your available balance.\n\n💰 New Available Balance: ${user_info['balance']:.2f}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
            
        await update.message.reply_text(f"✅ Released ${amount:.2f} from locked stake for user {target_user_id}.\nLocked: ${user_info['locked_stake_balance']:.2f} | Balance: ${user_info['balance']:.2f}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Usage: /releasestake <user_id> <amount>")

async def update_locked_stake(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update user's locked stake balance"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updatelocked <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found.")
            return
            
        # Update locked stake balance
        current_locked = user_info.get('locked_stake_balance', 0.0)
        user_info['locked_stake_balance'] = current_locked + amount
        
        # Ensure non-negative
        if user_info['locked_stake_balance'] < 0:
            user_info['locked_stake_balance'] = 0.0
            
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🔒 **Locked Stake Updated**\n\nYour locked stake balance has been updated by ${amount:.2f}.\nNew Locked Stake: ${user_info['locked_stake_balance']:.2f}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎯 Staking Dashboard", callback_data='stake')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
            
        await update.message.reply_text(f"✅ Updated locked stake for user {target_user_id}.\nNew Locked Stake: ${user_info['locked_stake_balance']:.2f}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Usage: /updatelocked <user_id> <amount>")

async def update_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update user profits"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updateprofit <user_id> <amount>")
            return
        
        target_user_id = int(args[0])
        amount = float(args[1])
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found. Use /listusers to see registered users.")
            return
        
        user_info['profit'] = user_info.get('profit', 0) + amount
        user_info['balance'] = user_info.get('balance', 0) + amount
        
        db.save_user(target_user_id, user_info)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 You've earned ${amount:.2f} in profits! Your new balance is ${user_info['balance']:.2f}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]])
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        await update.message.reply_text(f"✅ Added ${amount:.2f} profit for user {target_user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /updateprofit <user_id> <amount>")

async def update_crypto_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to update crypto addresses"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Usage: /updatecrypto <crypto_name> <address>")
            return
        
        crypto_name = args[0].title()
        address = args[1]
        
        from database import db
        crypto_addresses = db.get_all_crypto_addresses()
        
        if crypto_name not in crypto_addresses:
            await update.message.reply_text(
                f"❌ Crypto {crypto_name} not found. Available: {', '.join(crypto_addresses.keys())}"
            )
            return
        
        db.update_crypto_address(crypto_name, address)
        await update.message.reply_text(f"✅ Updated {crypto_name} address to: {address}")
    
    except IndexError:
        await update.message.reply_text("❌ Invalid format. Usage: /updatecrypto <crypto_name> <address>")

async def send_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to send website login details to a user"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    try:
        args = context.args
        if len(args) != 3:
            await update.message.reply_text("Usage: /sendlogin <user_id> <username> <password>")
            return
        
        target_user_id = int(args[0])
        username = args[1]
        password = args[2]
        
        from database import db
        user_info = db.get_user(target_user_id)
        
        if not user_info:
            await update.message.reply_text(f"❌ User {target_user_id} not found. Use /listusers to see registered users.")
            return
        
        login_message = f"""🌐 **Your Website Login Details**

👤 **Name:** {user_info.get('name', 'N/A')}
🆔 **User ID:** {target_user_id}
📧 **Email:** {user_info.get('email', 'N/A')}
🔐 **Username:** {username}
🔑 **Password:** {password}

Please log in at https://novacapitalwealthpro.com to access your account. Keep these details secure and do not share them."""
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=login_message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_menu')]]),
                parse_mode='Markdown'
            )
            await update.message.reply_text(f"✅ Sent login details to user {target_user_id}.")
        except TelegramError as e:
            logger.error(f"Failed to send login details to user {target_user_id}: {e}")
            await update.message.reply_text(f"❌ Failed to send login details to user {target_user_id}.")
    
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Usage: /sendlogin <user_id> <username> <password>")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list all users"""
    user_id = update.effective_user.id
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    from database import db
    user_data = db.get_all_users()
    
    if not user_data:
        await update.message.reply_text("📭 No users registered yet.")
        return
    
    users_list = """👥 **Registered Users** 👥\n\n"""
    for uid, data in user_data.items():
        status = "✅ Approved" if data.get('approved', False) else "⏳ Pending"
        bot = data.get('active_bot', 'None') if data.get('active_bot') else "None"
        pending_dep = f"${data.get('pending_deposit', 0):.2f}" if data.get('pending_deposit', 0) > 0 else "None"
        pending_with = f"${data.get('pending_withdrawal', 0):.2f}" if data.get('pending_withdrawal', 0) > 0 else "None"
        
        users_list += (
            f"🆔 **{uid}** - {data.get('name', 'N/A')}\n"
            f"📧 {data.get('email', 'N/A')}\n"
            f"📱 {data.get('phone', 'N/A')}\n"
            f"💰 Balance: ${data.get('balance', 0):.2f}\n"
            f"📈 Deposit: ${data.get('deposit', 0):.2f}\n"
            f"📊 Profit: ${data.get('profit', 0):.2f}\n"
            f"📉 Withdrawal: ${data.get('withdrawal', 0):.2f}\n"
            f"🎯 Staking Balance: ${data.get('staked_balance', 0):.2f}\n"
            f"🔒 Locked Stake: ${data.get('locked_stake_balance', 0):.2f}\n"
            f"📊 Status: {status}\n"
            f"🤖 Active Bot: {bot}\n"
            f"💳 Pending Deposit: {pending_dep}\n"
            f"💸 Pending Withdrawal: {pending_with}\n"
        )
        
        stakes = data.get('active_stakes', [])
        if stakes:
            users_list += "📋 **Active Stakes:**\n"
            for s in stakes:
                start = s.get('start_date', 'N/A')
                users_list += f"   • {s.get('coin')} | ${s.get('amount'):.2f} | {s.get('duration')} | {start}\n"
        
        users_list += "━━━━━━━━━━━━━━━━━━━\n"
    
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
    admin_id = int(context.bot_data.get('admin_id', 0))
    
    if not admin_id or user_id != admin_id:
        await update.message.reply_text("❌ Unauthorized access.")
        return
    
    help_text = """🛠 **Admin Panel Guide** 🛠

Welcome to the NCW Trading Bot Admin Panel. Below are the available commands:

👥 /listusers - List all registered users
💳 /approve <user_id> <amount> - Approve a deposit
💸 /approvewithdrawal <user_id> <amount> - Approve a withdrawal
❌ /rejectwithdrawal <user_id> <amount> - Reject a withdrawal
📈 /updateprofit <user_id> <amount> - Update user's profit
💎 /updatestake <user_id> <amount> - Update user's staking balance
🔒 /updatelocked <user_id> <amount> - Update user's locked stake balance
🔓 /releasestake <user_id> <amount> - Release stake to available balance
🪙 /updatecrypto <crypto> <address> - Update crypto address
📩 /sendlogin <user_id> <username> <password> - Send login details to user
ℹ️ /adminhelp - Show this help message"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def send_admin_panel(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send admin panel to admin on bot startup"""
    admin_id = int(context.job.data.get('admin_id', 0))
    
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
        [InlineKeyboardButton("❌ Reject Withdrawal", callback_data='admin_reject_withdrawal')],
        [InlineKeyboardButton("📈 Update Profit", callback_data='admin_update_profit')],
        [InlineKeyboardButton("💎 Update Stake Balance", callback_data='admin_update_stake')],
        [InlineKeyboardButton("🔒 Update Locked Stake", callback_data='admin_update_locked')],
        [InlineKeyboardButton("🔓 Release Stake", callback_data='admin_release_stake')],
        [InlineKeyboardButton("🪙 Update Crypto Address", callback_data='admin_update_crypto')],
        [InlineKeyboardButton("📩 Send Login Details", callback_data='admin_send_login')],
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