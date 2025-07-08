# Fastag API Postman Collection Setup

This directory contains the complete Postman collection and environment files for the Fastag RFID toll collection system.

## Files Included

1. **Fastag_API_Collection.json** - Main API collection with all endpoints
2. **Fastag_Production_Environment.json** - Production environment (https://fastag.onebee.in)
3. **Fastag_Development_Environment.json** - Development environment (http://localhost:5000)
4. **Fastag_Local_Network_Environment.json** - Local network environment (http://192.168.1.8:5000)

## Setup Instructions

### Step 1: Import the Collection
1. Open Postman
2. Click "Import" button
3. Select "Upload Files"
4. Choose `Fastag_API_Collection.json`
5. Click "Import"

### Step 2: Import Environments
1. In Postman, go to "Environments" tab
2. Click "Import" button
3. Import each environment file:
   - `Fastag_Production_Environment.json`
   - `Fastag_Development_Environment.json`
   - `Fastag_Local_Network_Environment.json`

### Step 3: Select Environment
1. In the top-right corner of Postman, select the appropriate environment:
   - **Production**: Use for testing against https://fastag.onebee.in
   - **Development**: Use for local development (localhost:5000)
   - **Local Network**: Use for testing on local network (192.168.1.8:5000)

## Environment URLs

| Environment | Base URL | Use Case |
|-------------|----------|----------|
| Production | https://fastag.onebee.in | Live production testing |
| Development | http://localhost:5000 | Local development |
| Local Network | http://192.168.1.8:5000 | Network testing |

## API Categories

The collection includes APIs organized into the following categories:

1. **Analytics APIs** - Dashboard data and exports
2. **Device Management APIs** - RFID device configuration
3. **Barrier Control APIs** - Physical barrier control
4. **RFID Power APIs** - RF power management
5. **Vehicle Finder APIs** - Vehicle information lookup
6. **Bank Finder APIs** - Bank information lookup
7. **FASTag Balance APIs** - Balance checking
8. **KYC Users APIs** - User management
9. **Admin APIs** - System administration
10. **User Authentication APIs** - User session management

## Authentication

Some APIs require authentication:
1. First use the web interface to log in
2. The session will be maintained for API calls
3. Admin APIs require proper user session

## Testing Tips

1. **Start with Health Checks**: Use `/device/status` to verify connectivity
2. **Test Authentication**: Use `/api/user-info` to check login status
3. **Use Sample Data**: The collection includes example request bodies
4. **Check Responses**: All APIs return JSON responses with success/error indicators

## Troubleshooting

- **Connection Issues**: Verify the base URL is correct for your environment
- **Authentication Errors**: Ensure you're logged in via web interface first
- **CORS Issues**: Some APIs may require proper headers
- **Port Issues**: Ensure the correct port (5000) is being used

## API Documentation

Each API in the collection includes:
- Detailed description
- Required parameters
- Example request bodies
- Expected response format

For detailed API documentation, refer to the individual route files in the `fastag/routes/` directory. 