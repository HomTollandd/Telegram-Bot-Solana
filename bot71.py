import logging
import re
import httpx  # Assicurati di installare httpx per effettuare chiamate API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Regex per identificare gli indirizzi di Solana
solana_address_regex = re.compile(r'([1-9A-HJ-NP-Za-km-z]{32,44})')

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Ciao! Mandami un Contract Address di Solana e ti aiuterò a comprarlo tramite @SolTradingBot o BullX. Usa /solana per ottenere il prezzo attuale di Solana.')

async def fetch_solana_price() -> float:
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        return data['solana']['usd']

async def solana(update: Update, context: CallbackContext) -> None:
    price = await fetch_solana_price()
    await update.message.reply_text(f"Il prezzo attuale di Solana (SOL) è: ${price:.2f}")

def format_number(value):
    """Formatta i numeri in modo leggibile."""
    if value is None or value == 'N/A':
        return "N/A"
    try:
        value = float(value)
    except ValueError:
        return "N/A"

    if value >= 1_000_000:
        return f"<b>{value / 1_000_000:.2f}M</b>"
    elif value >= 1_000:
        return f"<b>{value / 1_000:.2f}K</b>"
    else:
        return f"<b>{value}</b>"

async def fetch_token_info(token_address: str) -> dict:
    url = f'https://api.dexscreener.com/latest/dex/tokens/{token_address}'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info(f"API Response for {token_address}: {response.json()}")  # Log the full response for debugging
        return response.json()

def validate_market_cap(market_cap):
    """Controlla se il market cap è valido."""
    return market_cap > 0

def calculate_percentage_message(current_market_cap: float, initial_market_cap: float) -> str:
    """Calcola e restituisce un messaggio sulla percentuale di cambiamento."""
    percentage_change = ((current_market_cap - initial_market_cap) / initial_market_cap) * 100 if initial_market_cap > 0 else 0
    if percentage_change > 0:
        return f"(+{percentage_change:.2f}% ✅)"
    else:
        return f"({percentage_change:.2f}% ❌)"

async def update_info(message_id: int, chat_id: int, solana_address: str, initial_market_cap: float, context: CallbackContext) -> None:
    """Aggiorna le informazioni sul token."""
    token_info = await fetch_token_info(solana_address)

    if 'pairs' in token_info and len(token_info['pairs']) > 0:
        pair_data = token_info['pairs'][0]  # Prendi il primo pair
        
        price = f"${pair_data.get('priceUsd', 'N/A')}"
        
        # Controllo del market cap attuale
        current_market_cap_value = float(pair_data.get('marketCap', 0))
        
        # Se il market cap è zero o non valido, utilizza l'ultimo valore valido
        if not validate_market_cap(current_market_cap_value):
            current_market_cap_value = initial_market_cap
        
        current_market_cap_formatted = format_number(current_market_cap_value)
        lp = format_number(pair_data.get('liquidity', {}).get('usd', 0))

        # Calcola il messaggio sulla percentuale di cambiamento
        percentage_message = calculate_percentage_message(current_market_cap_value, initial_market_cap)

        # Aggiorna il messaggio con le informazioni sul token
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=(f"<b>Contract Address:</b> {solana_address}\n"
                  f"📈 Prezzo attuale: <b>{price}</b>\n"
                  f"💰 Market Cap attuale: {current_market_cap_formatted} {percentage_message}\n"
                  f"💰 Market Cap (al momento della call): {format_number(initial_market_cap)}\n"
                  f"💧 Liquidity Pool: {lp}\n"
                  "Clicca qui sotto per aggiornare le informazioni:\n"),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Aggiorna", callback_data=f'update_{solana_address}')]])
        )

async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    match = solana_address_regex.search(message_text)
    
    if match:
        solana_address = match.group(0)

        # Invia il messaggio iniziale con i bottoni
        keyboard = [
            [
                InlineKeyboardButton("🚀 Compra ora tramite @SolTradingBot 🚀", url=f"https://t.me/SolTradingBot?start={solana_address}"),
                InlineKeyboardButton("Compra ora su BullX🐂♉", url=f"https://bullx.io/terminal?chainId=1399811149&address={solana_address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the button message first
        button_message = await update.message.reply_text("Acquista velocemente tramite bot:", reply_markup=reply_markup)

        # Fetch initial token info to include in the information message
        token_info = await fetch_token_info(solana_address)
        
        if 'pairs' in token_info and len(token_info['pairs']) > 0:
            pair_data = token_info['pairs'][0]
            
            price = f"${pair_data.get('priceUsd', 'N/A')}"
            initial_market_cap_value = float(pair_data.get('marketCap', 0))
            
            # Controllo del market cap iniziale
            if not validate_market_cap(initial_market_cap_value):
                initial_market_cap_value = 0.0
            
            initial_market_cap_formatted = format_number(initial_market_cap_value)
            lp = format_number(pair_data.get('liquidity', {}).get('usd', 0))

            # Salva l'informazione iniziale nel contesto
            context.user_data['initial_market_cap'] = initial_market_cap_value

            # Invia il messaggio con le informazioni sul token e il bottone di aggiornamento
            info_message = await update.message.reply_text(
                f"<b>Contract Address:</b> {solana_address}\n"
                f"📈 Prezzo attuale: <b>{price}</b>\n"
                f"💰 Market Cap attuale: {initial_market_cap_formatted}\n"
                f"💰 Market Cap (al momento della call): {format_number(initial_market_cap_value)}\n"
                f"💧 Liquidity Pool: {lp}\n"
                "Clicca qui sotto per aggiornare le informazioni:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Aggiorna", callback_data=f'update_{solana_address}')]])
            )

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data.startswith('update_'):
        solana_address = query.data.split('_')[1]
        
        # Recupera l'informazione iniziale dal contesto
        initial_market_cap = context.user_data.get('initial_market_cap', 0)

        # Update the information message with the latest data without cooldown
        await update_info(query.message.message_id, query.message.chat.id, solana_address, initial_market_cap, context)

async def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main() -> None:
    token = '6715875529:AAG2NbGFsBhO0Eg4GvGR-yInlWIg-siU5D0'  # Token del bot

    # Creazione dell'applicazione
    application = Application.builder().token(token).build()

    # Aggiunta dei gestori
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("solana", solana))  # Aggiungi il comando /solana
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handler per i pulsanti di aggiornamento
    application.add_handler(CallbackQueryHandler(button_handler))  
    
    application.add_error_handler(error)

    # Avvio del bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()