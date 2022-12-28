import asyncio
import random
from time import time
from telebot import types, asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from pymongo import MongoClient
from bson.objectid import ObjectId

# TODO: Прописать хелп
# TODO: Сделать подтверждения выхода
# TODO: Добавить таймер хода


TOKEN = ""

bot = AsyncTeleBot(TOKEN, state_storage=StateMemoryStorage())

cluster = MongoClient('')
db = cluster["uno_data"]
lobby_collection = db["lobbies"]
user_collection = db["users"]
game_collection = db["games"]
hand_collection = db["hands"]

bot_start_string = "Это бот для игры в Uno"

create_lobby_text = "Создать лобби"
lobby_list_text = "Список лобби"
join_lobby_text = "Присоединиться по коду"

max_player_allowed = 6

uno_deck = ["0~y", "0~g", "0~r", "0~b",
            "1~y", "1~g", "1~r", "1~b",
            "1~y", "1~g", "1~r", "1~b",
            "2~y", "2~g", "2~r", "2~b",
            "2~y", "2~g", "2~r", "2~b",
            "3~y", "3~g", "3~r", "3~b",
            "3~y", "3~g", "3~r", "3~b",
            "4~y", "4~g", "4~r", "4~b",
            "4~y", "4~g", "4~r", "4~b",
            "5~y", "5~g", "5~r", "5~b",
            "5~y", "5~g", "5~r", "5~b",
            "6~y", "6~g", "6~r", "6~b",
            "6~y", "6~g", "6~r", "6~b",
            "7~y", "7~g", "7~r", "7~b",
            "7~y", "7~g", "7~r", "7~b",
            "8~y", "8~g", "8~r", "8~b",
            "8~y", "8~g", "8~r", "8~b",
            "9~y", "9~g", "9~r", "9~b",
            "9~y", "9~g", "9~r", "9~b",
            "re~y", "re~g", "re~r", "re~b",
            "re~y", "re~g", "re~r", "re~b",
            "s~y", "s~g", "s~r", "s~b",
            "s~y", "s~g", "s~r", "s~b",
            "d~y", "d~g", "d~r", "d~b",
            "d~y", "d~g", "d~r", "d~b",
            "w~bl", "w~bl", "w~bl", "w~bl",
            "wd4~bl", "wd4~bl", "wd4~bl", "wd4~bl"]

decode_sheet = {"r": "🔴",
                "b": "🔵",
                "y": "🟡",
                "g": "🟢",
                "bl": "⚫",
                "re": "Смена направления",
                "s": "Пропуск хода",
                "d": "+2 карты",
                "w": "Cмена цвета",
                "wd4": "Смена цвета и +4 карты",
                "1": "1",
                "2": "2",
                "3": "3",
                "4": "4",
                "5": "5",
                "6": "6",
                "7": "7",
                "8": "8",
                "9": "9",
                "0": "0",
                }


class MyStates(StatesGroup):
    menu = State()
    lobby_name = State()
    invite_code = State()


def invite_code_generator():
    random_string = ''
    for _ in range(6):
        random_integer = random.randint(97, 97 + 26 - 1)
        random_string += (chr(random_integer))

    return random_string


