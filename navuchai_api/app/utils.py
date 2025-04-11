def format_test_with_names(test, category_name: str, creator_name: str) -> dict:
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
        "status": test.status,
        "frozen": test.frozen,
        "locale": test.locale,
        "created_at": test.created_at,
        "updated_at": test.updated_at
    }