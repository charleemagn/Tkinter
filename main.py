import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime
import sys
import random
from datetime import timedelta

class ModuleApp(tk.Tk):
    DB_FILE = 'module_app.db'
    SQL_SCRIPT = 'create_SQLite.txt'
    
    def __init__(self):
        super().__init__()
        
        # Настройки приложения
        self.title("Программный модуль для обработки данных испытаний")
        self.geometry("1200x800")
        self.dark_mode = False
        self.fullscreen_mode = False
        
        # Инициализация БД
        self.db_conn = self.initialize_database()
        
        # Состояние испытаний
        self.current_test_start = None
        self.test_in_progress = False
        
        # Стили интерфейса
        self.style = ttk.Style()
        self.configure_styles()
        
        # Создание интерфейса
        self.create_main_interface()
        self.create_settings_interface()
        self.create_testing_interface()
        
        # Применение настроек
        self.apply_theme()
        self.update_test_stats()
        self.load_test_history()
        
        # Показываем главное меню
        self.show_main_interface()

    def initialize_database(self):
        """Инициализация базы данных с защитой от блокировки файла"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Пытаемся подключиться к существующей БД
                if os.path.exists(self.DB_FILE):
                    conn = sqlite3.connect(self.DB_FILE)
                    cursor = conn.cursor()
                    
                    # Проверяем наличие таблиц
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'")
                    if not cursor.fetchone():
                        conn.close()
                        os.remove(self.DB_FILE)
                        return self.create_new_database()
                    
                    return conn
                else:
                    return self.create_new_database()
                    
            except sqlite3.Error as e:
                attempt += 1
                if attempt == max_attempts:
                    messagebox.showerror("Ошибка БД", 
                        f"Не удалось подключиться к базе данных после {max_attempts} попыток.\n"
                        f"Ошибка: {str(e)}\n\n"
                        "Попробуйте закрыть другие программы, которые могут использовать этот файл.")
                    sys.exit(1)
                
                time.sleep(1)  # Ждем перед повторной попыткой

    def create_new_database(self):
        """Создание новой базы данных"""
        try:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            
            # Создаем таблицы
            cursor.executescript("""
            CREATE TABLE app_settings (
                dark_mode INTEGER,
                fullscreen_mode INTEGER
            );
            
            CREATE TABLE test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_time REAL,
                is_completed INTEGER,
                grade TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            INSERT INTO app_settings (dark_mode, fullscreen_mode) VALUES (0, 0);
            """)
            
            conn.commit()
            return conn
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            messagebox.showerror("Ошибка БД", f"Не удалось создать базу данных: {str(e)}")
            sys.exit(1)

    def configure_styles(self):
        """Настройка стилей интерфейса"""
        self.style = ttk.Style()
        
        # Общие стили
        self.style.configure('.', font=('Arial', 10))
        self.style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        self.style.configure('Status.TLabel', font=('Arial', 12))
        
        # Стиль кнопки выхода
        exit_bg = '#ff8000' if not self.dark_mode else '#ff5555'
        self.style.configure('Exit.TButton', 
                           font=('Arial', 10, 'bold'),
                           padding=6,
                           foreground='white',
                           background=exit_bg)
        self.style.map('Exit.TButton',
                      background=[('active', '#ff6666'), 
                                ('pressed', '#cc0000'), 
                                ('!disabled', exit_bg)])

    def create_main_interface(self):
        """Создание главного интерфейса"""
        self.main_frame = ttk.Frame(self)

        # Иконка приложения
        try:
            photo = tk.PhotoImage(file='./icon.png')
            self.iconphoto(False, photo)
        except tk.TclError:
            print("Файл иконки не найден")
        
        # Левая панель с кнопками
        left_frame = ttk.Frame(self.main_frame, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(left_frame, text="Главное меню", style='Title.TLabel').pack(pady=20)
        
        # Кнопки навигации
        ttk.Button(left_frame, text="Режим испытаний", 
                  command=self.show_testing_interface).pack(fill=tk.X, pady=5)
        ttk.Button(left_frame, text="Настройки", 
                  command=self.show_settings_interface).pack(fill=tk.X, pady=5)
        ttk.Button(left_frame, text="Выйти", 
                  style='Exit.TButton', command=self.exit_app).pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        # Правая панель - приветствие и статистика
        right_frame = ttk.Frame(self.main_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        ttk.Label(right_frame, text="Добро пожаловать в систему испытаний", 
                 style='Title.TLabel').pack(pady=50)
        
        # Краткая статистика
        self.quick_stats_frame = ttk.LabelFrame(right_frame, text="Краткая статистика")
        self.quick_stats_frame.pack(fill=tk.X, pady=10)
        
        self.quick_stats_label = ttk.Label(
            self.quick_stats_frame,
            text="Загружается...",
            justify=tk.LEFT
        )
        self.quick_stats_label.pack(pady=5, padx=5, anchor=tk.W)

    def create_settings_interface(self):
        """Создание интерфейса настроек"""
        self.settings_frame = ttk.Frame(self)
        
        ttk.Label(self.settings_frame, text="Настройки приложения", 
                 style='Title.TLabel').pack(pady=20)
        
        # Переключатель темы
        self.dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        ttk.Checkbutton(
            self.settings_frame,
            text="Темная тема",
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode
        ).pack(pady=10, padx=20, anchor=tk.W)
        
        # Переключатель полноэкранного режима
        self.fullscreen_var = tk.BooleanVar(value=self.fullscreen_mode)
        ttk.Checkbutton(
            self.settings_frame,
            text="Полноэкранный режим",
            variable=self.fullscreen_var,
            command=self.toggle_fullscreen
        ).pack(pady=10, padx=20, anchor=tk.W)
        
        # Кнопка возврата
        ttk.Button(
            self.settings_frame,
            text="Вернуться в главное меню",
            command=self.show_main_interface
        ).pack(pady=30)

    def create_testing_interface(self):
        """Создание интерфейса тестирования"""
        self.testing_frame = ttk.Frame(self)
        
        # Панель управления испытанием
        control_frame = ttk.Frame(self.testing_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Начать испытание", 
                  command=self.start_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Завершить испытание", 
                  command=self.finish_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить выбранное", 
                  command=self.delete_selected_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Добавить тестовые данные", 
                  command=self.add_test_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Очистить все данные", 
                  command=self.clear_all_data).pack(side=tk.LEFT, padx=5)
        
        # Статус испытания
        self.test_status = ttk.Label(
            self.testing_frame,
            text="Готов к проведению испытания",
            style='Status.TLabel'
        )
        self.test_status.pack(pady=10)
        
        # Статистика
        stats_frame = ttk.LabelFrame(self.testing_frame, text="Статистика испытаний")
        stats_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Используем StringVar для автоматического обновления
        self.stats_vars = {
            'total': tk.StringVar(value="Всего испытаний: 0"),
            'excellent': tk.StringVar(value="Отлично: 0"),
            'good': tk.StringVar(value="Хорошо: 0"),
            'satisfactory': tk.StringVar(value="Удовлетворительно: 0"),
            'failed': tk.StringVar(value="Неудачно: 0")
        }
        
        self.stats_labels = {
            'total': ttk.Label(stats_frame, textvariable=self.stats_vars['total']),
            'excellent': ttk.Label(stats_frame, textvariable=self.stats_vars['excellent']),
            'good': ttk.Label(stats_frame, textvariable=self.stats_vars['good']),
            'satisfactory': ttk.Label(stats_frame, textvariable=self.stats_vars['satisfactory']),
            'failed': ttk.Label(stats_frame, textvariable=self.stats_vars['failed'])
        }
        
        for label in self.stats_labels.values():
            label.pack(anchor=tk.W)
        
        # История испытаний
        history_frame = ttk.LabelFrame(self.testing_frame, text="История испытаний")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("id", "time", "completed", "grade", "date")
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Настройка столбцов
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("time", text="Время (сек)")
        self.history_tree.heading("completed", text="Завершено")
        self.history_tree.heading("grade", text="Оценка")
        self.history_tree.heading("date", text="Дата")
        
        self.history_tree.column("id", width=50, anchor=tk.CENTER)
        self.history_tree.column("time", width=100, anchor=tk.CENTER)
        self.history_tree.column("completed", width=100, anchor=tk.CENTER)
        self.history_tree.column("grade", width=120, anchor=tk.CENTER)
        self.history_tree.column("date", width=150, anchor=tk.CENTER)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        self.history_tree.bind("<Double-1>", lambda e: self.delete_selected_test())
        
        ttk.Button(
            self.testing_frame,
            text="Вернуться в главное меню",
            command=self.show_main_interface
        ).pack(pady=10)

    # Методы управления интерфейсом
    def show_main_interface(self):
        """Показать главное меню"""
        self.settings_frame.pack_forget()
        self.testing_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.update_quick_stats()

    def show_settings_interface(self):
        """Показать настройки"""
        self.main_frame.pack_forget()
        self.testing_frame.pack_forget()
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        self.dark_mode_var.set(self.dark_mode)
        self.fullscreen_var.set(self.fullscreen_mode)

    def show_testing_interface(self):
        """Показать интерфейс испытаний"""
        self.main_frame.pack_forget()
        self.settings_frame.pack_forget()
        self.testing_frame.pack(fill=tk.BOTH, expand=True)
        self.update_test_stats()
        self.load_test_history()

    # Методы работы с испытаниями
    def start_test(self):
        """Начать новое испытание"""
        if self.test_in_progress:
            messagebox.showwarning("Ошибка", "Испытание уже начато!")
            return
        
        self.current_test_start = time.time()
        self.test_in_progress = True
        self.test_status.config(
            text=f"Испытание начато в {datetime.now().strftime('%H:%M:%S')}",
            foreground='blue'
        )

    def finish_test(self):
        """Завершить текущее испытание"""
        if not self.test_in_progress:
            messagebox.showwarning("Ошибка", "Испытание не начато!")
            return
        
        test_time = round(time.time() - self.current_test_start, 2)
        grade = self.calculate_grade(test_time)
        is_completed = test_time <= 60
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
            INSERT INTO test_results (test_time, is_completed, grade)
            VALUES (?, ?, ?)
            """, (test_time, is_completed, grade))
            self.db_conn.commit()
            
            self.test_in_progress = False
            self.test_status.config(
                text=f"Последнее испытание: {test_time} сек. - {grade}",
                foreground='green' if is_completed else 'red'
            )
            
            self.update_test_stats()
            self.load_test_history()
            self.update_quick_stats()
            
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось сохранить результаты: {str(e)}")
            self.db_conn.rollback()

    def calculate_grade(self, time_sec):
        """Определить оценку по времени выполнения"""
        if time_sec < 15: return "Отлично"
        if time_sec < 30: return "Хорошо"
        if time_sec < 60: return "Удовлетворительно"
        return "Неудачно"

    def delete_selected_test(self):
        """Удалить выбранное испытание"""
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите испытание для удаления")
            return
        
        item_id = self.history_tree.item(selected_item)['values'][0]
        
        if not messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить это испытание?"):
            return
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM test_results WHERE id = ?", (item_id,))
            self.db_conn.commit()
            
            self.history_tree.delete(selected_item)
            self.update_test_stats()
            self.update_quick_stats()
            messagebox.showinfo("Успех", "Испытание успешно удалено")
            
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось удалить испытание: {str(e)}")
            self.db_conn.rollback()

    def clear_all_data(self):
        """Очистить все данные испытаний"""
        if not messagebox.askyesno(
            "Подтверждение", 
            "Вы действительно хотите удалить ВСЕ данные испытаний?\nЭто действие нельзя отменить!"
        ):
            return
    
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM test_results")
            self.db_conn.commit()
            
            self.update_test_stats()
            self.load_test_history()
            self.update_quick_stats()
            messagebox.showinfo("Успех", "Все данные успешно удалены")
        
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось очистить данные: {str(e)}")
            self.db_conn.rollback()

    def add_test_data(self):
        """Добавить тестовые данные"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM test_results")
            self.db_conn.commit()
            
            # Генерация тестовых данных
            grades = ["Отлично", "Хорошо", "Удовлетворительно", "Неудачно"]
            time_ranges = {
                "Отлично": (5, 15), 
                "Хорошо": (15, 30), 
                "Удовлетворительно": (30, 60), 
                "Неудачно": (60, 120)
            }
            
            for i in range(100):
                grade = random.choice(grades)
                min_time, max_time = time_ranges[grade]
                test_time = round(random.uniform(min_time, max_time), 2)
                is_completed = test_time <= 60
                timestamp = datetime.now() - timedelta(
                    days=random.randint(0, 365),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                cursor.execute("""
                INSERT INTO test_results (test_time, is_completed, grade, timestamp)
                VALUES (?, ?, ?, ?)
                """, (test_time, is_completed, grade, timestamp.strftime('%Y-%m-%d %H:%M:%S')))
            
            self.db_conn.commit()
            messagebox.showinfo("Успех", "Тестовые данные успешно добавлены")
            self.update_test_stats()
            self.load_test_history()
            self.update_quick_stats()
            
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось добавить тестовые данные: {str(e)}")
            self.db_conn.rollback()

    def update_test_stats(self):
        """Обновление статистики испытаний"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN grade = 'Отлично' THEN 1 ELSE 0 END) as excellent,
                SUM(CASE WHEN grade = 'Хорошо' THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN grade = 'Удовлетворительно' THEN 1 ELSE 0 END) as satisfactory,
                SUM(CASE WHEN grade = 'Неудачно' THEN 1 ELSE 0 END) as failed
            FROM test_results
            """)
            
            result = cursor.fetchone()
            
            if result:
                total = result[0] if result[0] is not None else 0
                excellent = result[1] if result[1] is not None else 0
                good = result[2] if result[2] is not None else 0
                satisfactory = result[3] if result[3] is not None else 0
                failed = result[4] if result[4] is not None else 0
                
                # Обновляем StringVar
                self.stats_vars['total'].set(f"Всего испытаний: {total}")
                self.stats_vars['excellent'].set(f"Отлично: {excellent}")
                self.stats_vars['good'].set(f"Хорошо: {good}")
                self.stats_vars['satisfactory'].set(f"Удовлетворительно: {satisfactory}")
                self.stats_vars['failed'].set(f"Неудачно: {failed}")
                
                # Принудительное обновление интерфейса
                self.update_idletasks()
                
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось обновить статистику: {str(e)}")

    def update_quick_stats(self):
        """Обновление краткой статистики на главном экране"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN grade = 'Отлично' THEN 1 ELSE 0 END) as excellent,
                AVG(test_time) as avg_time
            FROM test_results
            """)
            
            result = cursor.fetchone()
            
            if result:
                total = result[0] if result[0] is not None else 0
                excellent = result[1] if result[1] is not None else 0
                avg_time = result[2] if result[2] is not None else 0
                
                text = f"""Всего испытаний: {total}
