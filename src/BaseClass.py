import logging


class BaseClass:
    """
    A BaseClass defined by logging capabilities across levels, plus optional stdout printing.

    Inherited by all other classes

    """
    def stdout(self, msg: str = "", log_level: str = "INFO", print_enabled: bool = True):
        """
        Output strings

        :param msg: The message for the output
        :param log_level: Set a loglevel: DEBUG, INFO, WARNING, ERROR, CRITICAL
        :param print_enabled: Set to True to enable printing the msg string
        """
        if print_enabled:
            print(f"{msg}")
        if log_level == "DEBUG":
            logging.debug(f"{msg}")
        elif log_level == "INFO":
            logging.info(f"{msg}")
        elif log_level == "WARNING":
            logging.warning(f"{msg}")
        elif log_level == "ERROR":
            logging.error(f"{msg}")
        elif log_level == "CRITICAL":
            logging.critical(f"{msg}")