@bot.message_handler(commands=['start', 'cancel'])
async def hello_message(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    user = user_collection.find_one({"user_id": message.chat.id})
    if user is None:
        username = message.from_user.username
        if username is None:
            username = message.from_user.first_name
        new_user = {"user_id": message.chat.id,
                    "name": username,
                    "status": "start_menu",
                    "lobby": None,
                    "game": None,
                    "is_host": False}
        user_collection.insert_one(new_user)
    else:
        if user["status"] == "in_lobby":
            lobby = lobby_collection.find_one({"_id": ObjectId(user["lobby"])})
            in_game = user["game"] is not None
            game = None
            if in_game:
                game = game_collection.find_one({"_id": user["game"]})
            if user["is_host"]:
                for player in lobby["players"]:
                    user_collection.update_one({"user_id": player}, {"$set": {"status": "start_menu",
                                                                              "lobby": None,
                                                                              "game": None,
                                                                              "is_host": False}})
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    item_1 = types.KeyboardButton(create_lobby_text)
                    item_2 = types.KeyboardButton(join_lobby_text)
                    item_3 = types.KeyboardButton(lobby_list_text)
                    markup.add(item_1, item_2, item_3)
                    await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
                    if in_game:
                        await bot.send_message(player, "Хост отключился\n Игра окончена\n Лобби расформировано",
                                               reply_markup=markup)
                    else:
                        await bot.send_message(player, "Лобби расформировано",
                                               reply_markup=markup)
                lobby_collection.delete_one({"_id": lobby["_id"]})
                if in_game:
                    hand_collection.delete_one({"_id": game["player_hands"]})
                    game_collection.delete_one({"_id": game["_id"]})
            else:
                if in_game:
                    reverse_order = game["reverse_order"]
                    players = lobby["players"]
                    if len(players) <= 2:
                        for player in players:
                            if player == message.chat.id:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                                item_1 = types.KeyboardButton(create_lobby_text)
                                item_2 = types.KeyboardButton(join_lobby_text)
                                item_3 = types.KeyboardButton(lobby_list_text)
                                markup.add(item_1, item_2, item_3)
                                await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
                                await bot.send_message(message.chat.id, "Вы вышли из игры", reply_markup=markup)
                            else:
                                await bot.send_message(player, text=user["name"] +
                                                                    " вышел из игры\n Вы становитесь победителем!")
                            game_collection.update_one({"_id": game["_id"]}, {"$pull": {"players": message.chat.id}})
                            lobby_collection.update_one({"_id": lobby["_id"]}, {"$pull": {"players": message.chat.id},
                                                                                "$inc": {"cur_players": -1}})
                    else:
                        cur_player = game["cur_player"]
                        player_hands = hand_collection.find_one({"_id": game["player_hands"]})
                        cur_deck = game["cur_deck"]
                        for card in player_hands[str(message.chat.id)]:
                            cur_deck.append(card)
                        if reverse_order:
                            next_player = (len(players) + cur_player - 1) % len(players)
                        else:
                            next_player = (cur_player + 1) % len(players)
                        next_player_name = user_collection.find_one({"user_id": players[next_player]})["name"]
                        if players[cur_player] == message.chat.id:
                            for player in players:
                                if player == message.chat.id:
                                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                                    item_1 = types.KeyboardButton(create_lobby_text)
                                    item_2 = types.KeyboardButton(join_lobby_text)
                                    item_3 = types.KeyboardButton(lobby_list_text)
                                    markup.add(item_1, item_2, item_3)
                                    await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
                                    await bot.send_message(message.chat.id, "Вы вышли из игры", reply_markup=markup)
                                else:
                                    await bot.send_message(player, text=user["name"] + " вышел из игры\n " +
                                                                        "Его карты были переложены в колоду\n "
                                                                        "Ход переходит к игроку "
                                                                        + next_player_name)
                            game_collection.update_one({"_id": game["_id"]}, {"$pull": {"players": message.chat.id},
                                                                              "$set": {"cur_deck": cur_deck}})
                            lobby_collection.update_one({"_id": lobby["_id"]}, {"$pull": {"players": message.chat.id},
                                                                                "$inc": {"cur_players": -1}})
                            await make_move(game["_id"])
                        else:
                            left_player = max_player_allowed + 1
                            for i, player in enumerate(players):
                                if player == message.chat.id:
                                    left_player = i
                                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                                    item_1 = types.KeyboardButton(create_lobby_text)
                                    item_2 = types.KeyboardButton(join_lobby_text)
                                    item_3 = types.KeyboardButton(lobby_list_text)
                                    markup.add(item_1, item_2, item_3)
                                    await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
                                    await bot.send_message(message.chat.id, "Вы вышли из игры", reply_markup=markup)
                                else:
                                    await bot.send_message(player, text=user["name"] + " вышел из игры\n " +
                                                                        "Его карты были переложены в колоду\n ")
                            if cur_player > left_player:
                                cur_player -= 1
                            game_collection.update_one({"_id": game["_id"]}, {"$pull": {"players": message.chat.id},
                                                                              "$set": {"cur_player": cur_player,
                                                                                       "cur_deck": cur_deck}})
                            lobby_collection.update_one({"_id": lobby["_id"]}, {"$pull": {"players": message.chat.id},
                                                                                "$inc": {"cur_players": -1}})
                else:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    item_1 = types.KeyboardButton(create_lobby_text)
                    item_2 = types.KeyboardButton(join_lobby_text)
                    item_3 = types.KeyboardButton(lobby_list_text)
                    markup.add(item_1, item_2, item_3)
                    await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
                    await bot.send_message(message.chat.id, "Вы вышли из лобби", reply_markup=markup)
                    lobby_collection.update_one({"_id": lobby["_id"]}, {"$pull": {"players": message.chat.id},
                                                                        "$inc": {"cur_players": -1}})
                    for player in lobby["players"]:
                        if player == lobby["host"]:
                            markup = types.InlineKeyboardMarkup()
                            item1 = types.InlineKeyboardButton(text="Начать игру", callback_data="start")
                            markup.add(item1)
                            await bot.send_message(player, text=user["name"] + " вышел из лобби", reply_markup=markup)
                        elif player != message.chat.id:
                            await bot.send_message(player, text=user["name"] + " вышел из лобби")
                user_collection.update_one({"user_id": message.chat.id}, {"$set": {"status": "start_menu",
                                                                                   "lobby": None,
                                                                                   "game": None}})
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            item_1 = types.KeyboardButton(create_lobby_text)
            item_2 = types.KeyboardButton(join_lobby_text)
            item_3 = types.KeyboardButton(lobby_list_text)
            markup.add(item_1, item_2, item_3)
            await bot.set_state(message.from_user.id, MyStates.menu, message.chat.id)
            await bot.send_message(message.chat.id, bot_start_string, reply_markup=markup)


@bot.message_handler(state=MyStates.menu, content_types=['text'])
async def message_reply(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    user = user_collection.find_one({"user_id": message.chat.id})
    if user is None:
        await bot.send_message(message.chat.id, "Сначала запустите бота командой /start")
    elif user["status"] == "in_lobby":
        await bot.send_message(message.chat.id, "Для начала выйдите из лобби в меню командой /cancel")
    else:
        if message.text == lobby_list_text:
            lobbies = [lobby for lobby in lobby_collection.find({"is_full": False,
                                                                 "setting": "open"})]
            markup = types.InlineKeyboardMarkup()
            if len(lobbies) >= 5:
                for lobby in lobbies[:5]:
                    text = lobby["name"] + " " + str(lobby["cur_players"]) + "/" + str(lobby["max_players"])
                    item = types.InlineKeyboardButton(text=text, callback_data="connect;" + str(lobby["_id"]))
                    markup.add(item)
                item = types.InlineKeyboardButton(text="Дальше", callback_data="next;5")
                markup.add(item)
                await bot.send_message(message.chat.id, "Список лобби:", reply_markup=markup)
            else:
                for lobby in lobbies:
                    text = lobby["name"] + " " + str(lobby["cur_players"]) + "/" + str(lobby["max_players"])
                    item = types.InlineKeyboardButton(text=text, callback_data="connect;" + str(lobby["_id"]))
                    markup.add(item)
                await bot.send_message(message.chat.id, "Список лобби:", reply_markup=markup)
        elif message.text == create_lobby_text:
            # await bot.set_state(message.from_user.id, MyStates.name, message.chat.id)
            # await bot.send_message(message.chat.id, 'Hi, write me a name')
            await bot.send_message(message.chat.id, text="Напишите имя лобби (не используйте знак ; пожалуйста):")
            await bot.set_state(message.from_user.id, MyStates.lobby_name, message.chat.id)
        elif message.text == join_lobby_text:
            await bot.send_message(message.chat.id, text="Напишите код приглашения:")
            await bot.set_state(message.from_user.id, MyStates.invite_code, message.chat.id)


@bot.message_handler(state=MyStates.lobby_name)
async def choose_lobby_setting(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    if ";" in message.text:
        await bot.set_state(message.from_user.id, MyStates.lobby_name, message.chat.id)
        await bot.send_message(message.chat.id,
                               text="Ну я же попросил. Попробуйте другое, на этот раз всё-таки без точки с запятой:")
    elif lobby_collection.find_one({"name": message.text}) is not None:
        await bot.set_state(message.from_user.id, MyStates.lobby_name, message.chat.id)
        await bot.send_message(message.chat.id, text="Это имя занято. Попробуйте другое:")
    else:
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton(text="Открытое", callback_data="choose;" + message.text + ";open")
        item2 = types.InlineKeyboardButton(text="Закрытое", callback_data="choose;" + message.text + ";closed")
        markup.add(item1, item2)
        await bot.send_message(message.chat.id, text="Выберите тип лобби:", reply_markup=markup)


@bot.message_handler(state=MyStates.invite_code)
async def join_lobby(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    lobby = lobby_collection.find_one({"invite_code": message.text})
    if lobby is None:
        await bot.send_message(message.chat.id, text="Лобби не найдено")
    elif lobby["is_full"]:
        await bot.send_message(message.chat.id, text="Лобби заполнено")
    else:
        answer = "Присоединение к лобби " + lobby["name"]
        username = message.from_user.username
        if username is None:
            username = message.from_user.first_name
        for player in lobby["players"]:
            if player == lobby["host"]:
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton(text="Начать игру", callback_data="start")
                markup.add(item1)
                await bot.send_message(player, text=username + " присоединился к лобби",
                                       reply_markup=markup)
            else:
                await bot.send_message(player, text=username + " присоединился к лобби")
        lobby_collection.update_one({"_id": lobby["_id"]}, {"$inc": {"cur_players": 1},
                                                            "$push": {"players": message.chat.id}})
        if lobby["max_players"] <= lobby["cur_players"] + 1:
            lobby_collection.update_one({"_id": lobby["_id"]}, {"$set": {"is_full": True}})
        user_collection.update_one({"user_id": message.chat.id}, {"$set": {"status": "in_lobby",
                                                                           "lobby": lobby["_id"]}})
        await bot.send_message(message.chat.id, text=answer)


@bot.callback_query_handler(func=lambda call: True)
async def query_handler(call):
    random.seed(int(time()))
    call_split = call.data.split(";")
    if call_split[0] == "connect":
        user = user_collection.find_one({"user_id": call.message.chat.id})
        lobby = lobby_collection.find_one({"_id": ObjectId(call_split[1])})
        answer = "Присоединение к лобби " + lobby["name"]
        for player in lobby["players"]:
            if player == lobby["host"]:
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton(text="Начать игру", callback_data="start")
                markup.add(item1)
                await bot.send_message(player, text=user["name"] + " присоединился к лобби", reply_markup=markup)
            else:
                await bot.send_message(player, text=user["name"] + " присоединился к лобби")
        lobby_collection.update_one({"_id": lobby["_id"]}, {"$inc": {"cur_players": 1},
                                                            "$push": {"players": call.message.chat.id}})
        if lobby["max_players"] <= lobby["cur_players"] + 1:
            lobby_collection.update_one({"_id": lobby["_id"]}, {"$set": {"is_full": True}})
        user_collection.update_one({"user_id": call.message.chat.id}, {"$set": {"status": "in_lobby",
                                                                                "lobby": lobby["_id"]}})
        await bot.send_message(call.message.chat.id, answer)
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    elif call_split[0] == "next":
        markup = types.InlineKeyboardMarkup()
        lobbies = list(lobby_collection.find({"is_full": False,
                                              "setting": "open"}))
        num = int(call_split[1])
        if len(lobbies) >= num + 5:
            for lobby in lobbies[num:num + 5]:
                text = lobby["name"] + " " + str(lobby["cur_players"]) + "/" + str(lobby["max_players"])
                item = types.InlineKeyboardButton(text=text, callback_data="connect;" + lobby["_id"])
                markup.add(item)
            item = types.InlineKeyboardButton(text="Дальше", callback_data="next " + str(num + 5))
            markup.add(item)
            await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
        else:
            markup = types.InlineKeyboardMarkup()
            for lobby in lobbies[num:]:
                text = lobby["name"] + " " + str(lobby["cur_players"]) + "/" + str(lobby["max_players"])
                item = types.InlineKeyboardButton(text=text, callback_data="connect;" + lobby["_id"])
                markup.add(item)
            await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call_split[0] == "choose":
        markup = types.InlineKeyboardMarkup()
        for i in range(2, max_player_allowed + 1):
            item = types.InlineKeyboardButton(text=str(i), callback_data="create;" + call_split[1] + ";" +
                                                                         call_split[2] + ";" + str(i))
            markup.add(item)
        await bot.send_message(call.message.chat.id, text="Выберите число игроков:", reply_markup=markup)
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    elif call_split[0] == "create":
        user_name = call.message.chat.id
        lobby_name = call_split[1]
        invite_code = invite_code_generator()
        players = [call.message.chat.id]
        while lobby_collection.find_one({"invite_code": invite_code}) is not None:
            invite_code = invite_code_generator()
        lobby_setting = call_split[2]
        is_full = False
        cur_players = 1
        max_players = int(call_split[3])
        new_lobby = {"name": lobby_name,
                     "host": user_name,
                     "players": players,
                     "invite_code": invite_code,
                     "setting": lobby_setting,
                     "is_full": is_full,
                     "max_players": max_players,
                     "cur_players": cur_players,
                     }
        lobby = lobby_collection.insert_one(new_lobby)
        user_collection.update_one({"user_id": call.message.chat.id}, {"$set": {"status": "in_lobby",
                                                                                "lobby": lobby.inserted_id,
                                                                                "is_host": True}})
        if lobby_setting == "open":
            text = "Открытое лобби " + lobby_name + " на " + str(max_players) + " игроков\n"
        else:
            text = "Закрытое лобби " + lobby_name + " на " + str(max_players) + " игроков\n"
        await bot.send_message(call.message.chat.id, text=text + "Код для приглашения: " + invite_code)
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    elif call_split[0] == "start":
        user = user_collection.find_one({"user_id": call.message.chat.id})
        lobby = lobby_collection.find_one({"_id": user["lobby"]})
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        await start_game(lobby)

    elif call_split[0] == "play":
        user = user_collection.find_one({"user_id": call.message.chat.id})
        game = game_collection.find_one({"_id": user["game"]})
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        cur_deck = game["cur_deck"]
        player_hands = hand_collection.find_one({"_id": game["player_hands"]})
        cur_player = game["cur_player"]
        reverse_order = game["reverse_order"]
        cur_card = game["cur_card"]
        players = game["players"]
        cur_player_name = user_collection.find_one({"user_id": players[cur_player]})["name"]
        if call_split[1] == "draw":
            new_card = random.choice(cur_deck)
            player_hands[str(players[cur_player])].append(new_card)
            cur_deck.remove(new_card)
            if not cur_deck:
                cur_deck = uno_deck
                for player in players:
                    for card in player_hands[str(player)]:
                        cur_deck.remove(card)
                cur_deck.remove(cur_card)
            for player in players:
                if player == players[cur_player]:
                    await bot.send_message(player, "Вы взяли " + card_to_text(new_card) + " из колоды")
                else:
                    await bot.send_message(player, "Игрок " + cur_player_name + " взял карту из колоды")
            if reverse_order:
                cur_player = (len(players) + cur_player - 1) % len(players)
            else:
                cur_player = (cur_player + 1) % len(players)
        else:
            played_card = call_split[1].split("~")
            if (played_card[0] == "w" or played_card[0] == "wd4") and played_card[1] != "bl":
                player_hands[str(players[cur_player])].remove(played_card[0] + "~bl")
            else:
                player_hands[str(players[cur_player])].remove(call_split[1])
            if not player_hands[str(players[cur_player])]:
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы выиграли!!!")
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " выиграл. Игра окончена")
                return

            if played_card[0] == "d":
                cur_card = call_split[1]
                if reverse_order:
                    next_player = (len(players) + cur_player - 1) % len(players)
                else:
                    next_player = (cur_player + 1) % len(players)
                if len(cur_deck) < 3:
                    cur_deck = uno_deck
                    for player in players:
                        for card in player_hands[str(player)]:
                            cur_deck.remove(card)
                    cur_deck.remove(cur_card)
                first_new_card = random.choice(cur_deck)
                cur_deck.remove(first_new_card)
                second_new_card = random.choice(cur_deck)
                cur_deck.remove(second_new_card)
                player_hands[str(players[next_player])].append(first_new_card)
                player_hands[str(players[next_player])].append(second_new_card)
                next_player_name = user_collection.find_one({"user_id": players[next_player]})["name"]
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " + card_to_text(cur_card) + "\n" +
                                               "Игрок " + next_player_name + " взял две карты и пропустил ход")
                    elif player == players[next_player]:
                        await bot.send_message(player,
                                               "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card) + "\n" +
                                               "Вы взяли " + card_to_text(first_new_card) + " и " +
                                               card_to_text(second_new_card) + " и пропустили ход")
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card) + "\n" +
                                               "Игрок " + next_player_name + " взял две карты и пропустил ход")
                if reverse_order:
                    cur_player = (len(players) + next_player - 1) % len(players)
                else:
                    cur_player = (next_player + 1) % len(players)

            elif played_card[0] == "s":
                cur_card = call_split[1]
                if reverse_order:
                    next_player = (len(players) + cur_player - 1) % len(players)
                else:
                    next_player = (cur_player + 1) % len(players)
                next_player_name = user_collection.find_one({"user_id": players[next_player]})["name"]
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " + card_to_text(cur_card) + "\n" +
                                               "Игрок " + next_player_name + " пропустил ход")
                    elif player == players[next_player]:
                        await bot.send_message(player,
                                               "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card) + "\n" +
                                               "Вы пропустили ход")
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card) + "\n" +
                                               "Игрок " + next_player_name + " пропустил ход")
                if reverse_order:
                    cur_player = (len(players) + next_player - 1) % len(players)
                else:
                    cur_player = (next_player + 1) % len(players)

            elif played_card[0] == "re":
                cur_card = call_split[1]
                reverse_order = not reverse_order
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " +
                                               card_to_text(cur_card) + " и поменяли направление")
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card) + " и поменял направление")
                cur_player = (len(players) - cur_player) % len(players)

            elif (played_card[0] == "w" or played_card[0] == "wd4") and played_card[1] == "bl":
                markup = types.InlineKeyboardMarkup()
                item1 = types.InlineKeyboardButton("🔴", callback_data="play;" + played_card[0] + "~r")
                item2 = types.InlineKeyboardButton("🔵", callback_data="play;" + played_card[0] + "~b")
                item3 = types.InlineKeyboardButton("🟡", callback_data="play;" + played_card[0] + "~y")
                item4 = types.InlineKeyboardButton("🟢", callback_data="play;" + played_card[0] + "~g")
                markup.add(item1, item2, item3, item4)
                await bot.send_message(call.message.chat.id, "Выберите цвет", reply_markup=markup)
                return

            elif played_card[0] == "w":
                cur_card = call_split[1]
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " + decode_sheet[played_card[0]] +
                                               " и поменяли цвет на " + decode_sheet[played_card[1]])
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               decode_sheet[played_card[0]] + " и поменял цвет на " +
                                               decode_sheet[played_card[1]])
                if reverse_order:
                    cur_player = (len(players) + cur_player - 1) % len(players)
                else:
                    cur_player = (cur_player + 1) % len(players)

            elif played_card[0] == "wd4":
                cur_card = call_split[1]
                if reverse_order:
                    next_player = (len(players) + cur_player - 1) % len(players)
                else:
                    next_player = (cur_player + 1) % len(players)
                if len(cur_deck) < 5:
                    cur_deck = uno_deck
                    for player in players:
                        for card in player_hands[str(player)]:
                            cur_deck.remove(card)
                    cur_deck.remove(cur_card)
                first_new_card = random.choice(cur_deck)
                cur_deck.remove(first_new_card)
                second_new_card = random.choice(cur_deck)
                cur_deck.remove(second_new_card)
                third_new_card = random.choice(cur_deck)
                cur_deck.remove(third_new_card)
                forth_new_card = random.choice(cur_deck)
                cur_deck.remove(forth_new_card)
                player_hands[str(players[next_player])].append(first_new_card)
                player_hands[str(players[next_player])].append(second_new_card)
                player_hands[str(players[next_player])].append(third_new_card)
                player_hands[str(players[next_player])].append(forth_new_card)
                next_player_name = user_collection.find_one({"user_id": players[next_player]})["name"]
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " + decode_sheet[played_card[0]] +
                                               " и поменяли цвет на " + decode_sheet[played_card[1]] + "\n" +
                                               "Игрок " + next_player_name + " взял четыре карты и пропустил ход")
                    elif player == players[next_player]:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               decode_sheet[played_card[0]] + " и поменял цвет на " +
                                               decode_sheet[played_card[1]] + "\n" +
                                               "Вы взяли " + card_to_text(first_new_card) + ", " +
                                               card_to_text(second_new_card) + ", " +
                                               card_to_text(third_new_card) + " и " +
                                               card_to_text(forth_new_card) + " и пропустили ход")
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               decode_sheet[played_card[0]] + " и поменял цвет на " +
                                               decode_sheet[played_card[1]] + "\n" +
                                               "Игрок " + next_player_name + " взял четыре карты и пропустил ход")
                if reverse_order:
                    cur_player = (len(players) + next_player - 1) % len(players)
                else:
                    cur_player = (next_player + 1) % len(players)

            else:
                cur_card = call_split[1]
                for player in players:
                    if player == players[cur_player]:
                        await bot.send_message(player, "Вы сходили картой " + card_to_text(cur_card))
                    else:
                        await bot.send_message(player, "Игрок " + cur_player_name + " сходил картой " +
                                               card_to_text(cur_card))
                if reverse_order:
                    cur_player = (len(players) + cur_player - 1) % len(players)
                else:
                    cur_player = (cur_player + 1) % len(players)
        hand_collection.delete_one({"_id": game["player_hands"]})
        player_hands["_id"] = game["player_hands"]
        hand_collection.insert_one(player_hands)
        game_collection.update_one({"_id": game["_id"]}, {"$set": {"cur_deck": cur_deck,
                                                                   "cur_player": cur_player,
                                                                   "cur_card": cur_card,
                                                                   "reverse_order": reverse_order}})
        await make_move(game["_id"])


