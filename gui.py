"""
简易图形界面入口
允许选择输入书签HTML文件与输出路径，并一键执行整理流程。
"""
import asyncio
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from utils.logger import setup_logger
from parsers.bookmark_parser import BookmarkParser
from classifiers.ai_classifier import AIClassifier
from exporters.html_exporter import HTMLExporter
from config import config


logger = setup_logger(name="bookmark_gui")


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("书签整理工具")
        self.root.geometry("560x240")

        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar(value=config.output.output_filename)

        # 行1：输入文件
        tk.Label(root, text="书签HTML文件：").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(root, textvariable=self.input_path_var, width=50).grid(row=0, column=1, padx=5, pady=10, sticky="w")
        tk.Button(root, text="选择...", command=self.choose_input).grid(row=0, column=2, padx=10, pady=10)

        # 行2：输出文件
        tk.Label(root, text="输出HTML文件：").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(root, textvariable=self.output_path_var, width=50).grid(row=1, column=1, padx=5, pady=10, sticky="w")
        tk.Button(root, text="浏览...", command=self.choose_output).grid(row=1, column=2, padx=10, pady=10)

        # 行3：动作
        self.run_button = tk.Button(root, text="开始整理", command=self.run)
        self.run_button.grid(row=2, column=1, pady=20)

        # 状态
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(root, textvariable=self.status_var, anchor="w").grid(row=3, column=0, columnspan=3, sticky="we", padx=10)

    def choose_input(self) -> None:
        path = filedialog.askopenfilename(title="选择书签HTML文件", filetypes=[("HTML Files", "*.html;*.htm"), ("All Files", "*.*")])
        if path:
            self.input_path_var.set(path)

    def choose_output(self) -> None:
        path = filedialog.asksaveasfilename(title="选择输出HTML文件", defaultextension=".html", filetypes=[("HTML Files", "*.html")])
        if path:
            self.output_path_var.set(path)

    def run(self) -> None:
        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()

        if not input_path:
            messagebox.showwarning("提示", "请先选择书签HTML文件！")
            return
        if not Path(input_path).exists():
            messagebox.showerror("错误", "选择的书签文件不存在！")
            return
        if not output_path:
            messagebox.showwarning("提示", "请设置输出文件名！")
            return

        self.run_button.config(state=tk.DISABLED)
        self.status_var.set("正在处理，请稍候...")

        # 在后台线程中运行事件循环，避免阻塞UI
        threading.Thread(target=self._run_pipeline, args=(input_path, output_path), daemon=True).start()

    def _run_pipeline(self, input_path: str, output_path: str) -> None:
        try:
            asyncio.run(self._async_pipeline(input_path, output_path))
            self.status_var.set("处理完成！")
            messagebox.showinfo("完成", f"已导出：{output_path}")
        except Exception as e:
            logger.exception("处理失败")
            self.status_var.set("处理失败")
            messagebox.showerror("错误", str(e))
        finally:
            self.run_button.config(state=tk.NORMAL)

    async def _async_pipeline(self, input_path: str, output_path: str) -> None:
        parser = BookmarkParser(input_path, config.network.max_concurrency)
        bookmarks = await parser.parse()
        if not bookmarks:
            raise RuntimeError("未解析到书签")

        classifier = AIClassifier(bookmarks, config.network.max_concurrency)
        await classifier.classify_all()

        exporter = HTMLExporter(classifier.get_result(), filename=output_path, items=classifier.get_items())
        if not exporter.validate_data():
            raise RuntimeError("数据验证失败")
        exporter.export()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()


