

class InvalidQueryException(Exception):
    def __init__(self, q):
        self.args = (
            f"Invalid Query Format: {q}",
        )