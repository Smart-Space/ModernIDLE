from tkinter import Toplevel, Text
import sys
if sys.platform == "win32":
    import ctypes
    factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
else:
    factor = 1
import subprocess
import codecs
import queue
import threading
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

from tinui import BasicTinUI, ExpandPanel, VerticalPanel
from tinui.theme.tinuilight import TinUILight


class ProcessManager:

    def __init__(self, textbox, filename, debug):
        self.process = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.output_area = textbox
        self.filename = filename
        self.cwd = os.path.dirname(filename)
        self.debug = debug

    def _on_input_entered(self, user_input):
        if self.process and self.process.poll() is None:
            # 进程正在运行，发送输入
            self.input_queue.put(user_input + '\n')
        else:
            self.write_output("There is no process running.\n", 'ERROR')

    def write_output(self, text, TAG=None):
        """在输出区域显示文本"""
        if TAG:
            self.output_area.insert('end', text, TAG)
        else:
            self.output_area.insert('end', text)
        self.output_area.see('end')
        self.output_area.mark_set('input_start', 'insert')
        self.output_area.mark_set('insert', 'input_start')
        self.output_area.see('insert')

    def start_process(self):
        """启动子进程"""
        if not self.debug:
            cmds = [sys.executable, "-u", self.filename]
        else:
            cmds = [sys.executable, "-u", "-m", "pdb", self.filename]
        try:
            self.process = subprocess.Popen(
                cmds,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0,
                cwd=self.cwd
            )
            # 启动线程来处理输入输出
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stdout_thread.daemon = True
            self.stdout_thread.start()
            self.stderr_thread = threading.Thread(target=self._read_stderr)
            self.stderr_thread.daemon = True
            self.stderr_thread.start()
            self.stdin_thread = threading.Thread(target=self._write_stdin)
            self.stdin_thread.daemon = True
            self.stdin_thread.start()
            self.write_output(f"[Process started: {self.filename}]\n", 'INFO')
        except Exception as e:
            self.write_output(f"Error starting process: {e}\n", "ERROR")

    def stop_process(self):
        """停止子进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.write_output("[Process stopped]\n", "ERROR")

    def check_process(self):
        """检查子进程是否正在运行"""
        if self.process and self.process.poll() is None:
            return True
        else:
            return False

    def _read_stream(self, stream, flag=None):
        """从进程的输出流读取数据"""
        decoder = codecs.getincrementaldecoder('utf-8')()
        while self.process:
            try:
                chunk = stream.read(2048)
            except Exception:
                break
            if not chunk:
                break
            try:
                data = decoder.decode(chunk)
            except Exception:
                data = ""
            if data:
                self.write_output(data, flag)
        try:
            tail = decoder.decode(b"", final=True)
        except Exception:
            tail = ""
        if tail:
            self.write_output(tail, flag)

    def _read_stdout(self):
        """从进程的标准输出读取数据"""
        if not self.process:
            return
        self._read_stream(self.process.stdout, False)
        if self.process:
            try:
                return_code = self.process.wait()
            except Exception:
                return_code = self.process.poll()
            self.write_output(f"[Process ended, return code: {return_code}]\n\n", "SUCCESS")

    def _read_stderr(self):
        """从进程的标准错误读取数据"""
        if not self.process:
            return
        self._read_stream(self.process.stderr, "ERROR")

    def _write_stdin(self):
        """向进程的标准输入写入数据"""
        while self.process and self.process.poll() is None:
            try:
                # 从队列获取输入
                input_data = self.input_queue.get(timeout=0.1)
                if input_data:
                    self.process.stdin.write(input_data.encode('utf-8'))
                    self.process.stdin.flush()
            except queue.Empty:
                continue
            except Exception:
                break


process: ProcessManager = None


window_close = False
def close_window():
    global window_close
    window_close = True
    if process.check_process():
        process.stop_process()
    textbox.delete('1.0', 'end')
    window.withdraw()

def close_process(event):
    if process.check_process():
        process.stop_process()

def run_script(filename, debug):
    global process
    if process and process.check_process():
        process.stop_process()
    process = ProcessManager(textbox, filename, debug)
    process.start_process()


def _proxy(*args):
    # 接管insert/delete操作
    args_list = list(args)
    if args[0] == 'insert':
        if textbox.compare('insert', '<', 'input_start'):
            textbox.mark_set('insert', 'end')
            return
    elif args[0] == 'delete' and not window_close:
        if textbox.compare(args[1], '<', 'input_start'):
            if len(args_list) == 2:
                # 尝试删除单个字符
                return
            else:
                args_list[1] = 'input_start'
    result = textbox.tk.call((text_original_widget,)+tuple(args_list))
    return result

def _check_cursor_position(event=None):
    # 确保光标不越界
    if textbox.compare('insert', '<', 'input_start'):
        textbox.mark_set('insert', 'input_start')
    return None

def _run_command(event=None):
    command = textbox.get('input_start', 'end-1c')
    if not command.strip():
        return "break"
    process._on_input_entered(command)
    textbox.mark_set('input_start', 'insert')
    textbox.mark_set('insert', 'input_start')
    textbox.see('insert')

textbox:Text
text_original_widget:str
def init_shell_window():
    global window, textbox, entry, text_original_widget
    window = Toplevel()
    window.title("MIDLE Shell")
    width = int(700*factor)
    height = int(700*factor)
    window.geometry(f"{width}x{height}")
    window.iconbitmap("logo.ico")
    window.withdraw()
    window.protocol("WM_DELETE_WINDOW", close_window)
    window.bind("<Control-z>", close_process)

    ui = BasicTinUI(window)
    ui.set_scale(factor)
    ui.pack(fill="both", expand=True)
    uitheme = TinUILight(ui)

    rpanel = ExpandPanel(ui)
    vpanel = VerticalPanel(ui,spacing=5)
    rpanel.set_child(vpanel)

    epanel = ExpandPanel(ui, padding=(0,3,3,0))
    textboxs = uitheme.add_textbox((0,0), font='Consolas 12', scrollbar=True)
    epanel.set_child(textboxs[-1])
    textbox = textboxs[0]
    textbox.mark_set('input_start', 'insert')
    textbox.mark_gravity('input_start', 'left')
    # 拦截insert/delete操作
    text_original_widget = f"{textbox._w}_original"
    textbox.tk.call("rename", textbox._w, text_original_widget) # 保留原命令
    textbox.tk.createcommand(textbox._w, _proxy) # 重命名功能
    textbox.bind('<Return>', _run_command)
    textbox.bind('<Key>', _check_cursor_position)
    
    textbox.config(wrap='none')
    textbox.tag_config('ERROR', foreground='red')
    textbox.tag_config('INFO', foreground='#4A90E2')
    textbox.tag_config('SUCCESS', foreground='#2ECC71')
    textbox.tag_config('WARNING', foreground='#F39C12')
    vpanel.add_child(epanel, weight=1)

    def on_resize(event):
        rpanel.update_layout(0, 0, event.width, event.height)
    ui.bind("<Configure>", on_resize)

def show_shell_window(filename, debug=False):
    global window_close
    window.title(f"MIDLE Shell - {filename}")
    window.deiconify()
    textbox.focus_set()
    window_close = False
    run_script(filename, debug)
