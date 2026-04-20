import sys
from pathlib import Path
from typing import Any, Dict, Optional
import typer
from typer import Typer
from src.base_classes.task import Task
from src.base_classes.task_manager import TaskManager
from src.sources.registry import REGISTRY

# хранилище задач (для демонстрации)
tasks_storage: Dict[str, Task] = {}

cli = Typer(add_help_option=False, add_completion=False)


def display_task_info(task: Task) -> None:
    """Отображает информацию о задаче"""
    data = task.to_dict()

    print(f"Информация о задаче {data['id']}")
    print(f"ID:          {data['id']}")
    print(f"Название:    {data['title']}")
    print(f"Автор:       {data['author']}")
    print(f"Содержание:  {data['content']}")
    print(f"Приоритет:   {data['priority']} ({data['priority_label']})")
    print(f"Статус:      {data['status']}")
    print(f"Создана:     {data['created_at']}")
    print(f"Начата:      {data['started_at'] or 'Не начата'}")
    print(f"Завершена:   {data['completed_at'] or 'Не завершена'}")
    print(f"Возраст:     {data['age_seconds']:.1f} сек.")
    print(f"Длительность: {data['work_duration']:.1f} сек." if data['work_duration'] else "Длительность: Не завершена")


def display_all_tasks() -> None:
    """Отображает список всех задач"""
    if not tasks_storage:
        print("Нет созданных задач")
        return
    
    print("\n" + "-" * 90)
    print(f"{'ID':<15} {'Название':<30} {'Автор':<15} {'Статус':<15} {'Приоритет':<10}")
    print("-" * 90)
    
    for task in tasks_storage.values():
        title_display = task.title[:27] + "..." if len(task.title) > 30 else task.title
        print(f"{task.id:<15} {title_display:<30} {task.author:<15} {str(task.status):<15} {task.priority} ({task.priority_label})")
    
    print(f"Всего задач: {len(tasks_storage)}\n")


def get_task_or_exit(task_id: str) -> Optional[Task]:
    """Получает задачу по ID или выводит сообщение об ошибке"""
    if task_id not in tasks_storage:
        print(f"Ошибка: Задача с ID '{task_id}' не найдена")
        return None
    return tasks_storage[task_id]


def build_sources(stdin: bool, jsonl: list[Path]) -> list[Any]:
    """Создает источники задач"""
    sources: list[Any] = []
    for path in jsonl:
        sources.append(REGISTRY["jsonl-file"](path))
    if stdin:
        sources.append(REGISTRY["stdin"]())
    return sources

@cli.command("instruct")
def display_instructions() -> None:
    """Показывает подробную инструкцию по использованию"""
    print("""
Доступные команды:

1. instruct - Выводит это сообщение
    У этой команды нет опций или аргументов
    Пример: instruct

2. sources - Выводит список доступных источников задач
   Пример: sources

3. read - Читает и показывает задачи из указанных источников с возможностью фильтрации
    Аргументы и опции:
     --stdin              - Считывать задачи из стандартного ввода
     --max-tasks N        - Максимальное число задач (0 = без ограничения)
     --author TEXT        - Фильтр по автору
     --contains TEXT      - Фильтр по содержанию
     file1.jsonl          - Пути к JSONL файлам
    
    Подробно про аргументы и опции команды read:
          
    В качестве аргументов можно указать файлы формата jsonl, тогда задачи будут читаться из них.
    Примеры:
    read example_1.jsonl
    read example_1.jsonl example_2.jsonl
          
    --stdin - Считывать задачи из сдандартного ввода
    Задачи нужно писать в формате id:title:author:content:priority(число)
    Если вы захотите перестать вводить задачи, напишите stop
    Пример использования:
    read --stdin
    Дальше вводим задачи, например:   my_id:my_title:my_author:my_content:1
          
    --max_tasks - Установить максимум, сколько задач может быть прочитано
    По умолчанию 10, если поставить 0, то можно прочитать неограниченное число задач.
    При одновременном вводе --max_tasks 0 и --stdin не забывайте про возможность завершить ввод задач командой stop.
    Примеры:
    read --stdin --max-tasks 5
    read example_1.jsonl --max-tasks 0
          
    --author - Считывать задачи только указанного автора
    Пример:
    read --stdin --author milena
    Все встреченные задачи с другим автором не будут считываться программой
          
    --contains - Считывать только задачи с указанной подстрокой в содержании
    Пример:
    read example_1.jsonl --contains проект
    Задача '8:Сделать бэкап:milena:Сделать бэкап базы данных проекта:2' будет считана")
    Задача '9:Написать тесты:cool_user:Написать тесты к лабе по python:3' не считается")
          
    Все аргументы и опции можно комбинировать, примеры:
    read example_1.jsonl example_2.jsonl --max-tasks 20 --author kate
    read example_1.jsonl example_2.jsonl --stdin --max-tasks 20
    read example_1.jsonl --stdin --author alina --contains python

4. start TASK_ID - Начинает выполнение задачи
   Пример: start T-001

5. review TASK_ID - Отправляет задачу на ревью
   Пример: review PY_002

6. complete TASK_ID - Завершает задачу
   Пример: complete C_006

7. archive TASK_ID - Архивирует задачу
   Пример: archive T-007

8. info TASK_ID - Показывает подробную информацию о задаче
   Пример: info A111

9. list - Показывает список всех задач
   Пример: list

10. create - Создает новую задачу в интерактивном режиме
    Пример: create

11. exit - Выход из программы
    Пример: exit

""")


