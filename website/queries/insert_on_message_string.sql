INSERT INTO sessions (phone_number, on_message)
VALUES ('{{ phone_number }}', '{{ on_message_string }}')
ON DUPLICATE KEY UPDATE on_message = VALUES(on_message);
