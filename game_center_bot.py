import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

load_dotenv()

# In-memory storage (replace with database in production)
users: Dict[int, Dict] = {}
games: Dict[str, Dict] = {}
scores: Dict[int, List[Dict]] = {}
reservations: Dict[int, List[Dict]] = {}
tournaments: Dict[str, Dict] = {}
tournament_participants: Dict[str, List[int]] = {}
tournament_scores: Dict[str, List[Dict]] = {}
payment_receipts: List[Dict] = []
admin_ids = [123456789]  # Replace with actual admin IDs

# Sample games data - Popular PS4 Games
games_data = {
    "godofwar": {"name": "God of War", "category": "Action-Adventure", "price": "60,000 Toman/hour"},
    "spiderman": {"name": "Spider-Man", "category": "Action-Adventure", "price": "60,000 Toman/hour"},
    "rdr2": {"name": "Red Dead Redemption 2", "category": "Action-Adventure", "price": "70,000 Toman/hour"},
    "horizon": {"name": "Horizon Zero Dawn", "category": "Action-Adventure", "price": "60,000 Toman/hour"},
    "uncharted4": {"name": "Uncharted 4", "category": "Action-Adventure", "price": "60,000 Toman/hour"},
    "lastofus2": {"name": "The Last of Us Part II", "category": "Action-Adventure", "price": "70,000 Toman/hour"},
    "gta5": {"name": "GTA V", "category": "Action", "price": "55,000 Toman/hour"},
    "fifa24": {"name": "FIFA 24", "category": "Sports", "price": "50,000 Toman/hour"},
    "pes24": {"name": "eFootball 24", "category": "Sports", "price": "50,000 Toman/hour"},
    "cod": {"name": "Call of Duty: Modern Warfare", "category": "Shooter", "price": "65,000 Toman/hour"},
    "fortnite": {"name": "Fortnite", "category": "Battle Royale", "price": "40,000 Toman/hour"},
    "minecraft": {"name": "Minecraft", "category": "Sandbox", "price": "45,000 Toman/hour"},
    "nba2k": {"name": "NBA 2K24", "category": "Sports", "price": "50,000 Toman/hour"},
    "nfs": {"name": "Need for Speed", "category": "Racing", "price": "55,000 Toman/hour"},
    "wwe": {"name": "WWE 2K24", "category": "Fighting", "price": "50,000 Toman/hour"}
}

