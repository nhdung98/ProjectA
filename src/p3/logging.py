"""Mirror terminal output and uncaught errors into one log per invocation."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import sys
import traceback
import uuid


def member_log_folder(folder, arguments):
    """Resolve member folders before importing ML dependencies or parsing the full CLI."""
    for index, argument in enumerate(arguments):
        value = None
        if argument == '--member' and index + 1 < len(arguments):
            value = arguments[index + 1]
        elif argument.startswith('--member='):
            value = argument.partition('=')[2]
        if value in {'1', '2', '3', '4'}:
            return folder / f'member{value}'
    return folder


class Tee:
    def __init__(self, terminal, log):
        self.terminal, self.log = terminal, log

    def write(self, text):
        self.terminal.write(text)
        self.log.write(text)
        self.log.flush()
        return len(text)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def __getattr__(self, name):
        return getattr(self.terminal, name)


def logged_main(main, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8] + '.log')
    with path.open('x', encoding='utf-8') as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            print(f'Log file: {path.resolve()}', flush=True)
            print(f'Arguments: {sys.argv[1:]!r}', flush=True)
            try:
                main()
            except BaseException as error:
                if not isinstance(error, SystemExit) or error.code not in (None, 0):
                    traceback.print_exc()
                print(f'Log saved: {path.resolve()}', flush=True)
                if isinstance(error, SystemExit):
                    raise
                raise SystemExit(130 if isinstance(error, KeyboardInterrupt) else 1) from None
            print(f'Completed. Log saved: {path.resolve()}', flush=True)
