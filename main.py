import database, logging

from dotenv import load_dotenv


log = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.DEBUG)
    load_dotenv()
    log.debug("Loaded environment variables from .env file")
    database.init()


if __name__ == "__main__":
    main()