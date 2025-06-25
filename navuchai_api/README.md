# Navuchai API

This service exposes a set of endpoints for managing courses, modules and lessons.

## Uploading course images

Use `POST /api/files/upload-image/` to upload an image. To automatically attach the uploaded image to a course, pass the course identifier via the `courseId` query parameter (snake_case `course_id` is also accepted).
