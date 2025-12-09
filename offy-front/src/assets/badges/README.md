# Badge Icons

This directory contains custom badge icons for the screen time competition app.

## Badge Icon Requirements

- **Format:** PNG
- **Size:** Recommended 128x128px minimum
- **Naming:** kebab-case matching badge names (e.g., `first-friend-icon.png`)
- **Transparent background** preferred

## Badge List (23 total)

### Streak Badges (7)
- `fresh-start-icon.png` - First day tracked
- `weekend-warrior-icon.png` - 2-day streak
- `7-day-focus-icon.png` - 7-day streak
- `30-day-focus-icon.png` - 30-day streak
- `consistency-king-icon.png` - 60-day streak
- `unstoppable-icon.png` - 100-day streak
- `legendary-streak-icon.png` - 365-day streak

### Reduction Badges (8)
- `digital-minimalist-icon.png` - 10% reduction
- `one-hour-club-icon.png` - 20% reduction
- `screen-time-slayer-icon.png` - 30% reduction
- `minimalism-master-icon.png` - 40% reduction
- `digital-detox-champion-icon.png` - 50% reduction
- `master-of-discipline-icon.png` - 60% reduction
- `total-freedom-icon.png` - 70% reduction

### Social Badges (3)
- `first-friend-icon.png` - 1 friend added
- `squad-goals-icon.png` - 5 friends
- `social-butterfly-icon.png` - 10 friends

### Leaderboard Badges (3)
- `top-3-icon.png` - Top 3 rank
- `champion-icon.png` - Rank 1
- `hall-of-fame-icon.png` - Rank 1 for 7 days

### Prestige Badges (2)
- `zen-master-icon.png` - 50 total badges
- `elite-status-icon.png` - 100 total badges
- `ultimate-dedication-icon.png` - 200 total badges

### Special Icons
- `lock-icon.png` - Used for locked badges
- `trophy-icon.png` - Trophy/leaderboard stat icon
- `streak-icon.png` - Streak/fire stat icon
- `friends-icon.png` - Friends/social stat icon

## Implementation

The Profile.jsx component uses `getBadgeIconPath()` to dynamically load these images. If an icon is missing, it falls back to emoji icons from the BADGE_ICONS map.
