# FASTag Device API - cURL Commands for Postman

## Base URL
```
http://localhost:8000/api
```

## 1. Health Check
```bash
curl -X GET http://localhost:8000/api/device/status
```

**Expected Response:**
```json
{
  "success": true,
  "status": "online",
  "service": "FASTag Device Lookup API"
}
```

## 2. Device Lookup (Main Endpoint)

### Example 1: Valid MAC Address
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "00:1A:2B:3C:4D:5E"
  }'
```

### Example 2: MAC Address with Dashes
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "00-1A-2B-3C-4D-5E"
  }'
```

### Example 3: MAC Address without Separators
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "001A2B3C4D5E"
  }'
```

### Example 4: Invalid MAC Address (Not Found)
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "FF:FF:FF:FF:FF:FF"
  }'
```

**Expected Success Response:**
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

**Expected Error Response (404):**
```json
{
  "success": false,
  "error": "Device not found",
  "mac_address": "FF:FF:FF:FF:FF:FF"
}
```

## 3. Device Registration

### Example 1: Check if Device is Registered
```bash
curl -X POST http://localhost:8000/api/device/register \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "00:1A:2B:3C:4D:5E",
    "type": "reader"
  }'
```

### Example 2: Check Non-Registered Device
```bash
curl -X POST http://localhost:8000/api/device/register \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "FF:FF:FF:FF:FF:FF",
    "type": "reader"
  }'
```

## 4. Error Cases

### Missing MAC Address
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Invalid JSON
```bash
curl -X POST http://localhost:8000/api/device/lookup \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

## Postman Collection Setup

### Environment Variables
Set these in Postman:
- `base_url`: `http://localhost:8000`
- `api_url`: `{{base_url}}/api`

### Request Headers
```
Content-Type: application/json
```

### Test Scripts for Postman

#### For Device Lookup Success:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success flag", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(true);
});

pm.test("Response has device data", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.data).to.have.property('reader_id');
    pm.expect(jsonData.data).to.have.property('mac_address');
    pm.expect(jsonData.data).to.have.property('lane');
});
```

#### For Device Not Found:
```javascript
pm.test("Status code is 404", function () {
    pm.response.to.have.status(404);
});

pm.test("Response indicates device not found", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.success).to.eql(false);
    pm.expect(jsonData.error).to.include("Device not found");
});
```

## Notes for Testing

1. **Replace MAC Address**: Use a MAC address that exists in your database
2. **Database Setup**: Make sure you have at least one reader in your database
3. **Port**: Ensure the Flask app is running on port 8000
4. **CORS**: The API doesn't have CORS headers, so test from the same origin or disable CORS in Postman

## Quick Database Check
To see what MAC addresses are in your database, you can add a temporary endpoint or check through the web interface at `http://localhost:8000/readers/1` (replace 1 with an actual lane ID). 