-- Seed data for testing
-- Password for all users is: password123 (bcrypt hash)

INSERT INTO users (id, username, email, password_hash, full_name, role, is_active, created_at)
VALUES
    (
        'a0000000-0000-0000-0000-000000000001',
        'admin',
        'admin@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.K3rXDqnGhVH5Oa',
        'System Administrator',
        'admin',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000002',
        'approver1',
        'approver1@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.K3rXDqnGhVH5Oa',
        'Level 1 Approver',
        'approver_l1',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000003',
        'approver2',
        'approver2@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.K3rXDqnGhVH5Oa',
        'Level 2 Approver',
        'approver_l2',
        true,
        NOW()
    ),
    (
        'a0000000-0000-0000-0000-000000000004',
        'user1',
        'user1@example.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.K3rXDqnGhVH5Oa',
        'Regular User',
        'user',
        true,
        NOW()
    )
ON CONFLICT (username) DO NOTHING;
