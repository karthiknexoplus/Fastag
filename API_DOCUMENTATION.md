# FASTag Device API Documentation

This API allows external FASTag reader devices to lookup their configuration and register with the system.

## Base URL
```
http://localhost:8000/api
```

## Endpoints

### 1. Health Check
**GET** `/device/status`

Check if the API is online and responding.

**Response:**
```json
{
  "success": true,
  "status": "online",
  "service": "FASTag Device Lookup API"
}
```

### 2. Device Lookup
**POST** `/device/lookup`

Lookup device configuration based on MAC address.

**Request Body:**
```json
{
  "mac_address": "00:1A:2B:3C:4D:5E"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "reader_id": 1,
    "mac_address": "00:1A:2B:3C:4D:5E",
    "reader_ip": "192.168.1.100",
    "type": "entry",
    "lane": {
      "id": 1,
      "lane_name": "Main Entry",
      "location": {
        "id": 1,
        "name": "Central Parking",
        "site_id": "CP001"
      }
    }
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": "Device not found",
  "mac_address": "00:1A:2B:3C:4D:5E"
}
```

### 3. Device Registration
**POST** `/device/register`

Check if a device is registered in the system.

**Request Body:**
```json
{
  "mac_address": "00:1A:2B:3C:4D:5E",
  "type": "reader"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Device already registered",
  "mac_address": "00:1A:2B:3C:4D:5E"
}
```

**Not Found Response (404):**
```json
{
  "success": false,
  "error": "Device not found in system. Please register through admin panel first.",
  "mac_address": "00:1A:2B:3C:4D:5E"
}
```

## Usage Examples

### Python
```python
import requests

# Device lookup
response = requests.post('http://localhost:8000/api/device/lookup', 
                        json={'mac_address': '00:1A:2B:3C:4D:5E'})
data = response.json()

if data['success']:
    device_info = data['data']
    print(f"Device found: {device_info['lane']['lane_name']}")
```

### cURL
```bash
# Health check
curl -X GET http://localhost:8000/api/device/status

# Device lookup
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "00:1A:2B:3C:4D:5E"}'
```

### JavaScript
```javascript
// Device lookup
fetch('http://localhost:8000/api/device/lookup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mac_address: '00:1A:2B:3C:4D:5E'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Device found:', data.data);
  }
});
```

## MAC Address Format

The API accepts MAC addresses in various formats and normalizes them:
- `00:1A:2B:3C:4D:5E` (with colons)
- `00-1A-2B-3C-4D-5E` (with dashes)
- `001A2B3C4D5E` (without separators)

All formats are converted to the standard colon-separated format for database lookup.

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing or invalid data)
- `404`: Not Found (device not in system)
- `500`: Internal Server Error

## Testing

Use the provided `test_api.py` script to test the API endpoints:

```bash
python test_api.py
```

## Security Notes

- This API is designed for internal network use
- No authentication is currently implemented
- Consider adding API keys or IP whitelisting for production use
- All requests are logged for debugging purposes 