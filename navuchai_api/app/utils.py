def format_test_with_names(test, category_name: str, creator_name: str, locale_code: str, status_name: str, status_name_ru: str, status_color: str) -> dict:
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "time_limit": test.time_limit,
        "category_id": test.category_id,
        "category_name": category_name,
        "creator_id": test.creator_id,
        "creator_name": creator_name,
        "access_timestamp": test.access_timestamp,
        "status_id": test.status_id,
        "status_name": status_name,
        "status_name_ru": status_name_ru,
        "status_color": status_color,
        "percent": test.avg_percent,
        "completed": test.completed_number,
        "frozen": test.frozen,
        "locale_id": test.locale_id,
        "locale_code": locale_code,
        "img_id": test.img_id,
        "image": test.image,
        "created_at": test.created_at,
        "updated_at": test.updated_at
    }


# def format_user(user, role_name: str) -> dict:
#     return {
#         "id": user.id,
#         "name": user.name,
#         "username": user.username,
#         "email": user.email,
#         "role_id": user.role_id,
#         "role_name": role_name,
#         "created_at": user.created_at,
#         "updated_at": user.updated_at
#     }
