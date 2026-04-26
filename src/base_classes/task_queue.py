from collections.abc import Iterable, Iterator, Callable
from src.base_classes.task import Task
from src.base_classes.enums import TaskStatus
from src.base_classes.task_manager import TaskManager


class TaskQueueIterator(Iterator[Task]):
    """Итератор с поддержкой ленивого кэширования."""
    def __init__(self, queue: "TaskQueue"):
        self._queue = queue
        self._index = 0
        self._source_exhausted = False

    def __next__(self) -> Task:
        # если задача есть в кэшэ, возвращаем ее оттуда
        if self._index < len(self._queue._cache):
            task = self._queue._cache[self._index]
            self._index += 1
            return task
        # если источник полностью исчерпан, завершаем
        if self._source_exhausted or self._queue._fully_consumed:
            raise StopIteration

        # читаем следующую задачу из источника, возможно в кэше они ещё не появились
        try:
            task = next(self._queue._task_iterator)
            self._queue._cache.append(task)
            self._index += 1
            return task
        except StopIteration:
            self._source_exhausted = True
            self._queue._fully_consumed = True
            raise


class TaskQueue:
    """
    Очередь задач с поддержкой многократной итерации, ленивых фильтров.
    Использует lazy caching для соответствия требованиям лабораторной.
    """
    def __init__(self, manager: "TaskManager"):
        self._manager: "TaskManager" = manager
        self._cache: list[Task] = []
        self._fully_consumed: bool = False
        self._task_iterator: Iterator[Task] | None = None

    def __iter__(self) -> Iterator[Task]:
        """
        Важно: каждый вызов __iter__() возвращает новый итератор.
        При этом переиспользуем уже накопленный кэш.
        """
        if self._task_iterator is None and not self._fully_consumed:
            self._task_iterator = iter(self._manager.iter_tasks())  # важно использовать iter()

        return TaskQueueIterator(self)

    # ====================== ЛЕНИВЫЕ ФИЛЬТРЫ ======================

    def filter(self, predicate: Callable[[Task], bool]) -> Iterable[Task]:
        """Универсальный ленивый фильтр."""
        for task in self:          # здесь используется наш __iter__
            if predicate(task):
                yield task

    def filter_by_status(self, status: TaskStatus | str) -> Iterable[Task]:
        if isinstance(status, str):
            try:
                status = TaskStatus(status.upper())
            except ValueError:
                status = TaskStatus.PENDING

        return self.filter(lambda t: t.status == status)

    def filter_by_priority(self, min_priority: int = 1, max_priority: int = 5) -> Iterable[Task]:
        return self.filter(lambda t: min_priority <= t.priority <= max_priority)

    def filter_by_author(self, author: str) -> Iterable[Task]:
        author_lower = author.strip().lower()
        return self.filter(lambda t: t.author.lower() == author_lower)

    def filter_by_title_contains(self, substring: str) -> Iterable[Task]:
        substring_lower = substring.lower()
        return self.filter(lambda t: substring_lower in t.title.lower())

    # ====================== Удобные методы ======================

    def pending(self) -> Iterable[Task]:
        return self.filter_by_status(TaskStatus.PENDING)

    def in_progress(self) -> Iterable[Task]:
        return self.filter_by_status(TaskStatus.IN_PROGRESS)

    def done(self) -> Iterable[Task]:
        return self.filter_by_status(TaskStatus.DONE)

    def high_priority(self) -> Iterable[Task]:
        return self.filter_by_priority(min_priority=4)

    def __repr__(self) -> str:
        cached = len(self._cache)
        status = " (fully consumed)" if self._fully_consumed else " (+ source available)"
        return f"TaskQueue({cached} tasks cached{status})"

    def reset(self) -> None:
        """Сбрасывает кэш"""
        self._cache.clear()
        self._fully_consumed = False
        self._task_iterator = None