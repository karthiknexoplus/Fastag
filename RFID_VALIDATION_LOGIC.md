# RFID Validation Logic - Fastag Project

## Overview

This document explains the RFID validation logic adapted for the current Fastag project, which uses a simplified database schema compared to the original complex system. **Reader configurations are now dynamically loaded from the database instead of being hardcoded.**

## Database Schema

### Current Tables Used for Validation

#### 1. `kyc_users` Table
```sql
CREATE TABLE kyc_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    fastag_id TEXT UNIQUE NOT NULL,
    vehicle_number TEXT NOT NULL,
    contact_number TEXT NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Stores authorized users with their FASTag IDs and vehicle information.

#### 2. `access_logs` Table
```sql
CREATE TABLE access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id TEXT NOT NULL,
    reader_id INTEGER NOT NULL,
    lane_id INTEGER NOT NULL,
    access_result TEXT NOT NULL CHECK (access_result IN ('granted', 'denied')),
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reader_id) REFERENCES readers (id),
    FOREIGN KEY (lane_id) REFERENCES lanes (id)
);
```

**Purpose**: Logs all access attempts for audit and monitoring.

#### 3. `readers` Table
```sql
CREATE TABLE readers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lane_id INTEGER NOT NULL,
    mac_address TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('entry', 'exit')),
    reader_ip TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lane_id) REFERENCES lanes (id) ON DELETE CASCADE,
    UNIQUE(lane_id, type)
);
```

**Purpose**: Maps RFID readers to lanes and locations with dynamic IP configuration.

#### 4. `lanes` Table
```sql
CREATE TABLE lanes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    lane_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE CASCADE
);
```

**Purpose**: Defines parking lanes within locations.

#### 5. `locations` Table
```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    site_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Defines parking locations/sites.

## Dynamic Reader Configuration

### Database-Driven Setup
```python
def setup_readers(self):
    """Dynamically load reader configurations from database"""
    try:
        # Query all readers with their lane and location information
        readers_data = db.execute("""
            SELECT 
                r.id as reader_id,
                r.reader_ip,
                r.mac_address,
                r.type,
                r.lane_id,
                l.lane_name,
                loc.name as location_name
            FROM readers r
            JOIN lanes l ON r.lane_id = l.id
            JOIN locations loc ON l.location_id = loc.id
            ORDER BY r.id
        """).fetchall()
        
        for reader_data in readers_data:
            reader = RFIDReader(
                ip_address=reader_data['reader_ip'],
                reader_id=reader_data['reader_id'],
                lane_id=reader_data['lane_id'],
                device_id=reader_data['reader_id'],
                dll_path=f"./libSWNetClientApi{reader_data['reader_id']}.so"
            )
            self.readers.append(reader)
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        self.readers = []
```

### Individual Reader Services
Each reader service (reader1, reader2) also loads its configuration dynamically:

```python
def load_reader_config(reader_id):
    """Load specific reader configuration from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT r.reader_ip, r.type, r.lane_id, l.lane_name, loc.name
        FROM readers r
        JOIN lanes l ON r.lane_id = l.id
        JOIN locations loc ON l.location_id = loc.id
        WHERE r.id = ?
    """, (reader_id,))
    return c.fetchone()
```

## Database Path Configuration

### Correct Database Paths
All RFID services use the same database path that matches deploy.sh:

```python
# Main RFID service
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'fastag.db'))

# Individual reader services
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'fastag.db'))
```

## Validation Process Flow

### 1. Tag Detection
```python
def read_tags(self):
    # Hardware reads RFID tags
    # Returns: [{'tag_id': '123456', 'antenna': 1, 'rssi': -45}, ...]
```

### 2. Database Validation
```python
def verify_tag_in_database(self, tag_id):
    # Check kyc_users table for authorized tag
    user = db.execute('SELECT * FROM kyc_users WHERE fastag_id = ?', (tag_id,)).fetchone()
    
    if user:
        return {
            'found': True,
            'user': user,
            'message': f"Access granted for vehicle {user['vehicle_number']} - {user['name']}"
        }
    else:
        return {
            'found': False,
            'message': f"Access denied - Tag {tag_id} not found in database"
        }
```

### 3. Access Control Logic

#### Cooldown System
- **Tag Cooldown**: 3 seconds between same tag reads
- **Cross-Lane Block**: 20 seconds to prevent same tag in different lanes
- **DB Insert Limit**: Maximum 3 records per tag/lane per session

```python
def is_tag_in_cooldown(self, tag_id):
    if tag_id in self.tag_cooldowns:
        time_since_last = time.time() - self.tag_cooldowns[tag_id]
        if time_since_last < self.tag_cooldown_duration:
            return True, self.tag_cooldown_duration - time_since_last
    return False, 0
```

