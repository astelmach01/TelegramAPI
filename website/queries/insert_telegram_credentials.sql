INSERT INTO
    `telegram_credentials` (
        `phone_number`,
        `phone_code_hash`,
        `telegram_api_id`,
        `telegram_api_hash`,
        `pipedrive_client_id`,
        `pipedrive_client_secret`
    )
VALUES
    (
        '{{phone_number}}',
        '{{phone_code_hash}}',
        '{{telegram_api_id}}',
        '{{telegram_api_hash}}',
        '{{pipedrive_client_id}}',
        '{{pipedrive_client_secret}}'
    );