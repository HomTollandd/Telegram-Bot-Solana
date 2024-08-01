# made with love <3 by @uzivelt

import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Regex per identificare gli indirizzi di Solana
solana_address_regex = re.compile(r'([1-9A-HJ-NP-Za-km-z]{32,44})')

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Ciao! Mandami un Contract Address di Solana e ti aiuterò a comprarlo tramite @SolTradingBot')

async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    match = solana_address_regex.search(message_text)
    if match:
        solana_address = match.group(0)
        keyboard = [
            [
                InlineKeyboardButton("🚀 Compra ora tramite @SolTradingBot 🚀", url=f"https://t.me/SolTradingBot?start={solana_address}"),
                InlineKeyboardButton("Compra ora su BullX♉", url=f"https://bullx.io/terminal?chainId=1399811149&address={solana_address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await asyncio.sleep(2.2)  # Delay di 2.3 secondi
        await update.message.reply_text(f"Rilevato un nuovo Contract Address✅: {solana_address} ", reply_markup=reply_markup)
    # Non invia alcun messaggio se l'indirizzo non è valido

async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    token = '6715875529:AAG2NbGFsBhO0Eg4GvGR-yInlWIg-siU5D0'  # Token del bot

    # Creazione dell'applicazione
    application = Application.builder().token(token).build()

    # Aggiunta dei gestori
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)

    # Avvio del bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
