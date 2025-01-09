import logging
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes

# Configura il logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Regex per il contract address di Solana
solana_address_regex = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

# Funzione per recuperare il prezzo di Solana
def fetch_solana_price():
    response = requests.get('https://docs-demo.solana-mainnet.quiknode.pro/price?ids=SOL')
    data = response.json()
    return data['data'][0]['price'] if 'data' in data and len(data['data']) > 0 else None

# Funzione per recuperare le informazioni sul token
async def fetch_token_info(solana_address: str):
    response = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{solana_address}')
    return response.json()

# Funzione per formattare i numeri in modo leggibile
def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}k"
    else:
        return f"{value:.2f}"

# Funzione per validare il market cap
def validate_market_cap(market_cap):
    return market_cap > 0

# Funzione per calcolare la percentuale di profitto/perdita
def calculate_percentage_change(current_value, previous_value):
    if previous_value == 0:
        return 0
    return ((current_value - previous_value) / previous_value) * 100

# Funzione per aggiornare le informazioni sul token
async def update_info(message_id: int, chat_id: int, solana_address: str, initial_market_cap: float, context: ContextTypes.DEFAULT_TYPE) -> None:
    token_info = await fetch_token_info(solana_address)
    if 'pairs' in token_info and len(token_info['pairs']) > 0:
        pair_data = token_info['pairs'][0]
        price = f"${pair_data.get('priceUsd', 'N/A')}"
        current_market_cap_value = float(pair_data.get('marketCap', 0))

        # Mantieni fisso il market cap al momento della chiamata se non è valido
        if not validate_market_cap(current_market_cap_value):
            logging.warning(f"Invalid market cap received for {solana_address}. Keeping previous value.")
            current_market_cap_value = initial_market_cap

        current_market_cap_formatted = format_number(initial_market_cap)
        percentage_change = calculate_percentage_change(current_market_cap_value, initial_market_cap)
        change_symbol = "-" if percentage_change < 0 else "✅"
        lp = format_number(pair_data.get('liquidity', {}).get('usd', 0))
        volume = format_number(pair_data.get('volume', {}).get('h24', 0))
        coin_name = pair_data['baseToken']['name']

        new_message_text = (
            f"**Nome Coin:** {coin_name}\n"
            f"**CA:** {solana_address} [Copy](tg://sendMessage?text={solana_address})\n"
            f"📈 **Prezzo attuale:** {price}\n"
            f"💰 **Market Cap (al momento della call):** {current_market_cap_formatted} ({change_symbol}{abs(percentage_change):.2f}%)\n"
            f"💰 **Market Cap attuale:** {format_number(current_market_cap_value)}\n"
            f"💰 **Volume (24h):** {volume}\n"
            f"💧 **Liquidity Pool:** {lp}\n"
            "Clicca qui sotto per aggiornare le informazioni:\n"
        )

        # Edit message text for all users in the group chat or channel
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_message_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                InlineKeyboardButton("DexScreener", url=pair_data['url']),
                InlineKeyboardButton("🔄 Aggiorna", callback_data=f'update_{solana_address}')
            ])
        )

# Funzione per gestire i messaggi
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    message_text = update.message.text
    match = solana_address_regex.search(message_text)
    
    if match:
        solana_address = match.group(0)
        
        keyboard = [
            [InlineKeyboardButton("@SolTradingBot 🚀", url=f"https://t.me/SolTradingBot?start={solana_address}")],
            [InlineKeyboardButton("BullX🐂♉", url=f"https://bullx.io/terminal?chainId=1399811149&address={solana_address}")],
            [InlineKeyboardButton("NeoBullX🐂🎇", url=f"https://neo.bullx.io/?address={solana_address}")],
            [InlineKeyboardButton("Nova 🚀", url=f"https://t.me/TradeonNovaBot?start={solana_address}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        button_message = await update.message.reply_text("Acquista velocemente tramite bot:", reply_markup=reply_markup)

        token_info = await fetch_token_info(solana_address)
        
        if 'pairs' in token_info and len(token_info['pairs']) > 0:
            pair_data = token_info['pairs'][0]
            price = f"${pair_data.get('priceUsd', 'N/A')}"
            initial_market_cap_value = float(pair_data.get('marketCap', 0))

            # Store the initial market cap value to maintain it during updates
            context.user_data[solana_address] = {
                'initial_market_cap': initial_market_cap_value,
                'message_id': button_message.message_id,
                'chat_id': button_message.chat.id,
                'coin_name': pair_data['baseToken']['name']
            }

            initial_market_cap_formatted = format_number(initial_market_cap_value)
            lp = format_number(pair_data.get('liquidity', {}).get('usd', 0))
            volume = format_number(pair_data.get('volume', {}).get('h24', 0))

            info_message_text = (
                f"**Nome Coin:** {pair_data['baseToken']['name']}\n"
                f"**CA:** {solana_address} [Copy](tg://sendMessage?text={solana_address})\n"
                f"📈 **Prezzo attuale:** {price}\n"
                f"💰 **Market Cap (al momento della call):** {initial_market_cap_formatted} (+{abs(calculate_percentage_change(initial_market_cap_value, initial_market_cap_value)):.2f}% ✅)\n"
                f"💰 **Market Cap attuale:** {format_number(initial_market_cap_value)}\n"
                f"💰 **Volume (24h):** {volume}\n"
                f"💧 **Liquidity Pool:** {lp}\n"
                "Clicca qui sotto per aggiornare le informazioni:\n"
            )

            social_buttons_flattened = [
                InlineKeyboardButton("DexScreener", url=pair_data['url']),
                InlineKeyboardButton("🔄 Aggiorna", callback_data=f'update_{solana_address}')
            ]

            await update.message.reply_text(
                text=info_message_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([social_buttons_flattened])
            )

# Funzione per gestire i callback dei pulsanti
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer() # Rispondi al callback

    # Estrai l'indirizzo dalla callback data
    solana_address_match = re.search(r'update_(.+)', query.data)

    if solana_address_match:
        solana_address = solana_address_match.group(1)

        # Recupera il market cap iniziale memorizzato e altri dati pertinenti
        stored_data = context.user_data.get(solana_address)

        if stored_data:
            initial_market_cap_value = stored_data['initial_market_cap']
            
            # Aggiorna le informazioni del token
            await update_info(query.message.message_id, stored_data['chat_id'], solana_address, initial_market_cap_value, context)

# Funzione per gestire il comando /solana e restituire il prezzo di Solana
async def solana_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    price = fetch_solana_price()
    
    if price is not None:
        await update.message.reply_text(f"📈 Il prezzo attuale di Solana (SOL) è: **{price}** USD")
    else:
        await update.message.reply_text("⚠️ Impossibile recuperare il prezzo di Solana al momento.")

def main():
    application = ApplicationBuilder().token("6715875529:AAFPYAa6-OiEj3PEw_tuO0gMyevwiDhZnus").build()
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Aggiungi il gestore per i callback dei pulsanti usando CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Aggiungi il gestore per il comando /solana
    application.add_handler(CommandHandler("solana", solana_price))
    
    application.run_polling()

if __name__ == '__main__':
    main()
