class RepositoryError(Exception):
    pass


class NotFoundError(RepositoryError):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(f"{resource} {identifier} wurde nicht gefunden.")
        self.resource = resource
        self.identifier = identifier


class ConflictError(RepositoryError):
    pass


class VersionConflictError(ConflictError):
    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            f"{resource} {identifier} wurde zwischenzeitlich geändert. "
            "Bitte den Datensatz neu laden und die Änderung erneut senden."
        )
