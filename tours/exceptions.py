class NotEnoughCapacityError(Exception):
    """Raised when a reservation asks for more seats than the slot has available."""

    def __init__(self, seats_available: int) -> None:
        self.seats_available = seats_available
        super().__init__(f'Only {seats_available} seats available.')
