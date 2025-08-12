-- SQL migration for FAQ enhancements
ALTER TABLE faq
    ADD COLUMN answered_at TIMESTAMP NULL,
    ADD COLUMN answer_author_id INTEGER NULL REFERENCES "user"(id) ON DELETE SET NULL,
    ADD COLUMN has_new_answer BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE faq
    DROP CONSTRAINT IF EXISTS faq_category_id_fkey,
    ADD CONSTRAINT faq_category_id_fkey FOREIGN KEY (category_id)
        REFERENCES faq_categories (id) ON DELETE CASCADE;

ALTER TABLE faq_categories
    DROP COLUMN IF EXISTS user_group_id;

CREATE TABLE faq_category_access (
    id SERIAL PRIMARY KEY,
    faq_category_id INTEGER NOT NULL REFERENCES faq_categories (id) ON DELETE CASCADE,
    user_group_id INTEGER NOT NULL REFERENCES user_group (id) ON DELETE CASCADE
);
