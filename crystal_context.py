import json
import os
import subprocess
import sys

import sublime
import sublime_plugin

OUTPUT_PANEL_SETTINGS = {
    "is_widget": True,
    "line_numbers": False,
}


class CrystalShowContextCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        caret = self.view.sel()[0].a
        syntax = self.view.scope_name(caret)
        has_filename = bool(self.view.file_name())
        return has_filename and "source.crystal" in syntax

    def description(self):
        return "Show types of variables in the scope currently under cursor"

    def run(self, edit):
        window = self.view.window()
        filename = self.view.file_name()
        cursor_pos = self.view.sel()[0].b
        row, col = self.view.rowcol(cursor_pos)  # zero-based
        filepos = "{}:{}:{}".format(filename, row + 1, col + 1)

        settings = sublime.load_settings("Crystal.sublime-settings")
        command = [
            settings.get("crystal_cmd"),
            "tool",
            "context",
            "-f", "json",
            "-c", filepos,
            filename,
        ]

        # for Windows Subsystem for Linux
        if os.name == "nt":
            command.insert(0, "wsl")

        popen_args = {
            "args": command,
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }
        # Prevent flashing terminal windows
        if sys.platform.startswith("win"):
            popen_args["startupinfo"] = subprocess.STARTUPINFO()
            popen_args["startupinfo"].dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen(**popen_args)
        stdout, _stderr = proc.communicate()
        stdout = stdout.decode("utf-8")
        results = json.loads(stdout)

        output = ""
        for i, ctx in enumerate(results["contexts"], 1):
            output += "======== Context #{} ========\n".format(i)
            for varname, vartype in ctx.items():
                output += "  {} : {}\n".format(varname, vartype)
            output += "\n"

        ctx_panel = window.create_output_panel("crystal_context")
        ctx_panel.set_read_only(False)
        settings = ctx_panel.settings()
        for key, value in OUTPUT_PANEL_SETTINGS.items():
            settings.set(key, value)
        ctx_panel.run_command("append", {"characters": output})
        ctx_panel.set_read_only(True)

        window.run_command("show_panel", {"panel": "output.crystal_context"})
