# Badge Icons

This directory contains custom badge icons for the screen time competition app.

## Badge Icon Requirements

- **Format:** PNG
- **Size:** Recommended 128x128px minimum
- **Naming:** kebab-case matching badge names (e.g., `first-friend-icon.png`)
- **Transparent background** preferred

## Badge List (23 total)

### Streak Badges (6)
- `fresh-start-icon.png` - Complete your first day meeting your screen-time goal
- `weekend-warrior-icon.png` - Hit your goal on a Saturday and Sunday
- `7-day-focus-icon.png` - 7 days in a row hitting daily goal
- `habit-builder-icon.png` - 14-day streak
- `unstoppable-icon.png` - 30-day streak
- `bounce-back-icon.png` - Lose a streak, then start a new one the next day

### Reduction Badges (5)
- `tiny-wins-icon.png` - Reduce total time by 5% from your baseline week
- `the-declutter-icon.png` - Reduce total screen time by 10% from baseline
- `half-life-icon.png` - Reduce screen time by 50% from baseline
- `one-hour-club-icon.png` - Stay under 1h of social media in a day
- `digital-minimalist-icon.png` - Average < 2 hours/day over a whole week

### Social Badges (5)
- `team-player-icon.png` - Add your first friend
- `the-connector-icon.png` - Add 10 friends
- `challenge-accepted-icon.png` - Join your first challenge
- `friendly-rival-icon.png` - Participate in 5 challenges
- `community-champion-icon.png` - Win a weekly challenge among friends

### Leaderboard Badges (4)
- `top-10-icon.png` - Be in top 10% of the leaderboard in a week
- `top-3-icon.png` - Finish as #1, #2, or #3 among friends
- `the-phantom-icon.png` - Win a challenge with the lowest screen time without chatting
- `comeback-kid-icon.png` - Go from bottom half to top 3 in the next challenge

### Prestige Badges (3)
- `offline-legend-icon.png` - Average < 2h/day for a full month
- `master-of-attention-icon.png` - Maintain a 30-day goal streak and < 2h/day average
- `life-screen-icon.png` - Complete a full 24h digital detox

### Special Icons
- `lock-icon.png` - Used for locked badges
- `trophy-icon.png` - Trophy/leaderboard stat icon
- `streak-icon.png` - Streak/fire stat icon
- `friends-icon.png` - Friends/social stat icon

## Implementation

The Profile.jsx component uses `getBadgeIconPath()` to dynamically load these images. If an icon is missing, it falls back to emoji icons from the BADGE_ICONS map.