# Sample tournaments data
tournaments_data = {
    "fifa_cup": {
        "name": "FIFA 24 کاپ هفتگی",
        "game": "fifa24",
        "game_name": "FIFA 24",
        "start_date": "2026-11-15 18:00",
        "end_date": "2026-11-15 22:00",
        "max_participants": 16,
        "current_participants": 0,
        "prize": "500,000 تومان",
        "entry_fee": "20,000 تومان",
        "status": "open",
        "description": "تورنمنت FIFA 24 - فرمت حذفی"
    },
    "cod_tournament": {
        "name": "Call of Duty Championship",
        "game": "cod",
        "game_name": "Call of Duty",
        "start_date": "2026-11-16 20:00",
        "end_date": "2026-11-16 23:00",
        "max_participants": 32,
        "current_participants": 0,
        "prize": "1,000,000 تومان",
        "entry_fee": "30,000 تومان",
        "status": "open",
        "description": "تورنمنت Call of Duty - فرمت تیمی"
    },
    "fortnite_battle": {
        "name": "Fortnite Battle Royale",
        "game": "fortnite",
        "game_name": "Fortnite",
        "start_date": "2026-11-17 19:00",
        "end_date": "2026-11-17 21:00",
        "max_participants": 50,
        "current_participants": 0,
        "prize": "750,000 تومان",
        "entry_fee": "15,000 تومان",
        "status": "open",
        "description": "تورنمنت Fortnite - Solo"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Initialize user"""
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {
            "name": update.effective_user.first_name,
            "username": update.effective_user.username,
            "balance": 0,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        scores[user_id] = []
        reservations[user_id] = []

    await show_main_menu_text(update, user_id)

async def show_main_menu_text(update: Update, user_id: int):
    """Show main menu with new message"""
    keyboard = [
        [InlineKeyboardButton("🎮 بازی‌ها", callback_data="games")],
        [InlineKeyboardButton("🏆 تورنمنت‌ها", callback_data="tournaments")],
        [InlineKeyboardButton("📊 امتیازات من", callback_data="scores")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile")],
        [InlineKeyboardButton("📅 رزرو وقت", callback_data="reserve")],
        [InlineKeyboardButton("💰 افزایش موجودی", callback_data="deposit")]
    ]

    # Add admin button if user is admin
    if user_id in admin_ids:
        keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")])

    keyboard.append([InlineKeyboardButton("🔔 اطلاع‌رسانی", callback_data="notifications")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎮 خوش آمدید به گیم سنتر!\n\n"
        f"کاربر: {users[user_id]['name']}\n"
        f"موجودی: {users[user_id]['balance']:,} تومان\n\n"
        f"لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_main_menu(query, user_id: int):
    """Show main menu by editing existing message"""
    keyboard = [
        [InlineKeyboardButton("🎮 بازی‌ها", callback_data="games")],
        [InlineKeyboardButton("🏆 تورنمنت‌ها", callback_data="tournaments")],
        [InlineKeyboardButton("📊 امتیازات من", callback_data="scores")],
        [InlineKeyboardButton("👤 پروفایل", callback_data="profile")],
        [InlineKeyboardButton("📅 رزرو وقت", callback_data="reserve")],
        [InlineKeyboardButton("💰 افزایش موجودی", callback_data="deposit")]
    ]

    # Add admin button if user is admin
    if user_id in admin_ids:
        keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")])

    keyboard.append([InlineKeyboardButton("🔔 اطلاع‌رسانی", callback_data="notifications")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🎮 خوش آمدید به گیم سنتر!\n\n"
        f"کاربر: {users[user_id]['name']}\n"
        f"موجودی: {users[user_id]['balance']:,} تومان\n\n"
        f"لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # Initialize user if not exists
    if user_id not in users:
        users[user_id] = {
            "name": query.from_user.first_name,
            "username": query.from_user.username,
            "balance": 0,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        scores[user_id] = []
        reservations[user_id] = []

    if data == "start":
        await show_main_menu(query, user_id)
    elif data == "games":
        await show_games(query)
    elif data == "tournaments":
        await show_tournaments(query)
    elif data == "scores":
        await show_scores(query, user_id)
    elif data == "profile":
        await show_profile(query, user_id)
    elif data == "reserve":
        await show_reservation_menu(query)
    elif data == "deposit":
        await show_deposit_menu(query)
    elif data == "notifications":
        await show_notifications(query)
    elif data == "admin_panel":
        if user_id in admin_ids:
            await show_admin_panel(query)
        else:
            try:
                await query.edit_message_text("⚠️ دسترسی غیرمجاز")
            except:
                await query.message.reply_text("⚠️ دسترسی غیرمجاز")
    elif data.startswith("game_"):
        game_id = data.split("_")[1]
        await show_game_details(query, game_id)
    elif data.startswith("select_game_"):
        game_id = data.split("_")[2]
        await select_game_for_reservation(query, game_id)
    elif data.startswith("time_"):
        parts = data.split("_")
        game_id = parts[1]
        hours_from_now = int(parts[2])
        await select_duration(query, game_id, hours_from_now)
    elif data.startswith("duration_"):
        parts = data.split("_")
        game_id = parts[1]
        hours_from_now = int(parts[2])
        duration = int(parts[3])
        await reserve_game_with_time_and_duration(query, user_id, game_id, hours_from_now, duration)
    elif data == "my_reservations":
        await show_my_reservations(query, user_id)
    elif data.startswith("cancel_"):
        reservation_index = int(data.split("_")[1])
        await cancel_reservation(query, user_id, reservation_index)
    elif data.startswith("confirm_cancel_"):
        reservation_index = int(data.split("_")[2])
        await confirm_cancel_reservation(query, user_id, reservation_index)
    elif data.startswith("tournament_"):
        tournament_id = data.split("_")[1]
        await show_tournament_details(query, tournament_id)
    elif data.startswith("join_"):
        tournament_id = data.split("_")[1]
        await join_tournament(query, user_id, tournament_id)
    elif data == "my_tournaments":
        await show_my_tournaments(query, user_id)
    elif data == "send_receipt":
        await show_receipt_instructions(query)
    elif data.startswith("approve_"):
        receipt_id = int(data.split("_")[1])
        await approve_receipt(query, receipt_id)
    elif data.startswith("reject_"):
        receipt_id = int(data.split("_")[1])
        await reject_receipt(query, receipt_id)
    elif data == "admin_users":
        await show_admin_users(query)
    elif data == "admin_reservations":
        await show_admin_reservations(query)
    elif data == "admin_receipts":
        await show_admin_receipts(query)

async def show_games(query):
    """Show available games"""
    text = "🎮 بازی‌های موجود:\n\n"
    keyboard = []

    for game_id, game in games_data.items():
        text += f"• {game['name']} ({game['category']})\n"
        text += f"  قیمت: {game['price']}\n\n"
        keyboard.append([InlineKeyboardButton(f"🎯 {game['name']}", callback_data=f"game_{game_id}")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_game_details(query, game_id):
    """Show game details"""
    game = games_data.get(game_id)
    if not game:
        try:
            await query.edit_message_text("بازی یافت نشد.")
        except:
            await query.message.reply_text("بازی یافت نشد.")
        return

    text = f"🎮 {game['name']}\n\n"
    text += f"دسته‌بندی: {game['category']}\n"
    text += f"قیمت: {game['price']}\n\n"
    text += "آیا می‌خواهید رزرو کنید؟"

    keyboard = [
        [InlineKeyboardButton("✅ رزرو وقت", callback_data=f"select_game_{game_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="games")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_scores(query, user_id):
    """Show user's scores"""
    user_scores = scores.get(user_id, [])

    if not user_scores:
        text = "📊 هنوز امتیازی ثبت نشده است.\n\n"
        text += "برای ثبت امتیاز، فرمت زیر را ارسال کنید:\n"
        text += "/score بازی_نام امتیاز"
    else:
        text = "📊 امتیازات شما:\n\n"
        for idx, score in enumerate(user_scores[-10:], 1):
            text += f"{idx}. {score['game']}: {score['score']} ({score['date']})\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_profile(query, user_id):
    """Show user profile"""
    user = users.get(user_id, {})
    user_reservations = reservations.get(user_id, [])

    # Count user's tournaments
    user_tournament_count = 0
    for participants in tournament_participants.values():
        if user_id in participants:
            user_tournament_count += 1

    text = f"👤 پروفایل کاربری\n\n"
    text += f"نام: {user.get('name', 'N/A')}\n"
    text += f"یوزرنیم: @{user.get('username', 'N/A')}\n"
    text += f"موجودی: {user.get('balance', 0):,} تومان\n"
    text += f"تاریخ عضویت: {user.get('joined', 'N/A')}\n"
    text += f"تعداد رزرو: {len(user_reservations)}\n"
    text += f"تعداد تورنمنت: {user_tournament_count}\n"

    keyboard = [
        [InlineKeyboardButton("📅 رزروهای من", callback_data="my_reservations")],
        [InlineKeyboardButton("📋 تورنمنت‌های من", callback_data="my_tournaments")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_reservation_menu(query):
    """Show reservation menu"""
    text = "📅 رزرو وقت\n\n"
    text += "ابتدا بازی مورد نظر را انتخاب کنید:"

    keyboard = []
    for game_id, game in games_data.items():
        keyboard.append([InlineKeyboardButton(f"🎮 {game['name']}", callback_data=f"select_game_{game_id}")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def select_game_for_reservation(query, game_id):
    """Select game and show time slots"""
    game = games_data.get(game_id)
    if not game:
        try:
            await query.edit_message_text("بازی یافت نشد.")
        except:
            await query.message.reply_text("بازی یافت نشد.")
        return

    text = f"🎮 {game['name']}\n\n"
    text += f"قیمت: {game['price']}\n\n"
    text += "⏰ زمان شروع را انتخاب کنید (24 ساعت آینده):"

    keyboard = []
    now = datetime.now()

    # Create time slots for next 24 hours (every 2 hours for better UX)
    for hour in range(0, 24, 2):
        slot_time = now + timedelta(hours=hour)
        time_str = slot_time.strftime("%H:%M")
        date_str = slot_time.strftime("%Y-%m-%d")
        callback_data = f"time_{game_id}_{hour}"

        if hour == 0:
            display_time = f"همین حالا ({time_str})"
        else:
            display_time = f"{hour} ساعت بعد ({time_str})"

        keyboard.append([InlineKeyboardButton(f"🕐 {display_time}", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت به بازی‌ها", callback_data="reserve")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def select_duration(query, game_id, hours_from_now):
    """Select duration for reservation"""
    game = games_data.get(game_id)
    if not game:
        try:
            await query.edit_message_text("بازی یافت نشد.")
        except:
            await query.message.reply_text("بازی یافت نشد.")
        return

    start_time = datetime.now() + timedelta(hours=hours_from_now)
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M")

    text = f"🎮 {game['name']}\n\n"
    text += f"⏰ زمان شروع: {start_time_str}\n"
    text += f"💰 قیمت ساعت: {game['price']}\n\n"
    text += "⏱️ مدت زمان رزرو را انتخاب کنید:"

    keyboard = []
    durations = [1, 2, 3, 4, 5, 6, 8, 10, 12]

    for duration in durations:
        callback_data = f"duration_{game_id}_{hours_from_now}_{duration}"
        keyboard.append([InlineKeyboardButton(f"⏱️ {duration} ساعت", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت به انتخاب زمان", callback_data=f"select_game_{game_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def reserve_game_with_time_and_duration(query, user_id, game_id, hours_from_now, duration):
    """Reserve a game with specific time and duration"""
    game = games_data.get(game_id)
    if not game:
        try:
            await query.edit_message_text("بازی یافت نشد.")
        except:
            await query.message.reply_text("بازی یافت نشد.")
        return

    # Calculate reservation time
    start_time = datetime.now() + timedelta(hours=hours_from_now)
    end_time = start_time + timedelta(hours=duration)

    # Extract price and calculate total
    price_str = game['price']
    try:
        price_per_hour = int(price_str.replace(',', '').replace(' Toman/hour', '').replace(' Toman', '').strip())
        total_price = price_per_hour * duration
        total_price_str = f"{total_price:,} تومان"
    except:
        total_price_str = f"{price_str} × {duration} ساعت"

    reservation = {
        "game": game['name'],
        "game_id": game_id,
        "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
        "duration": duration,
        "price_per_hour": game['price'],
        "total_price": total_price_str,
        "status": "confirmed"
    }

    if user_id not in reservations:
        reservations[user_id] = []

    reservations[user_id].append(reservation)

    text = f"✅ رزرو با موفقیت انجام شد!\n\n"
    text += f"🎮 بازی: {game['name']}\n"
    text += f"📅 تاریخ: {start_time.strftime('%Y-%m-%d')}\n"
    text += f"⏰ زمان شروع: {start_time.strftime('%H:%M')}\n"
    text += f"⏰ زمان پایان: {end_time.strftime('%H:%M')}\n"
    text += f"⏱️ مدت: {duration} ساعت\n"
    text += f"💰 قیمت هر ساعت: {game['price']}\n"
    text += f"💰 جمع کل: {total_price_str}\n"
    text += f"✅ وضعیت: تایید شده\n\n"
    text += "⚠️ لطفاً ۵ دقیقه قبل از زمان شروع حضور پیدا کنید."

    keyboard = [
        [InlineKeyboardButton("📅 مشاهده رزروهای من", callback_data="my_reservations")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_my_reservations(query, user_id):
    """Show user's reservations"""
    user_reservations = reservations.get(user_id, [])

    if not user_reservations:
        text = "📅 هیچ رزروی ندارید.\n\n"
        text += "برای رزرو، از منوی اصلی گزینه 'رزرو وقت' را انتخاب کنید."
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    else:
        text = "📅 رزروهای شما:\n\n"
        keyboard = []

        for idx, res in enumerate(user_reservations, 1):
            text += f"{idx}. 🎮 {res['game']}\n"

            # Check if it's old format or new format
            if 'duration' in res:
                text += f"   📅 شروع: {res['start_time']}\n"
                text += f"   📅 پایان: {res['end_time']}\n"
                text += f"   ⏱️ مدت: {res['duration']} ساعت\n"
                text += f"   💰 جمع کل: {res['total_price']}\n"
            else:
                text += f"   📅 زمان: {res['time']}\n"
                text += f"   💰 قیمت: {res['price']}\n"

            # Show status with emoji
            if res['status'] == 'confirmed':
                text += f"   ✅ وضعیت: تایید شده\n\n"
                # Add cancel button only for confirmed reservations
                keyboard.append([InlineKeyboardButton(f"❌ کنسل رزرو {idx}", callback_data=f"cancel_{idx-1}")])
            elif res['status'] == 'cancelled':
                text += f"   ❌ وضعیت: کنسل شده\n\n"
            else:
                text += f"   ⏳ وضعیت: {res['status']}\n\n"

        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def cancel_reservation(query, user_id, reservation_index):
    """Cancel a reservation"""
    user_reservations = reservations.get(user_id, [])

    if reservation_index < 0 or reservation_index >= len(user_reservations):
        try:
            await query.edit_message_text("❌ رزرو یافت نشد.")
        except:
            await query.message.reply_text("❌ رزرو یافت نشد.")
        return

    reservation = user_reservations[reservation_index]

    if reservation['status'] != 'confirmed':
        try:
            await query.edit_message_text("❌ این رزرو قبلاً کنسل شده است.")
        except:
            await query.message.reply_text("❌ این رزرو قبلاً کنسل شده است.")
        return

    # Show confirmation dialog
    text = f"⚠️ آیا مطمئن هستید که می‌خواهید این رزرو را کنسل کنید؟\n\n"
    text += f"🎮 بازی: {reservation['game']}\n"

    if 'start_time' in reservation:
        text += f"📅 زمان شروع: {reservation['start_time']}\n"
        text += f"📅 زمان پایان: {reservation['end_time']}\n"
        text += f"⏱️ مدت: {reservation['duration']} ساعت\n"
    else:
        text += f"📅 زمان: {reservation['time']}\n"

    keyboard = [
        [InlineKeyboardButton("✅ بله، کنسل کن", callback_data=f"confirm_cancel_{reservation_index}")],
        [InlineKeyboardButton("❌ خیر، بازگشت", callback_data="my_reservations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def confirm_cancel_reservation(query, user_id, reservation_index):
    """Confirm and cancel a reservation"""
    user_reservations = reservations.get(user_id, [])

    if reservation_index < 0 or reservation_index >= len(user_reservations):
        try:
            await query.edit_message_text("❌ رزرو یافت نشد.")
        except:
            await query.message.reply_text("❌ رزرو یافت نشد.")
        return

    reservation = user_reservations[reservation_index]

    # Cancel the reservation
    reservation['status'] = 'cancelled'

    text = f"✅ رزرو با موفقیت کنسل شد!\n\n"
    text += f"🎮 بازی: {reservation['game']}\n"

    if 'start_time' in reservation:
        text += f"📅 زمان شروع: {reservation['start_time']}\n"
    else:
        text += f"📅 زمان: {reservation['time']}\n"

    text += f"❌ وضعیت: کنسل شده\n\n"
    text += "برای رزرو جدید، از منوی اصلی استفاده کنید."

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به رزروهای من", callback_data="my_reservations")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_tournaments(query):
    """Show available tournaments"""
    text = "🏆 تورنمنت‌های فعال:\n\n"
    keyboard = []

    for tournament_id, tournament in tournaments_data.items():
        text += f"🎮 {tournament['name']}\n"
        text += f"   بازی: {tournament['game_name']}\n"
        text += f"   شروع: {tournament['start_date']}\n"
        text += f"   جایزه: {tournament['prize']}\n"
        text += f"   شرکت‌کنندگان: {tournament['current_participants']}/{tournament['max_participants']}\n"
        text += f"   وضعیت: {tournament['status']}\n\n"

        button_text = f"🎯 {tournament['name']}"
        if tournament['status'] == 'open':
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"tournament_{tournament_id}")])
        else:
            keyboard.append([InlineKeyboardButton(f"🔒 {tournament['name']} (بسته)", callback_data=f"tournament_{tournament_id}")])

    keyboard.append([InlineKeyboardButton("📋 تورنمنت‌های من", callback_data="my_tournaments")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_tournament_details(query, tournament_id):
    """Show tournament details"""
    tournament = tournaments_data.get(tournament_id)
    if not tournament:
        try:
            await query.edit_message_text("تورنمنت یافت نشد.")
        except:
            await query.message.reply_text("تورنمنت یافت نشد.")
        return

    text = f"🏆 {tournament['name']}\n\n"
    text += f"🎮 بازی: {tournament['game_name']}\n"
    text += f"📅 شروع: {tournament['start_date']}\n"
    text += f"📅 پایان: {tournament['end_date']}\n"
    text += f"👥 شرکت‌کنندگان: {tournament['current_participants']}/{tournament['max_participants']}\n"
    text += f"💰 جایزه: {tournament['prize']}\n"
    text += f"💳 هزینه ورود: {tournament['entry_fee']}\n"
    text += f"📝 توضیحات: {tournament['description']}\n"
    text += f"✅ وضعیت: {tournament['status']}\n"

    keyboard = []
    if tournament['status'] == 'open' and tournament['current_participants'] < tournament['max_participants']:
        keyboard.append([InlineKeyboardButton("✅ ثبت‌نام در تورنمنت", callback_data=f"join_{tournament_id}")])
    elif tournament['current_participants'] >= tournament['max_participants']:
        keyboard.append([InlineKeyboardButton("⚠️ ظرفیت پر شده", callback_data="tournaments")])
    else:
        keyboard.append([InlineKeyboardButton("⚠️ ثبت‌نام بسته شده", callback_data="tournaments")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت به تورنمنت‌ها", callback_data="tournaments")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def join_tournament(query, user_id, tournament_id):
    """Join a tournament"""
    tournament = tournaments_data.get(tournament_id)
    if not tournament:
        try:
            await query.edit_message_text("تورنمنت یافت نشد.")
        except:
            await query.message.reply_text("تورنمنت یافت نشد.")
        return

    if tournament['status'] != 'open':
        try:
            await query.edit_message_text("⚠️ ثبت‌نام در این تورنمنت بسته شده است.")
        except:
            await query.message.reply_text("⚠️ ثبت‌نام در این تورنمنت بسته شده است.")
        return

    if tournament['current_participants'] >= tournament['max_participants']:
        try:
            await query.edit_message_text("⚠️ ظرفیت تورنمنت پر شده است.")
        except:
            await query.message.reply_text("⚠️ ظرفیت تورنمنت پر شده است.")
        return

    # Initialize tournament data if needed
    if tournament_id not in tournament_participants:
        tournament_participants[tournament_id] = []

    # Check if user already joined
    if user_id in tournament_participants[tournament_id]:
        try:
            await query.edit_message_text("⚠️ شما قبلاً در این تورنمنت ثبت‌نام کرده‌اید.")
        except:
            await query.message.reply_text("⚠️ شما قبلاً در این تورنمنت ثبت‌نام کرده‌اید.")
        return

    # Add user to tournament
    tournament_participants[tournament_id].append(user_id)
    tournament['current_participants'] += 1

    text = f"✅ ثبت‌نام با موفقیت انجام شد!\n\n"
    text += f"🏆 تورنمنت: {tournament['name']}\n"
    text += f"🎮 بازی: {tournament['game_name']}\n"
    text += f"📅 زمان شروع: {tournament['start_date']}\n"
    text += f"💳 هزینه ورود: {tournament['entry_fee']}\n"
    text += f"💰 جایزه: {tournament['prize']}\n\n"
    text += "⚠️ لطفاً ۱۵ دقیقه قبل از شروع تورنمنت حضور پیدا کنید."

    keyboard = [
        [InlineKeyboardButton("📋 تورنمنت‌های من", callback_data="my_tournaments")],
        [InlineKeyboardButton("🔙 بازگشت به تورنمنت‌ها", callback_data="tournaments")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_my_tournaments(query, user_id):
    """Show user's tournaments"""
    user_tournaments = []
    for tournament_id, participants in tournament_participants.items():
        if user_id in participants:
            tournament = tournaments_data.get(tournament_id)
            if tournament:
                user_tournaments.append(tournament)

    if not user_tournaments:
        text = "📋 شما در هیچ تورنمنتی ثبت‌نام نکرده‌اید.\n\n"
        text += "برای مشاهده تورنمنت‌های فعال، از منوی اصلی گزینه 'تورنمنت‌ها' را انتخاب کنید."
    else:
        text = "📋 تورنمنت‌های شما:\n\n"
        for idx, tournament in enumerate(user_tournaments, 1):
            text += f"{idx}. 🏆 {tournament['name']}\n"
            text += f"   🎮 بازی: {tournament['game_name']}\n"
            text += f"   📅 شروع: {tournament['start_date']}\n"
            text += f"   💰 جایزه: {tournament['prize']}\n"
            text += f"   ✅ وضعیت: {tournament['status']}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_notifications(query):
    """Show notification settings"""
    text = "🔔 اطلاع‌رسانی‌ها\n\n"
    text += "این بخش به زودی فعال می‌شود.\n"
    text += "شما می‌توانید اطلاع‌رسانی برای موارد زیر دریافت کنید:\n"
    text += "• یادآوری رزرو\n"
    text += "• یادآوری تورنمنت\n"
    text += "• تخفیف‌های ویژه\n"
    text += "• بازی‌های جدید\n"
    text += "• تورنمنت‌های جدید\n"
    text += "• رویدادهای گیم سنتر"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_deposit_menu(query):
    """Show deposit menu"""
    text = "💰 افزایش موجودی\n\n"
    text += "برای افزایش موجودی، مراحل زیر را انجام دهید:\n\n"
    text += "1️⃣ مبلغ مورد نظر را واریز کنید:\n"
    text += "   شماره کارت: ۶۰۳۷-۹۹۷۹-۰۰۰۰-۰۰۰۰\n"
    text += "   به نام: گیم سنتر\n\n"
    text += "2️⃣ تصویر رسید پرداخت را ارسال کنید\n\n"
    text += "⚠️ پس از تایید، موجودی شما اضافه می‌شود."

    keyboard = [[InlineKeyboardButton("📸 ارسال رسید پرداخت", callback_data="send_receipt")]]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_receipt_instructions(query):
    """Show instructions for sending receipt"""
    text = "📸 ارسال رسید پرداخت\n\n"
    text += "لطفاً تصویر رسید پرداخت را ارسال کنید.\n\n"
    text += "⚠️ لطفاً مطمئن شوید:\n"
    text += "• تاریخ و ساعت رسید واضح باشد\n"
    text += "• مبلغ واریزی قابل خواندن باشد\n"
    text += "• شماره پیگیری واضح باشد\n\n"
    text += "پس از ارسال، رسید بررسی می‌شود."

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="deposit")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_admin_panel(query):
    """Show admin panel"""
    text = "⚙️ پنل ادمین\n\n"
    text += f"👥 تعداد کاربران: {len(users)}\n"
    text += f"📅 تعداد رزروها: {sum(len(r) for r in reservations.values())}\n"
    text += f"🏆 تعداد تورنمنت‌ها: {len(tournaments_data)}\n"
    text += f"💰 رسیدهای در انتظار: {len([r for r in payment_receipts if r['status'] == 'pending'])}\n"

    keyboard = [
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📅 مدیریت رزروها", callback_data="admin_reservations")],
        [InlineKeyboardButton("💰 رسیدهای پرداخت", callback_data="admin_receipts")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_admin_users(query):
    """Show all users"""
    text = "👥 لیست کاربران:\n\n"

    for idx, (user_id, user) in enumerate(users.items(), 1):
        text += f"{idx}. {user['name']} (@{user.get('username', 'N/A')})\n"
        text += f"   ID: {user_id}\n"
        text += f"   موجودی: {user['balance']:,} تومان\n"
        text += f"   تاریخ عضویت: {user['joined']}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_admin_reservations(query):
    """Show all reservations"""
    text = "📅 لیست تمام رزروها:\n\n"

    count = 0
    for user_id, user_reservations in reservations.items():
        user = users.get(user_id, {})
        for res in user_reservations:
            count += 1
            text += f"{count}. {res['game']}\n"
            text += f"   کاربر: {user.get('name', 'N/A')}\n"
            if 'start_time' in res:
                text += f"   زمان: {res['start_time']} - {res['end_time']}\n"
            else:
                text += f"   زمان: {res['time']}\n"
            text += f"   وضعیت: {res['status']}\n\n"

    if count == 0:
        text = "📅 هیچ رزروی ثبت نشده است."

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def show_admin_receipts(query):
    """Show payment receipts"""
    pending_receipts = [r for r in payment_receipts if r['status'] == 'pending']

    if not pending_receipts:
        text = "💰 هیچ رسیدی در انتظار تایید نیست.\n\n"
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
    else:
        text = "💰 رسیدهای در انتظار تایید:\n\n"
        keyboard = []

        for receipt in pending_receipts:
            user = users.get(receipt['user_id'], {})
            text += f"📸 رسید #{receipt['id']}\n"
            text += f"کاربر: {user.get('name', 'N/A')}\n"
            text += f"مبلغ: {receipt['amount']:,} تومان\n"
            text += f"تاریخ: {receipt['date']}\n"
            text += f"وضعیت: {receipt['status']}\n\n"

            keyboard.append([
                InlineKeyboardButton("✅ تایید", callback_data=f"approve_{receipt['id']}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{receipt['id']}")
            ])

        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def approve_receipt(query, receipt_id):
    """Approve a payment receipt"""
    receipt = next((r for r in payment_receipts if r['id'] == receipt_id), None)

    if not receipt:
        try:
            await query.edit_message_text("❌ رسید یافت نشد.")
        except:
            await query.message.reply_text("❌ رسید یافت نشد.")
        return

    # Update receipt status
    receipt['status'] = 'approved'

    # Add to user balance
    user_id = receipt['user_id']
    if user_id in users:
        users[user_id]['balance'] += receipt['amount']

    text = f"✅ رسید تایید شد!\n\n"
    text += f"رسید #{receipt_id}\n"
    text += f"مبلغ: {receipt['amount']:,} تومان\n"
    text += f"موجودی کاربر اضافه شد."

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به رسیدها", callback_data="admin_receipts")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def reject_receipt(query, receipt_id):
    """Reject a payment receipt"""
    receipt = next((r for r in payment_receipts if r['id'] == receipt_id), None)

    if not receipt:
        try:
            await query.edit_message_text("❌ رسید یافت نشد.")
        except:
            await query.message.reply_text("❌ رسید یافت نشد.")
        return

    # Update receipt status
    receipt['status'] = 'rejected'

    text = f"❌ رسید رد شد!\n\n"
    text += f"رسید #{receipt_id}\n"
    text += f"مبلغ: {receipt['amount']:,} تومان"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به رسیدها", callback_data="admin_receipts")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        await query.message.reply_text(text, reply_markup=reply_markup)

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /score command to record game scores"""
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text(
            "لطفاً فرمت زیر را استفاده کنید:\n"
            "/score نام_بازی امتیاز\n\n"
            "مثال: /score fifa 150"
        )
        return

    game_name = context.args[0]
    try:
        score_value = int(context.args[1])
    except ValueError:
        await update.message.reply_text("امتیاز باید یک عدد باشد.")
        return

    if user_id not in scores:
        scores[user_id] = []

    scores[user_id].append({
        "game": game_name,
        "score": score_value,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

    await update.message.reply_text(
        f"✅ امتیاز ثبت شد!\n\n"
        f"بازی: {game_name}\n"
        f"امتیاز: {score_value}\n"
        f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    text = "🎮 راهنمای ربات گیم سنتر\n\n"
    text += "دستورات:\n"
    text += "/start - شروع ربات\n"
    text += "/score نام_بازی امتیاز - ثبت امتیاز\n"
    text += "/help - راهنما\n\n"
    text += "از دکمه‌های منوی اصلی برای دسترسی به بخش‌های مختلف استفاده کنید."

    await update.message.reply_text(text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages for payment receipts"""
    user_id = update.effective_user.id

    if user_id not in users:
        await update.message.reply_text("⚠️ لطفاً ابتدا دستور /start را بزنید.")
        return

    # Create receipt record
    receipt = {
        "id": len(payment_receipts) + 1,
        "user_id": user_id,
        "photo_file_id": update.message.photo[-1].file_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
        "amount": 0  # Admin will need to verify amount from photo
    }

    payment_receipts.append(receipt)

    text = f"📸 رسید پرداخت دریافت شد!\n\n"
    text += f"رسید #{receipt['id']}\n"
    text += f"وضعیت: در انتظار تایید\n\n"
    text += "⚠️ لطفاً مبلغ واریزی را در پیام بعدی بنویسید.\n"
    text += "مثال: 50000"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_text_for_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages that might be receipt amounts"""
    user_id = update.effective_user.id
    text = update.message.text

    # Try to parse as number (receipt amount)
    try:
        amount = int(text.replace(',', '').replace(' ', ''))
        # Find last pending receipt for this user
        user_receipts = [r for r in payment_receipts if r['user_id'] == user_id and r['status'] == 'pending']

        if user_receipts:
            last_receipt = user_receipts[-1]
            last_receipt['amount'] = amount

            response = f"✅ مبلغ {amount:,} تومان ثبت شد.\n\n"
            response += f"رسید #{last_receipt['id']}\n"
            response += "رسید در انتظار تایید ادمین است."

            await update.message.reply_text(response)
            return
    except ValueError:
        pass

    # If not a number, send help message
    await update.message.reply_text(
        "🤔 پیام دریافت شد.\n\n"
        "اگر می‌خواهید مبلغ رسید را وارد کنید، لطفاً فقط عدد بنویسید.\n"
        "مثال: 50000"
    )

def main():
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("Error: Bot token not found.")
        print("Please create .env file and set TELEGRAM_BOT_TOKEN.")
        return

    print("Bot is starting...")
    print(f"Token found: {token[:10]}...")

    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("score", score_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_for_receipt))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