async def start_game(lobby):
    random.seed(int(time()))
    cur_deck = uno_deck
    players = lobby["players"]
    player_hands = {}
    cur_player = 0
    reverse_order = False

    for player in players:
        player_hands[str(player)] = [random.choice(cur_deck)]
        cur_deck.remove(player_hands[str(player)][0])
        for i in range(6):
            new_card = random.choice(cur_deck)
            player_hands[str(player)].append(new_card)
            cur_deck.remove(new_card)
        card_text = ''
        for card in player_hands[str(player)]:
            card_text += card_to_text(card) + "\n"
        await bot.send_message(player, "Ваша рука:\n" + card_text)

    cur_card = random.choice(cur_deck)
    cur_deck.remove(cur_card)
    hand = hand_collection.insert_one(player_hands)
    game = game_collection.insert_one({"lobby_id": lobby["_id"],
                                       "cur_deck": cur_deck,
                                       "cur_player": cur_player,
                                       "cur_card": cur_card,
                                       "players": players,
                                       "player_hands": hand.inserted_id,
                                       "reverse_order": reverse_order})
    for player in players:
        user_collection.update_one({"user_id": player}, {"$set": {"game": game.inserted_id}})
    await make_move(game.inserted_id)


async def make_move(game_id):
    game = game_collection.find_one({"_id": game_id})
    cur_card = game["cur_card"]
    cur_card_split = cur_card.split("~")
    cur_player = game["cur_player"]
    player_hands = hand_collection.find_one({"_id": game["player_hands"]})
    players = game["players"]
    cur_player_name = user_collection.find_one({"user_id": players[cur_player]})["name"]
    reverse_order = game["reverse_order"]
    cur_card_text = "Карта на столе:\n" + card_to_text(cur_card) + "\n"
    order_text = "Порядок:\n"
    if reverse_order:
        ordered_players = reversed(players)
    else:
        ordered_players = players
    for player in ordered_players:
        player_name = user_collection.find_one({"user_id": player})["name"]
        hand_count = len(player_hands[str(player)])
        if player_name == cur_player_name:
            order_text += player_name + " | " + str(hand_count) + " карт в руке <--\n"
        else:
            order_text += player_name + " | " + str(hand_count) + " карт в руке\n"

    order_text += "\n"
    for player in players:
        if player == players[cur_player]:
            markup = types.InlineKeyboardMarkup()
            hand_text = 'Ваша рука:\n'
            for card in player_hands[str(player)]:
                card_split = card.split("~")
                hand_text += card_to_text(card) + "\n"
                if card_split[1] == "bl" or card_split[0] == cur_card_split[0] or card_split[1] == cur_card_split[1]:
                    item = types.InlineKeyboardButton(card_to_text(card), callback_data="play;" + card)
                    markup.add(item)
            item = types.InlineKeyboardButton(text="Тянуть карту из колоды", callback_data="play;draw")
            markup.add(item)
            await bot.send_message(player, order_text + hand_text + "\n" + cur_card_text + "\nВаш ход:",
                                   reply_markup=markup)
        else:
            hand_text = 'Ваша рука:\n'
            for card in player_hands[str(player)]:
                hand_text += card_to_text(card) + "\n"
            await bot.send_message(player,
                                   order_text + hand_text + "\n" + cur_card_text + "\nХод игрока " + cur_player_name)


def card_to_text(card):
    card_split = card.split("~")
    return decode_sheet[card_split[1]] + " " + decode_sheet[card_split[0]]


bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.TextContainsFilter())


loop = asyncio.get_event_loop()
result = loop.run_until_complete(bot.polling())