#### Cross-Lane Protection
```python
def cross_lane_recent(self, tag_id, current_lane_id):
    for (tid, lid), info in self.last_db_insert.items():
        if tid == tag_id and lid != current_lane_id:
            if time.time() - info['time'] < self.CROSS_LANE_SECONDS:
                return True
    return False
```

### 4. Access Decision Process

```python
def process_tag(self, tag_data):
    tag_id = tag_data['tag_id']
    lane_id = tag_data['lane_id']
    
    # 1. Cross-lane check
    if self.cross_lane_recent(tag_id, lane_id):
        self.log_access_async(tag_id, None, 'cross_lane_blocked', reader_id, lane_id, device_id)
        return
    
    # 2. Cooldown check
    if self.is_tag_in_cooldown(tag_id):
        self.log_access_async(tag_id, None, 'cooldown_active', reader_id, lane_id, device_id)
        return
    
    # 3. Database validation
    result = self.verify_tag_in_database(tag_id)
    
    # 4. Access decision
    if result['found']:
        self.activate_barrier()
        self.log_access_async(tag_id, result['user'], 'granted', reader_id, lane_id, device_id)
    else:
        self.log_access_async(tag_id, None, 'denied', reader_id, lane_id, device_id)
```

## Reader Configuration Management

### Database Configuration
```sql
-- Sample location
INSERT INTO locations (name, address, site_id) 
VALUES ('Main Parking Lot', '123 Main Street', 'SITE001');

-- Sample lanes
INSERT INTO lanes (location_id, lane_name) VALUES (1, 'Entry Lane');
INSERT INTO lanes (location_id, lane_name) VALUES (1, 'Exit Lane');

-- Sample readers (dynamically configured)
INSERT INTO readers (lane_id, mac_address, type, reader_ip) 
VALUES (1, '00:11:22:33:44:55', 'entry', '192.168.60.250');

INSERT INTO readers (lane_id, mac_address, type, reader_ip) 
VALUES (2, '00:11:22:33:44:66', 'exit', '192.168.60.251');
```

## Access Logging

### Log Entry Structure
```python
def log_access_async(self, tag_id, user, status, reader_id, lane_id, device_id):
    db.execute("""
        INSERT INTO access_logs (tag_id, reader_id, lane_id, access_result, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tag_id, reader_id, lane_id, status, None, datetime.now()))
```

### Access Result Types
- `granted`: Successful access
- `denied`: Tag not found in database
- `cross_lane_blocked`: Tag used in different lane recently
- `cooldown_active`: Tag used too recently

## Security Features

### 1. Duplicate Prevention
- Unique tag processing within reading cycles
- Cooldown periods prevent rapid re-use
- Cross-lane protection prevents tag sharing

### 2. Buffer Management
- Automatic buffer clearing after access decisions
- Overflow protection for multiple tag reads
- Connection health monitoring

### 3. Audit Trail
- Complete access logging
- User identification for granted access
- Timestamp tracking for all events

## Error Handling

### Database Errors
```python
try:
    # Database operations
    return {'found': True, 'user': user}
except Exception as e:
    logger.error(f"Database error: {str(e)}")
    return {'found': False, 'message': f"Database error: {str(e)}"}
```

### Reader Connection Issues
- Automatic reconnection attempts
- Connection health monitoring
- Graceful degradation when readers are unavailable

## Integration Points

### Web Interface
- KYC user management through `/kyc_users` route
- Access log viewing through admin interface
- Reader configuration through `/readers/<lane_id>` route

### API Endpoints
- `/api/device/lookup`: Device registration and lookup
- `/api/barrier-control`: Relay control for barrier activation

## Configuration

### Cooldown Settings
```python
self.tag_cooldown_duration = 3  # 3 seconds
self.CROSS_LANE_SECONDS = 20    # 20 seconds
self.MAX_DB_RECORDS = 3         # Max records per session
```

### Reader Settings
```python
self.connection_check_interval = 30  # 30 seconds
self.buffer_clear_threshold = 5      # Clear buffer if >5 tags
self.heartbeat_interval = 60         # 60 seconds
```

## Testing

### Test Script
Run the test script to verify RFID setup:

```bash
python test_rfid_setup.py
```

This will test:
- Database connection and table creation
- RFID service imports
- Database paths
- Logging directory creation

## Monitoring and Logging

### Log Files
- `logs/rfid.log`: Main RFID service logs
- `logs/rfid_reader1.log`: Reader 1 specific logs
- `logs/rfid_reader2.log`: Reader 2 specific logs

### Log Levels
- **INFO**: Access decisions, user identification, configuration loading
- **WARNING**: Cooldown activations, cross-lane blocks
- **ERROR**: Database errors, connection failures, configuration errors
- **DEBUG**: Detailed processing information

This adapted validation system provides secure, reliable access control with dynamic configuration management while maintaining simplicity and compatibility with the current Fastag project structure. 