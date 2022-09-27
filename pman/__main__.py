import os
from pman.app import create_app


def main():
    """
    Run pman in development mode.
    """
    if 'APPLICATION_MODE' not in os.environ:
        os.environ['APPLICATION_MODE'] = 'dev'
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5010)))


if __name__ == '__main__':
    main()
