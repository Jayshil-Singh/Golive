try:
    from app import create_app
    app = create_app()
except Exception as e:
    import sys
    print(f"Error importing create_app: {e}", file=sys.stderr)
    raise

if __name__ == '__main__':
    app.run() 