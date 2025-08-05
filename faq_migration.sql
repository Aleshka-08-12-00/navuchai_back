-- SQL migration for FAQ enhancements
ALTER TABLE faq
    ADD COLUMN answered_at TIMESTAMP NULL,
    ADD COLUMN answer_author_id INTEGER NULL REFERENCES "user"(id) ON DELETE SET NULL,
    ADD COLUMN has_new_answer BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN question_file_url TEXT NULL,
    ADD COLUMN answer_file_url TEXT NULL;
ALTER TABLE faq
    DROP CONSTRAINT IF EXISTS faq_category_id_fkey,
    ADD CONSTRAINT faq_category_id_fkey FOREIGN KEY (category_id)
        REFERENCES faq_categories (id) ON DELETE CASCADE;
