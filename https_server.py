from fastag import create_app
import ssl

app = create_app()

if __name__ == '__main__':
    # SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('ssl/cert.pem', 'ssl/key.pem')
    
    # Run with HTTPS
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=8444,
        ssl_context=context
    )
