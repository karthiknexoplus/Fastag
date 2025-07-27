from fastag import create_app
 
app = create_app()
with app.test_client() as client:
    response = client.get('/analytics/api/denied-fastag-activity-feed')
    print('Status:', response.status_code)
    print('Response:', response.get_json()) 