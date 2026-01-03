from BrandrdXMusic.utils.mongo import db

# تغيير الاسم لتفادي التعارض مع pyrogram.filters
filtersdb = db.filters["filters"]


async def add_filter_db(
    chat_id: int,
    filter_name: str,
    content: str,
    text: str,
    data_type: int,
):
    filter_data = await filtersdb.find_one(
        {
            "chat_id": chat_id
        }
    )

    if filter_data is None:
        await filtersdb.insert_one(
            {
                "chat_id": chat_id,
                "filters": [
                    {
                        "filter_name": filter_name,
                        "content": content,
                        "text": text,
                        "data_type": data_type,
                    }
                ],
            }
        )

    else:
        FILTERS_NAME = await get_filters_list(chat_id)

        if filter_name not in FILTERS_NAME:
            await filtersdb.update_one(
                {
                    "chat_id": chat_id
                },
                {
                    "$addToSet": {
                        "filters": {
                            "filter_name": filter_name,
                            "content": content,
                            "text": text,
                            "data_type": data_type,
                        }
                    }
                },
                upsert=True,
            )
        else:
            await filtersdb.update_one(
                {
                    "chat_id": chat_id,
                    "filters.filter_name": filter_name,
                },
                {
                    "$set": {
                        "filters.$.filter_name": filter_name,
                        "filters.$.content": content,
                        "filters.$.text": text,
                        "filters.$.data_type": data_type,
                    }
                },
            )


async def stop_db(chat_id: int, filter_name: str):
    await filtersdb.update_one(
        {
            "chat_id": chat_id
        },
        {
            "$pull": {
                "filters": {
                    "filter_name": filter_name
                }
            }
        },
    )


async def stop_all_db(chat_id: int):
    await filtersdb.update_one(
        {
            "chat_id": chat_id
        },
        {
            "$set": {
                "filters": []
            }
        },
        upsert=True,
    )


async def get_filter(chat_id: int, filter_name: str):
    filter_data = await filtersdb.find_one(
        {
            "chat_id": chat_id
        }
    )

    if filter_data is not None:
        for filter_ in filter_data.get("filters", []):
            if filter_["filter_name"] == filter_name:
                return (
                    filter_name,
                    filter_["content"],
                    filter_["text"],
                    filter_["data_type"],
                )

    return None


async def get_filters_list(chat_id: int):
    filter_data = await filtersdb.find_one(
        {
            "chat_id": chat_id
        }
    )

    if filter_data is not None:
        return [
            f["filter_name"]
            for f in filter_data.get("filters", [])
        ]

    return []