@cli.command("sources")
def list_sources() -> None:
    """Выводит список доступных источников"""
    print("Доступные источники:")
    for name in sorted(REGISTRY):
        print(f"  - {name}")

@cli.command("read")
def read_tasks(
    stdin: bool = typer.Option(False, "--stdin", help="Прочитать задачи из стандартного ввода"),
    jsonl: list[Path] = typer.Argument(
        None,
        help="Прочитать задачи из JSONL файлов",
    ),
    max_tasks: int = typer.Option(
        10,
        "--max-tasks",
        help="Максимальное число задач (0 = без ограничения)",
        min=0,
    ),
    author: Optional[str] = typer.Option(None, "--author", help="Читать задачи только от заданного автора"),
    contains: Optional[str] = typer.Option(None, "--contains", help="Читать только задачи, содержащие заданную подстроку"),
) -> None:
    """Читает задачи из указанных источников"""
    if not stdin and not jsonl:
        print("Ошибка: Укажите хотя бы один источник (--stdin или JSONL файлы)")
        return
    
    if jsonl is None:
        jsonl = []
    
    try:
        raw_sources = build_sources(stdin, jsonl)
        inbox = TaskManager(raw_sources)
        count = 0
        
        for tsk in inbox.iter_tasks():
            if author and author != tsk.author:
                continue
            if contains and contains not in tsk.content:
                continue
            
            if tsk.id in tasks_storage:
                print(f"Предупреждение: Задача с ID '{tsk.id}' уже существует, пропускаем")
                continue
            
            tasks_storage[tsk.id] = tsk
            count += 1
            print(f"Создана задача: {tsk}")
            
            if max_tasks and count >= max_tasks:
                break
        
        print(f"\nВсего создано задач: {count}")
        
    except Exception as e:
        print(f"Ошибка при чтении задач: {e}")


@cli.command("start")
def start_task(task_id: str = typer.Argument(..., help="ID задачи")) -> None:
    """Начинает выполнение задачи"""
    task = get_task_or_exit(task_id)
    if not task:
        return
    
    try:
        old_status = task.status
        task.start()
        print(f"Задача '{task_id}' переведена из статуса '{old_status}' в '{task.status}'")
    except Exception as e:
        print(f"Ошибка: {e}")


@cli.command("review")
def review_task(task_id: str = typer.Argument(..., help="ID задачи")) -> None:
    """Отправляет задачу на ревью"""
    task = get_task_or_exit(task_id)
    if not task:
        return
    
    try:
        old_status = task.status
        task.review()
        print(f"Задача '{task_id}' переведена из статуса '{old_status}' в '{task.status}'")
    except Exception as e:
        print(f"Ошибка: {e}")


@cli.command("complete")
def complete_task(task_id: str = typer.Argument(..., help="ID задачи")) -> None:
    """Завершает задачу"""
    task = get_task_or_exit(task_id)
    if not task:
        return
    
    try:
        old_status = task.status
        task.complete()
        print(f"Задача '{task_id}' переведена из статуса '{old_status}' в '{task.status}'")
    except Exception as e:
        print(f"Ошибка: {e}")


