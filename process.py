from tkinter import Toplevel
import sys
import subprocess
import queue
import threading

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel
from tinui.theme.tinuilight import TinUILight


class ProcessManager:

    def __init__(self, textbox, filename):
        self.process = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.output_area = textbox
        self.filename = filename

    def _on_input_entered(self, user_input):
        if self.process and self.process.poll() is None:
            # 进程正在运行，发送输入
            self.input_queue.put(user_input + '\n')
        else:
            self.write_output("There is no process running.\n")
    
    def write_output(self, text):
        """在输出区域显示文本"""
        self.output_area.configure(state='normal')
        self.output_area.insert('end', text)
        self.output_area.see('end')
        self.output_area.configure(state='disabled')
    
    def start_process(self):
        """启动子进程"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", self.filename],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,# 将标准错误合并到标准输出
                text=False,
                bufsize=0
            )
            # 启动线程来处理输入输出
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stdout_thread.daemon = True
            self.stdout_thread.start()
            self.stdin_thread = threading.Thread(target=self._write_stdin)
            self.stdin_thread.daemon = True
            self.stdin_thread.start()
            self.write_output(f"[Process started: {self.filename}]\n\n")
        except Exception as e:
            self.write_output(f"Error starting process: {e}\n")
    
    def stop_process(self):
        """停止子进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass            
            self.write_output("[Process stopped]\n")
    
    def check_process(self):
        """检查子进程是否正在运行"""
        if self.process and self.process.poll() is None:
            return True
        else:
            return False

    def _read_stdout(self):
        """从进程的标准输出读取数据"""
        buffer = b""
        while self.process and self.process.poll() is None:
            try:
                buffer += self.process.stdout.read(1024)
                try:
                    data = buffer.decode('utf-8')
                    self.write_output(data)
                    buffer = b""
                except:
                    pass
            except:
                break
        # 进程已结束
        if self.process:
            return_code = self.process.poll()
            self.write_output(f"\n[Process ended, return code: {return_code}]\n")
    
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
            except:
                break


def close_window():
    if process.check_process():
        process.stop_process()
    window.withdraw()

def close_process(event):
    if process.check_process():
        process.stop_process()

def write_input(event):
    process._on_input_entered(entry.get())
    entry.delete(0, 'end')

def run_script(filename):
    global process
    process = ProcessManager(textbox, filename)
    process.start_process()

def init_shell_window():
    global window, textbox, entry
    window = Toplevel()
    window.title("MIDLE Shell")
    window.geometry("700x700")
    window.iconbitmap("logo.ico")
    window.withdraw()
    window.protocol("WM_DELETE_WINDOW", close_window)
    window.bind("<Control-z>", close_process)

    ui = BasicTinUI(window)
    ui.pack(fill="both", expand=True)
    uitheme = TinUILight(ui)

    rpanel = ExpandPanel(ui)
    vpanel = VerticalPanel(ui,spacing=5)
    rpanel.set_child(vpanel)
    
    epanel = ExpandPanel(ui, padding=(0,3,3,0))
    textboxs = uitheme.add_textbox((0,0), font='Consolas 12', scrollbar=True)
    epanel.set_child(textboxs[-1])
    textbox = textboxs[0]
    textbox.config(wrap='none', state='disabled')
    vpanel.add_child(epanel, weight=1)

    hpanel = HorizonPanel(ui, spacing=5, padding=(0,8,0,3))
    entrys = uitheme.add_entry((0,0), width=100, anchor='w')
    entry = entrys[0]
    entry.bind('<Return>', write_input)
    epanel2 = ExpandPanel(ui)
    epanel2.set_child(entrys[-1])
    hpanel.add_child(epanel2, weight=1)
    button = uitheme.add_button2((0,0), text='Input', anchor='w', command=write_input)[-1]
    hpanel.add_child(button)
    vpanel.add_child(hpanel, 40)

    def on_resize(event):
        rpanel.update_layout(0, 0, event.width, event.height)
    ui.bind("<Configure>", on_resize)

def show_shell_window(filename):
    window.title(f"MIDLE Shell - {filename}")
    window.deiconify()
    run_script(filename)
