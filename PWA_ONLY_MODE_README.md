# PWA-Only Mode

This feature allows you to temporarily disable all non-PWA routes, so only `/get-the-app` and PWA-related routes work.

## How to Enable PWA-Only Mode

### Method 1: Using the shell script (Recommended)
```bash
# Enable PWA-only mode
./toggle_pwa_only.sh enable

# Run the app with PWA-only mode
PWA_ONLY_MODE=true python3 wsgi.py

# Disable PWA-only mode
./toggle_pwa_only.sh disable
```

### Method 2: Using environment variable directly
```bash
# Enable PWA-only mode
export PWA_ONLY_MODE=true
python3 wsgi.py

# Disable PWA-only mode
export PWA_ONLY_MODE=false
python3 wsgi.py
```

### Method 3: Using Python scripts
```bash
# Enable PWA-only mode
python3 enable_pwa_only.py

# Disable PWA-only mode
python3 disable_pwa_only.py
```

## What Happens in PWA-Only Mode

When PWA-only mode is enabled:

✅ **Working Routes:**
- `/get-the-app` - PWA landing page
- `/pwa-login` - PWA login page
- `/pwa-dashboard` - PWA dashboard
- `/pwa-logout` - PWA logout
- `/pwa-dashboard/*` - All PWA dashboard routes
- `/pwa/vehicle-finder` - PWA vehicle finder
- `/sw.js` - Service worker
- `/firebase-messaging-sw.js` - Firebase messaging service worker

❌ **Disabled Routes (redirect to `/get-the-app`):**
- `/` - Home page
- `/home` - Home page
- `/login` - Regular login
- `/signup` - Signup page
- `/logout` - Regular logout
- `/audit-log` - Audit log
- `/watchlist` - Watchlist
- `/onboarding` - Onboarding
- All other non-PWA routes

## Benefits

1. **Security**: Prevents access to admin/management interfaces
2. **Focus**: Users can only access the PWA functionality
3. **Testing**: Easy to test PWA-only experience
4. **Temporary**: Can be easily disabled without code changes

## Implementation Details

- Uses environment variable `PWA_ONLY_MODE`
- Checks are added to route handlers in `fastag/routes/auth.py`
- Non-PWA routes redirect to `/get-the-app` when mode is enabled
- PWA routes are unaffected
- No code deletion - routes are just temporarily disabled

## Usage Examples

```bash
# Start server in PWA-only mode
PWA_ONLY_MODE=true python3 wsgi.py

# Start server with all routes enabled
PWA_ONLY_MODE=false python3 wsgi.py

# Check current mode
echo $PWA_ONLY_MODE
``` 