import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError
import random
import string
import asyncio

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and admin ID from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

# Simulated user database (in-memory dictionary for simplicity)
users = {}

# States for ConversationHandler
(
    FULLNAME,
    EMAIL,
    PHONE,
    ADDRESS,
    DEPOSIT_AMOUNT,
    DEPOSIT_PROOF,
    WITHDRAW_AMOUNT,
    WITHDRAW_ADDRESS,
    COPY_TRADE_AMOUNT,
) = range(9)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features. Use admin commands like /listusers or the admin panel.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Welcome to NCW Trading Bot! Please provide your full name to register."
    )
    return FULLNAME

async def get_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    context.user_data["fullname"] = update.message.text
    await update.message.reply_text("Please provide your email address.")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Please provide your phone number.")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Please provide your wallet address.")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    context.user_data["address"] = update.message.text
    user_data = {
        "fullname": context.user_data["fullname"],
        "email": context.user_data["email"],
        "phone": context.user_data["phone"],
        "address": context.user_data["address"],
        "balance": 0.0,
        "status": "pending",
    }
    users[user_id] = user_data
    await update.message.reply_text(
        "Registration complete! Your account is pending approval by the admin."
    )
    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"New user registration:\n"
                 f"User ID: {user_id}\n"
                 f"Name: {user_data['fullname']}\n"
                 f"Email: {user_data['email']}\n"
                 f"Phone: {user_data['phone']}\n"
                 f"Address: {user_data['address']}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Approve", callback_data=f"approve_user_{user_id}"
                        ),
                        InlineKeyboardButton(
                            "Reject", callback_data=f"reject_user_{user_id}"
                        ),
                    ]
                ]
            ),
        )
    except TelegramError as e:
        logger.error(f"Failed to send registration notification to admin: {e}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your Telegram User ID is: {user_id}")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features. Use admin commands like /listusers or the admin panel.")
        return
    if user_id not in users or users[user_id]["status"] != "approved":
        await update.message.reply_text(
            "You are not registered or your account is not approved yet."
        )
        return
    keyboard = [
        [
            InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        ],
        [InlineKeyboardButton("📈 Copy Trade", callback_data="copy_trade")],
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data="refresh_balance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Welcome back, {users[user_id]['fullname']}!\nYour current balance: ${users[user_id]['balance']:.2f}",
        reply_markup=reply_markup,
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id == ADMIN_USER_ID and data in ["deposit", "withdraw", "copy_trade", "refresh_balance", "back_to_menu"]:
        await query.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END

    if data == "deposit":
        if user_id not in users or users[user_id]["status"] != "approved":
            await query.message.reply_text("Your account is not approved yet.")
            return ConversationHandler.END
        await query.message.reply_text("Please enter the deposit amount (in USD):")
        return DEPOSIT_AMOUNT
    elif data == "withdraw":
        if user_id not in users or users[user_id]["status"] != "approved":
            await query.message.reply_text("Your account is not approved yet.")
            return ConversationHandler.END
        await query.message.reply_text("Please enter the amount to withdraw (in USD):")
        return WITHDRAW_AMOUNT
    elif data == "copy_trade":
        if user_id not in users or users[user_id]["status"] != "approved":
            await query.message.reply_text("Your account is not approved yet.")
            return ConversationHandler.END
        await query.message.reply_text("Please enter the amount for copy trading (in USD):")
        return COPY_TRADE_AMOUNT
    elif data == "refresh_balance":
        if user_id not in users or users[user_id]["status"] != "approved":
            await query.message.reply_text("Your account is not approved yet.")
            return ConversationHandler.END
        await query.message.reply_text(
            f"Your current balance: ${users[user_id]['balance']:.2f}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
            ),
        )
        return ConversationHandler.END
    elif data == "back_to_menu":
        if user_id not in users or users[user_id]["status"] != "approved":
            await query.message.reply_text("Your account is not approved yet.")
            return ConversationHandler.END
        keyboard = [
            [
                InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
                InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
            ],
            [InlineKeyboardButton("📈 Copy Trade", callback_data="copy_trade")],
            [InlineKeyboardButton("🔄 Refresh Balance", callback_data="refresh_balance")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            f"Welcome back, {users[user_id]['fullname']}!\nYour current balance: ${users[user_id]['balance']:.2f}",
            reply_markup=reply_markup,
        )
        return ConversationHandler.END
    elif data.startswith("approve_user_"):
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("Only admins can approve users.")
            return ConversationHandler.END
        target_user_id = int(data.split("_")[2])
        if target_user_id in users:
            users[target_user_id]["status"] = "approved"
            await query.message.reply_text(f"User {target_user_id} approved.")
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="Your account has been approved! Use /menu to access features.",
                )
            except TelegramError as e:
                logger.error(f"Failed to notify user {target_user_id}: {e}")
        else:
            await query.message.reply_text("User not found.")
        return ConversationHandler.END
    elif data.startswith("reject_user_"):
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("Only admins can reject users.")
            return ConversationHandler.END
        target_user_id = int(data.split("_")[2])
        if target_user_id in users:
            del users[target_user_id]
            await query.message.reply_text(f"User {target_user_id} rejected and removed.")
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="Your registration was rejected by the admin.",
                )
            except TelegramError as e:
                logger.error(f"Failed to notify user {target_user_id}: {e}")
        else:
            await query.message.reply_text("User not found.")
        return ConversationHandler.END
    elif data.startswith("approve_deposit_"):
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("Only admins can approve deposits.")
            return ConversationHandler.END
        parts = data.split("_")
        target_user_id = int(parts[2])
        amount = float(parts[3])
        if target_user_id not in users:
            await query.message.reply_text("User not found.")
            return ConversationHandler.END
        users[target_user_id]["balance"] += amount
        await query.message.reply_text(
            f"Deposit of ${amount:.2f} approved for User ID: {target_user_id}"
        )
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Your deposit of ${amount:.2f} has been approved. New balance: ${users[target_user_id]['balance']:.2f}",
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        return ConversationHandler.END
    elif data.startswith("reject_deposit_"):
        if user_id != ADMIN_USER_ID:
            await query.message.reply_text("Only admins can reject deposits.")
            return ConversationHandler.END
        target_user_id = int(data.split("_")[2])
        if target_user_id not in users:
            await query.message.reply_text("User not found.")
            return ConversationHandler.END
        await query.message.reply_text(f"Deposit rejected for User ID: {target_user_id}")
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="Your deposit request was rejected by the admin.",
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        return ConversationHandler.END
    return ConversationHandler.END

