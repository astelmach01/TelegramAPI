INSERT INTO `telegram_credentials` (
    `phone_number`,
    `telegram_api_id`,
    `telegram_api_hash`,
    `pipedrive_client_id`,
    `pipedrive_client_secret`
)
VALUES (
    '{{phone_number}}',
    '{{telegram_api_id}}',
    '{{telegram_api_hash}}',
    '{{pipedrive_client_id}}',
    '{{pipedrive_client_secret}}'
)
ON DUPLICATE KEY UPDATE
    `telegram_api_id` = VALUES(`telegram_api_id`),
    `telegram_api_hash` = VALUES(`telegram_api_hash`),
    `pipedrive_client_id` = VALUES(`pipedrive_client_id`),
    `pipedrive_client_secret` = VALUES(`pipedrive_client_secret`);
