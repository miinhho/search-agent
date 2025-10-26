class NoInputError(Exception):
    def __str__(self) -> str:
        return "No input provided."