async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return DEPOSIT_AMOUNT
        context.user_data["deposit_amount"] = amount
        await update.message.reply_text(
            "Please upload a screenshot of your payment proof."
        )
        return DEPOSIT_PROOF
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return DEPOSIT_AMOUNT

async def get_deposit_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    if not update.message.photo:
        await update.message.reply_text("Please upload an image as proof of payment.")
        return DEPOSIT_PROOF
    photo = update.message.photo[-1]
    context.user_data["deposit_proof"] = photo.file_id
    amount = context.user_data["deposit_amount"]
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"New deposit request from User ID: {user_id}\n"
                 f"Name: {users[user_id]['fullname']}\n"
                 f"Amount: ${amount:.2f}",
        )
        await context.bot.send_photo(
            chat_id=ADMIN_USER_ID,
            photo=photo.file_id,
            caption="Payment proof",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Approve", callback_data=f"approve_deposit_{user_id}_{amount}"
                        ),
                        InlineKeyboardButton(
                            "Reject", callback_data=f"reject_deposit_{user_id}"
                        ),
                    ]
                ]
            ),
        )
        await update.message.reply_text(
            "Your deposit request has been sent to the admin for approval."
        )
    except TelegramError as e:
        logger.error(f"Failed to send deposit notification to admin: {e}")
        await update.message.reply_text(
            "Failed to send deposit request. Please try again later."
        )
    return ConversationHandler.END

async def get_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return WITHDRAW_AMOUNT
        if amount > users[user_id]["balance"]:
            await update.message.reply_text("Insufficient balance.")
            return ConversationHandler.END
        context.user_data["withdraw_amount"] = amount
        await update.message.reply_text("Please enter your withdrawal wallet address.")
        return WITHDRAW_ADDRESS
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return WITHDRAW_AMOUNT

async def get_withdraw_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    address = update.message.text
    amount = context.user_data["withdraw_amount"]
    users[user_id]["balance"] -= amount
    await update.message.reply_text(
        f"Withdrawal of ${amount:.2f} to {address} processed successfully."
    )
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"Withdrawal request processed:\n"
                 f"User ID: {user_id}\n"
                 f"Name: {users[user_id]['fullname']}\n"
                 f"Amount: ${amount:.2f}\n"
                 f"Address: {address}",
        )
    except TelegramError as e:
        logger.error(f"Failed to notify admin about withdrawal: {e}")
    return ConversationHandler.END

