INSERT INTO sessions (phone_number, send_message)
VALUES ('{{ phone_number }}', '{{ send_message_string }}')
ON DUPLICATE KEY UPDATE send_message = VALUES(send_message);