На отлично: {excellent}
Среднее время: {round(avg_time, 2) if avg_time else 0} сек."""
                
                self.quick_stats_label.config(text=text)
                
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось обновить краткую статистику: {str(e)}")

    def load_test_history(self):
        """Загрузка истории испытаний в таблицу"""
        try:
            # Очищаем текущие данные
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            cursor = self.db_conn.cursor()
            cursor.execute("""
            SELECT id, test_time, 
                   CASE WHEN is_completed THEN 'Да' ELSE 'Нет' END,
                   grade, 
                   strftime('%d.%m.%Y %H:%M', timestamp) 
            FROM test_results 
            ORDER BY timestamp DESC 
            """)
            
            for row in cursor.fetchall():
                self.history_tree.insert("", tk.END, values=row)
                
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось загрузить историю испытаний: {str(e)}")

    def export_data(self):
        """Экспорт данных в SQL-скрипт"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [table[0] for table in cursor.fetchall()]
            
            with open(self.SQL_SCRIPT, 'w', encoding='utf-8') as f:
                f.write("-- SQL-SCRIPT --\n")
                f.write(f"-- Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for table in tables:
                    cursor.execute(f"SELECT sql from sqlite_master WHERE type='table' AND name=?", (table,))
                    create_table = cursor.fetchone()[0]
                    f.write(f"{create_table};\n\n")

                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    if rows:
                        columns = [description[0] for description in cursor.description]
                        for row in rows:
                            values = ",".join([f"'{str(v)}'" if not isinstance(v, (int,float)) else str(v) for v in row])
                            f.write(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({values});\n")
                        f.write("\n")
            messagebox.showinfo("Экспорт", f"База данных успешно экспортирована в {self.SQL_SCRIPT}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {str(e)}")

    # Методы управления настройками
    def toggle_dark_mode(self):
        """Переключение темной темы"""
        self.dark_mode = self.dark_mode_var.get()
        self.apply_theme()
        self.save_settings()

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        self.fullscreen_mode = self.fullscreen_var.get()
        self.attributes('-fullscreen', self.fullscreen_mode)
        if not self.fullscreen_mode:
            self.geometry("1200x800")
        self.save_settings()

    def apply_theme(self):
        """Применение выбранной темы"""
        bg = '#2d2d2d' if self.dark_mode else '#f0f0f0'
        fg = '#ffffff' if self.dark_mode else '#000000'
        
        self.tk_setPalette(
            background=bg,
            foreground=fg,
            activeBackground=bg,
            activeForeground=fg
        )
        
        self.style.theme_use('alt' if self.dark_mode else 'clam')
        self.style.configure('.', background=bg, foreground=fg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('TButton', background=bg, foreground=fg)
        self.style.configure('Treeview', 
                           background=bg, 
                           foreground=fg, 
                           fieldbackground=bg,
                           rowheight=25)
        
        # Обновляем стиль кнопки выхода
        exit_bg = '#ff5555' if self.dark_mode else '#ff8000'
        self.style.configure('Exit.TButton', background=exit_bg)
        self.style.map('Exit.TButton',
                      background=[('active', '#ff6666'), 
                                ('pressed', '#cc0000'), 
                                ('!disabled', exit_bg)])

    def save_settings(self):
        """Сохранение настроек в БД"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
            UPDATE app_settings 
            SET dark_mode = ?, fullscreen_mode = ?
            """, (int(self.dark_mode), int(self.fullscreen_mode)))
            self.db_conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Не удалось сохранить настройки: {str(e)}")

    def exit_app(self):
        """Завершение работы приложения"""
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите выйти?"):
            try:
                self.export_data()
                if self.db_conn:
                    self.db_conn.close()
                self.destroy()
                sys.exit()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось завершить работу: {str(e)}")
                sys.exit(1)

if __name__ == "__main__":
    try:
        app = ModuleApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Приложение завершено с ошибкой: {str(e)}")
        sys.exit(1)