async def get_copy_trade_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return ConversationHandler.END
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Please enter a positive amount.")
            return COPY_TRADE_AMOUNT
        if amount > users[user_id]["balance"]:
            await update.message.reply_text("Insufficient balance.")
            return ConversationHandler.END
        users[user_id]["balance"] -= amount
        profit = amount * random.uniform(0.05, 0.2)  # Simulated profit (5-20%)
        users[user_id]["balance"] += amount + profit
        await update.message.reply_text(
            f"Copy trade of ${amount:.2f} completed. Profit: ${profit:.2f}. New balance: ${users[user_id]['balance']:.2f}"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=f"Copy trade completed:\n"
                     f"User ID: {user_id}\n"
                     f"Name: {users[user_id]['fullname']}\n"
                     f"Amount: ${amount:.2f}\n"
                     f"Profit: ${profit:.2f}",
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin about copy trade: {e}")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a number.")
        return COPY_TRADE_AMOUNT

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Only admins can list users.")
        return
    if not users:
        await update.message.reply_text("No registered users.")
        return
    user_list = "\n".join(
        f"ID: {uid}, Name: {data['fullname']}, Status: {data['status']}, Balance: ${data['balance']:.2f}"
        for uid, data in users.items()
    )
    await update.message.reply_text(f"Registered users:\n{user_list}")

async def approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Only admins can approve deposits.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /approve <user_id> <amount>")
        return
    try:
        target_user_id = int(args[0])
        amount = float(args[1])
        if target_user_id not in users:
            await update.message.reply_text("User not found.")
            return
        if amount <= 0:
            await update.message.reply_text("Amount must be positive.")
            return
        users[target_user_id]["balance"] += amount
        await update.message.reply_text(
            f"Deposit of ${amount:.2f} approved for User ID: {target_user_id}"
        )
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Your deposit of ${amount:.2f} has been approved. New balance: ${users[target_user_id]['balance']:.2f}",
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid user ID or amount.")

async def admin_panel_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_USER_ID:
        await query.message.reply_text("Only admins can access the admin panel.")
        return
    data = query.data
    if data == "list_users":
        if not users:
            await query.message.reply_text("No registered users.")
            return
        user_list = "\n".join(
            f"ID: {uid}, Name: {data['fullname']}, Status: {data['status']}, Balance: ${data['balance']:.2f}"
            for uid, data in users.items()
        )
        await query.message.reply_text(f"Registered users:\n{user_list}")
    elif data == "approve_deposit":
        await query.message.reply_text("Please enter: /approve <user_id> <amount>")
    elif data == "back_to_admin_menu":
        keyboard = [
            [InlineKeyboardButton("📋 List Users", callback_data="list_users")],
            [InlineKeyboardButton("✅ Approve Deposit", callback_data="approve_deposit")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Admin Panel", reply_markup=reply_markup)

async def send_admin_panel(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        keyboard = [
            [InlineKeyboardButton("📋 List Users", callback_data="list_users")],
            [InlineKeyboardButton("✅ Approve Deposit", callback_data="approve_deposit")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text="Admin Panel",
            reply_markup=reply_markup,
        )
    except TelegramError as e:
        logger.error(f"Failed to send admin panel: {e}")

async def get_crypto_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Admins cannot access user features.")
        return
    if user_id not in users or users[user_id]["status"] != "approved":
        await update.message.reply_text("Your account is not approved yet.")
        return
    # Simulated wallet address generation
    wallet_address = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=34)
    )
    await update.message.reply_text(
        f"Your crypto wallet address for deposits:\n`{wallet_address}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_menu")]]
        ),
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred. Please try again later."
        )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.job_queue.run_once(send_admin_panel, 1)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fullname)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_deposit_amount)
            ],
            DEPOSIT_PROOF: [
                MessageHandler(filters.PHOTO, get_deposit_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_deposit_proof),
            ],
            WITHDRAW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_withdraw_amount)
            ],
            WITHDRAW_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_withdraw_address)
            ],
            COPY_TRADE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_copy_trade_amount)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("getid", get_id))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("listusers", list_users))
    application.add_handler(CommandHandler("approve", approve_deposit))
    application.add_handler(CommandHandler("getaddress", get_crypto_address))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(admin_panel_button, pattern="^(list_users|approve_deposit|back_to_admin_menu)$"))
    application.add_error_handler(error_handler)
    logger.info("Starting NCW Trading Bot...")
    application.run_polling(timeout=30)

if __name__ == "__main__":
    main()