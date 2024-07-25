#made with love <3 by @uzivelt

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Regex per identificare gli indirizzi di Solana
solana_address_regex = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Ciao! Mandami un Contract Address di Solana e ti aiuterò a comprarlo tramite @SolTradingBot')

async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    if solana_address_regex.match(message_text):
        keyboard = [
            [
                InlineKeyboardButton("🚀 Compra ora tramite @SolTradingBot 🚀", url=f"https://t.me/SolTradingBot?start={message_text}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Rilevato un nuovo Contract Address✅: {message_text} ", reply_markup=reply_markup)
    # Non invia alcun messaggio se l'indirizzo non è valido

async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    token = 'xxxx'  # Token del bot

    # Creazione dell'applicazione
    application = Application.builder().token(token).build()

    # Aggiunta dei gestori
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)

    # Avvio del bot
    application.run_polling()

if __name__ == '__main__':
    main()
