from .collections import usersdbc, chatsdbc
from .users import is_served_user
from .chats import is_served_chat

async def is_served_user_clone(user_id: int) -> bool:
    user = await usersdbc.find_one({"user_id": user_id})
    if not user:
        return False
    return True

async def get_served_users_clone() -> list:
    users_list = []
    async for user in usersdbc.find({"user_id": {"$gt": 0}}):
        users_list.append(user)
    return users_list

async def add_served_user_clone(user_id: int):
    is_served = await is_served_user(user_id)
    if is_served:
        return
    return await usersdbc.insert_one({"user_id": user_id})

async def get_served_chats_clone() -> list:
    chats_list = []
    async for chat in chatsdbc.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)
    return chats_list

async def is_served_chat_clone(chat_id: int) -> bool:
    chat = await chatsdbc.find_one({"chat_id": chat_id})
    if not chat:
        return False
    return True

async def add_served_chat_clone(chat_id: int):
    is_served = await is_served_chat(chat_id)
    if is_served:
        return
    return await chatsdbc.insert_one({"chat_id": chat_id})

async def delete_served_chat_clone(chat_id: int):
    await chatsdbc.delete_one({"chat_id": chat_id})
