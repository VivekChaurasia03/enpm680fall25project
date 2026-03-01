"""
Development server runner with graceful shutdown
Usage: python run.py
"""
import signal
import sys
import uvicorn


def signal_handler(sig, frame):
    """
    Handle CTRL+C (SIGINT) and SIGTERM gracefully
    """
    print("\n\n🛑 Shutdown signal received. Stopping server gracefully...")
    print("⏳ Waiting for active connections to finish...")
    sys.exit(0)


def main():
    """
    Main function to run the development server
    """
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Handle CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal
    
    print("=" * 70)
    print("🚀 Starting FleetWise Development Server")
    print("=" * 70)
    print("📍 Server: http://0.0.0.0:8000")
    print("📚 API Docs: http://0.0.0.0:8000/docs")
    print("📖 ReDoc: http://0.0.0.0:8000/redoc")
    print("=" * 70)
    print("ℹ️  Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped successfully!")
    except Exception as e:
        print(f"\n\n❌ Server stopped with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()