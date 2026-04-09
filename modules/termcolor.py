import json

class termcolor:
    dark = "\x1b[1;30m"
    red = "\x1b[1;31m"
    green = "\x1b[1;32m"
    yellow = "\x1b[1;33m"
    blue = "\x1b[1;34m"
    magenta = "\x1b[1;35m"
    cyan = "\x1b[1;36m"
    white = "\x1b[1;37m"

    orange = "\x1b[1;38;5;202m"
    blpurple = "\x1b[1;38;5;105m"
    lightblue = "\x1b[1;38;5;45m"

    reset = "\x1b[0m"

    @staticmethod
    def success(data):
        print(f"{termcolor.green}{data}{termcolor.reset}")

    @staticmethod
    def error(data):
        print(f"{termcolor.red}{data}{termcolor.reset}")

    @staticmethod
    def info(data):
        print(f"{termcolor.blue}{data}{termcolor.reset}")

    @staticmethod
    def warning(data):
        print(f"{termcolor.yellow}{data}{termcolor.reset}")

    @staticmethod
    def process(data):
        print(f"{termcolor.cyan}{data}{termcolor.reset}")

    @staticmethod
    def debug(data):
        print(f"{termcolor.dark}{data}{termcolor.reset}")

    @staticmethod
    def notice(data):
        print(f"{termcolor.magenta}{data}{termcolor.reset}")

    @staticmethod
    def finish(data):
        print(f"{termcolor.orange}{data}{termcolor.reset}")

    @staticmethod
    def report(title, data, extra=None):
        if extra:
            print(f"[+] {termcolor.cyan}{title}: {termcolor.blpurple}{data} {termcolor.orange}[{extra}]{termcolor.reset}")

        else:
            print(f"[+] {termcolor.cyan}{title}: {termcolor.blpurple}{data}{termcolor.reset}")

    @staticmethod
    def column(title, data):
        print(f"[+] {termcolor.blue}{title}: {termcolor.blpurple}{data}{termcolor.reset}")


    @staticmethod
    def objdump(data):
        print(json.dumps(data, indent=2, default=str))
