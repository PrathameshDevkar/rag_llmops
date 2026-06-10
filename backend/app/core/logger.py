import logging
import sys
from colorama import Fore, init

# Initialize colorama for safe cross-platform terminal coloring
init(autoreset=True)

class ProductionFormatter(logging.Formatter):
    """ Custom formatter adding structured visual context to local terminal logs """
    
    LEVEL_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Fore.RED
    }

    def format(self, record):
        log_color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        
        # Define structural layout pattern
        log_format = (
            f"{Fore.LIGHTBLACK_EX}[%(asctime)s]{Fore.RESET} "
            f"{log_color}[%(levelname)s]{Fore.RESET} "
            f"{Fore.CYAN}(%(name)s:%(funcName)s:%(lineno)d){Fore.RESET} "
            f"─ %(message)s"
        )
        
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logging():
    """ Initializes global logger configurations across the application lifecycle """
    root_logger = logging.getLogger()
    
    # Avoid duplicate handlers if re-initialized
    if root_logger.hasHandlers():
        return
        
    root_logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ProductionFormatter())
    
    root_logger.addHandler(handler)
    
    # Mute overly verbose third-party engine logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Initialize logs on module import
setup_logging()