@cli.command("archive")
def archive_task(task_id: str = typer.Argument(..., help="ID задачи")) -> None:
    """Архивирует задачу"""
    task = get_task_or_exit(task_id)
    if not task:
        return
    
    try:
        old_status = task.status
        task.archive()
        print(f"Задача '{task_id}' переведена из статуса '{old_status}' в '{task.status}'")
    except Exception as e:
        print(f"Ошибка: {e}")


@cli.command("info")
def task_info(task_id: str = typer.Argument(..., help="ID задачи")) -> None:
    """Показывает подробную информацию о задаче"""
    task = get_task_or_exit(task_id)
    if not task:
        return
    
    display_task_info(task)


@cli.command("list")
def list_all_tasks() -> None:
    """Показывает список всех задач"""
    display_all_tasks()


@cli.command("create")
def create_task_interactive() -> None:
    """Создает новую задачу в интерактивном режиме"""
    print("    Создание новой задачи:")

    while True:
        task_id = input("ID задачи: ").strip()
        if task_id in tasks_storage:
            print("Ошибка: Задача с таким ID уже существует!")
            continue
        if not task_id:
            print("Ошибка: ID не может быть пустым!")
            continue
        break

    while True:
        title = input("Название задачи: ").strip()
        if len(title) < 3:
            print("Ошибка: Название должно содержать минимум 3 символа!")
            continue
        break

    while True:
        author = input("Автор: ").strip()
        if len(author) < 2:
            print("Ошибка: Имя автора должно содержать минимум 2 символа!")
            continue
        break

    while True:
        content = input("Содержание задачи: ").strip()
        if not content:
            print("Ошибка: Содержание не может быть пустым!")
            continue
        break

    print("\nВыберите приоритет:")
    print("  1 - Низкий (LOW)")
    print("  2 - Средний (MEDIUM)")
    print("  3 - Высокий (HIGH)")
    print("  4 - Срочный (URGENT)")
    print("  5 - Критический (CRITICAL)")
    
    while True:
        priority_choice = input("Введите номер приоритета от 1 до 5 (по умолчанию 2): ").strip()
        if not priority_choice:
            priority_value = 2
            break
        try:
            priority_value = int(priority_choice)
            if 1 <= priority_value <= 5:
                break
            else:
                print("Ошибка: Введите число от 1 до 5")
        except ValueError:
            print("Ошибка: Введите число")
    
    try:
        task = Task(
            id=task_id,
            title=title,
            author=author,
            content=content,
            priority=priority_value
        )
        tasks_storage[task_id] = task
        print("Задача успешно создана: ")
        display_task_info(task)
    except Exception as e:
        print(f"Ошибка при создании задачи: {e}")


def main_loop() -> None:
    """Главный цикл программы"""
    print("Добро пожаловать в систему управления задачами!")
    print("Введите 'instruct' для списка команд или 'exit' для выхода.\n")
    
    if len(sys.argv) > 1:
        try:
            cli()
        except SystemExit:
            pass

    while True:
        try:
            command_line = input("Введите команду: ").strip()
            
            if not command_line:
                continue
            
            if command_line.lower() == "exit":
                print("Выход из программы...")
                break

            parts = command_line.split()
            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            temp_cli = Typer(no_args_is_help=True, add_completion=False)
            
            # копируем команды в временный CLI
            temp_cli.command("instruct")(display_instructions)
            temp_cli.command("sources")(list_sources)
            temp_cli.command("read")(read_tasks)
            temp_cli.command("start")(start_task)
            temp_cli.command("review")(review_task)
            temp_cli.command("complete")(complete_task)
            temp_cli.command("archive")(archive_task)
            temp_cli.command("info")(task_info)
            temp_cli.command("list")(list_all_tasks)
            temp_cli.command("create")(create_task_interactive)

            try:
                sys.argv = ["temp_cli"] + [cmd] + args
                temp_cli()
            except SystemExit:
                pass
            except Exception as e:
                print(f"Ошибка: {e}")
                
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except EOFError:
            print("\nВыход...")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")