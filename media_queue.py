class Queue:
    """Media playing queue for ushiko

    === Attributes ===
    _queue: FIFO, implemented with python list
    looping: boolean indicating whether the user is looping
    current_song: the current song played by the user
    """
    _queue: list
    is_looping: bool
    is_paused: bool
    current_song: str

    def __init__(self):
        """Initialize a queue

        """
        self._queue = []
        self.is_looping = False
        self.current_song = ""
        self.is_paused = False

    def dequeue(self):
        """Return the first added track

        Precondition: queue is not empty
        """
        self.current_song = self._queue.pop(0)
        return self.current_song

    def enqueue(self, url):
        """Add <url> to the end of queue

        """
        self._queue.append(url)

    def enqueue_with_priority(self, url):
        """Add <url> to the front of queue

        """
        self._queue.insert(0, url)

    def is_empty(self) -> bool:
        """Return True if queue is empty, return False otherwise

        """
        return self._queue == []

    def clear(self):
        """Clear the queue

        """
        self._queue.clear()

    def get_list(self):
        """Return the list object that stores the queue

        """
        return self._queue

    def remove(self, index):
        """Remove the item in queue at index

        """
        self._queue.remove(index-1)
