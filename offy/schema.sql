-- SQLite schema for Offy (derived from er.dot)
PRAGMA foreign_keys = ON;

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    profile_picture TEXT,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    streak_count INTEGER NOT NULL DEFAULT 0,
    total_points INTEGER NOT NULL DEFAULT 0
);

-- Screen time logs
CREATE TABLE IF NOT EXISTS screen_time_logs (
    log_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    screen_time_minutes INTEGER NOT NULL DEFAULT 0,
    uploaded_image TEXT,
    ocr_extracted INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_screen_time_logs_user_date ON screen_time_logs(user_id, date);

-- Goals
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    goal_type TEXT NOT NULL CHECK(goal_type IN ('daily','weekly')),
    target_minutes INTEGER NOT NULL DEFAULT 0,
    start_date DATE,
    end_date DATE,
    achieved INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);

-- Rewards
CREATE TABLE IF NOT EXISTS rewards (
    reward_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reward_type TEXT NOT NULL CHECK(reward_type IN ('streak','goal','challenge')),
    description TEXT,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    date_awarded DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_rewards_user ON rewards(user_id);

-- Friendships
CREATE TABLE IF NOT EXISTS friendships (
    friendship_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    friend_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','accepted','blocked')),
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (friend_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK(user_id <> friend_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_friendships_pair ON friendships(user_id, friend_id);

-- Challenges
CREATE TABLE IF NOT EXISTS challenges (
    challenge_id TEXT PRIMARY KEY,
    creator_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    metric TEXT NOT NULL CHECK(metric IN ('total_time','app_specific','goal_streak')),
    start_date DATE,
    end_date DATE,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (creator_id) REFERENCES users(user_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_challenges_creator ON challenges(creator_id);

-- Challenge participants
CREATE TABLE IF NOT EXISTS challenge_participants (
    participant_id TEXT PRIMARY KEY,
    challenge_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    total_screen_time INTEGER NOT NULL DEFAULT 0,
    rank INTEGER,
    completed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_challenge_participants_challenge ON challenge_participants(challenge_id);
CREATE INDEX IF NOT EXISTS idx_challenge_participants_user ON challenge_participants(user_id);

-- Leaderboard snapshots
CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    challenge_id TEXT NOT NULL,
    week_start DATE NOT NULL,
    generated_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    data_json TEXT NOT NULL CHECK(json_valid(data_json)),
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_leaderboard_snapshots_challenge_week ON leaderboard_snapshots(challenge_id, week_start);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('goal_update','friend_request','challenge_invite','reward')),
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);

-- Optional: convenience view for user summary
CREATE VIEW IF NOT EXISTS user_summary AS
SELECT
    u.user_id,
    u.username,
    u.email,
    u.streak_count,
    u.total_points,
    (SELECT COUNT(*) FROM friendships f WHERE f.user_id = u.user_id AND f.status = 'accepted') AS friends_count,
    (SELECT COUNT(*) FROM challenges c WHERE c.creator_id = u.user_id) AS challenges_created
FROM users u;
