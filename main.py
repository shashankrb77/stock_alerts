from dotenv import load_dotenv
from anchor_lockin import anchor_lockin
from ipo_close import ipo_close


if __name__ == "__main__":
    load_dotenv()
    anchor_lockin()
    ipo_close()