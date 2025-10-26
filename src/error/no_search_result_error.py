class NoSearchResultError(Exception):
    def __str__(self) -> str:
        return "No search results found."
