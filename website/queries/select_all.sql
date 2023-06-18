SELECT 
    tc.phone_number, 
    tc.telegram_api_id,
    tc.telegram_api_hash,
    tc.pipedrive_client_id,
    tc.pipedrive_client_secret,
    s.on_message,
    s.send_message
FROM
    telegram_credentials tc JOIN sessions s 
    ON tc.phone_number = s.phone_number