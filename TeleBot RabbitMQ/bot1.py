import logging
from typing import Final
from json import dumps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import pika

# RabbitMQ connection 
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_QUEUE = 'telebot'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
channel = connection.channel()
channel.queue_declare(queue=RABBITMQ_QUEUE)

TOKEN: Final = '6464310280:AAE88MhpwS4KvJKqPn3lGKHr664EwPp77Pc'  
BOT_USERNAME: Final = 'TeleTest86bot' 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

bold_text = '* Welcome to TeleTestBot *'

SELECTING_ACTION, TYPING_REPLY, LOGIN_USERNAME, LOGIN_PASSWORD = range(4)

# Buttons
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Buy", callback_data='buy')],
        [InlineKeyboardButton("Sell & Manage", callback_data='sell_manage')],
        [InlineKeyboardButton("Help", callback_data='help'),
         InlineKeyboardButton("Refer Friends", callback_data='refer_friends')],
        [InlineKeyboardButton("Alerts", callback_data='alerts')],
        [InlineKeyboardButton("Creator Login", callback_data='clogin')],
        [InlineKeyboardButton("Wallet", callback_data='wallet'),
         InlineKeyboardButton("Settings", callback_data='settings')],
        [InlineKeyboardButton("Pin", callback_data='pin'),
         InlineKeyboardButton("Refresh", callback_data='refresh')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(bold_text + "\n\n One of the best bots to trade in Telegram", reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Help section, please type something.')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command.')

async def xtg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('XTG Technologies is a leading IT firm based in Kochi')

# Responses
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'
    if 'how are you' in processed:
        return 'I am good!'
    return 'No idea.'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    print('Bot:', response)
    await update.message.reply_text(response)


#Button Responses
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        cncl = InlineKeyboardButton("Cancel", callback_data='cancel')
        
        reply_markup  = InlineKeyboardMarkup([[cncl]])

        await query.message.reply_text("WHICH STOCK TO BUY ? [ETH/USDT]" , reply_markup=reply_markup)
        return SELECTING_ACTION

    if query.data == "sell_manage":
        await query.message.reply_text("You clicked SELL & MANAGE button!")

    if query.data == "help":
        await query.message.reply_text("You clicked Help button!")

    if query.data == "refer_friends":
        await query.message.reply_text("You clicked Refer Friends button!")

    if query.data == "alerts":
        await query.message.reply_text("You clicked Alerts button!")

    if query.data == "clogin":
        await query.message.reply_text("Please enter your username:")
        return LOGIN_USERNAME

    if query.data == "wallet":
        await query.message.reply_text("You clicked Wallet button!")

    if query.data == "settings":
        await query.message.reply_text("You clicked Settings button!")

    if query.data == "pin":
        await query.message.reply_text("You clicked PIN button!")

    if query.data == "refresh":
        await query.message.reply_text("You clicked Refresh button!")

    if query.data == "cancel":
        await cancel(update, context)
        return ConversationHandler.END

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['username'] = update.message.text
    await update.message.reply_text("Please enter your password:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['password'] = update.message.text
    username = context.user_data['username']
    password = context.user_data['password']

    
    await update.message.reply_text(f"SUCESSFULLY LOGGED IN \n\n  USERNAME: {username} \n PASSWORD: {password}", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def select_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()

    if text in ['ETH', 'USDT']:
        context.user_data['stock'] = text
        cncl = InlineKeyboardButton("Cancel", callback_data='cancel')
        
        d = InlineKeyboardMarkup([[cncl]])
        await update.message.reply_text(f"You selected {text}. Please specify the quantity:", reply_markup=d)
        return TYPING_REPLY
    else:
        await update.message.reply_text("Please choose a valid option: ETH or USDT")
        return SELECTING_ACTION

async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity = update.message.text
    try:
        quantity = float(quantity)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the quantity:")
        return TYPING_REPLY

    stock = context.user_data.get('stock')
    data = {'stock': stock, 'quantity': quantity}

    message = dumps(data)

    # Sending message to RabbitMQ
    channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=message)
    
    await update.message.reply_text(f"You bought {quantity} units of {stock}.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info('Cancel button pressed.')

    if update.callback_query:
        await update.callback_query.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    elif update.message:
        await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    else:
        logger.error("No valid update found for cancelling.")

    return ConversationHandler.END

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('xtg', xtg_command))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern='buy|clogin')],
        states={
            SELECTING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_stock)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_quantity)],
            LOGIN_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)]
        },
        fallbacks=[CallbackQueryHandler(button_click, pattern='cancel')],
        allow_reentry=True
    )
    app.add_handler(conv_handler)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(button_click))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
