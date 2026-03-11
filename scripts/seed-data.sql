-- Seed data for testing
-- Password for all users is: password123 (bcrypt hash)

INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at)
VALUES
    (
        'a0000000-0000-0000-0000-000000000001',
        'admin',
        'admin@example.com',
        '$2y$12$SntCaVGq8x5OxVN0/mxAFOQ9.L8VCQD2ylOZx5fO9G4k2A6ydwcdC',
        'System Administrator',
        'ADMIN',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000002',
        'approver1',
        'approver1@example.com',
        '$2y$12$SntCaVGq8x5OxVN0/mxAFOQ9.L8VCQD2ylOZx5fO9G4k2A6ydwcdC',
        'Level 1 Approver',
        'APPROVER_L1',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000003',
        'approver2',
        'approver2@example.com',
        '$2y$12$SntCaVGq8x5OxVN0/mxAFOQ9.L8VCQD2ylOZx5fO9G4k2A6ydwcdC',
        'Level 2 Approver',
        'APPROVER_L2',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000004',
        'user1',
        'user1@example.com',
        '$2y$12$SntCaVGq8x5OxVN0/mxAFOQ9.L8VCQD2ylOZx5fO9G4k2A6ydwcdC',
        'Regular User',
        'USER',
        true,
        NOW()
    )
ON CONFLICT (username) DO NOTHING;
