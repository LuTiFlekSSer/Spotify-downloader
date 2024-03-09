__all__ = [
    'CustomTable'
]

import customtkinter
import copy


class CustomTable(customtkinter.CTkFrame):
    def __init__(self, master: any,
                 row: int = None,
                 column: int = None,
                 padx: int = 1,
                 pady: int = 0,
                 width: int = 140,
                 height: int = 28,
                 values: list = None,
                 colors: list = [None, None],
                 orientation: str = "horizontal",
                 color_phase: str = "horizontal",
                 border_width: int = 0,
                 text_color: str or tuple = None,
                 border_color: str or tuple = None,
                 font: tuple = None,
                 header_color: str or tuple = None,
                 corner_radius: int = 25,
                 command=None,
                 anchor: str = "c",
                 hover_color: str or tuple = None,
                 hover: bool = False,
                 justify: str = "center",
                 wraplength: int = 1000,
                 max_rows=10,
                 max_columns=3,
                 **kwargs):
        super().__init__(master, fg_color="transparent")

        if values is None:
            values = [[None, None], [None, None]]

        self.master = master  # parent widget
        self.rows = row if row else len(values)  # number of default rows
        self.columns = column if column else len(values[0])  # number of default columns
        self.width = width
        self.height = height
        self.padx = padx  # internal padding between the rows/columns
        self.pady = pady
        self.command = command
        self.values = values  # the default values of the table
        self.colors = colors  # colors of the table if required
        self.header_color = header_color  # specify the topmost row color
        self.phase = color_phase
        self.corner = corner_radius
        self.justify = justify
        self.binded_objects = []

        if hover_color is not None and hover is False:
            hover = True

        self.anchor = anchor
        self.wraplength = wraplength
        self.hover = hover
        self.border_width = border_width
        self.hover_color = customtkinter.ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None else hover_color
        self.orient = orientation
        self.border_color = customtkinter.ThemeManager.theme["CTkButton"]["border_color"] if border_color is None else border_color
        self.inside_frame = customtkinter.CTkFrame(self, border_width=0, fg_color="transparent")

        super().configure(border_color=self.border_color, border_width=self.border_width, corner_radius=self.corner)
        self.inside_frame.pack(expand=True, fill="both", padx=self.border_width, pady=self.border_width)

        self.text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else text_color
        self.font = font
        self.data = {}
        self.fg_color = customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"] if not self.colors[0] else self.colors[0]
        self.fg_color2 = customtkinter.ThemeManager.theme["CTkFrame"]["top_fg_color"] if not self.colors[1] else self.colors[1]

        if self.colors[0] is None and self.colors[1] is None:
            if self.fg_color == self.master.cget("fg_color"):
                self.fg_color = customtkinter.ThemeManager.theme["CTk"]["fg_color"]
            if self.fg_color2 == self.master.cget("fg_color"):
                self.fg_color2 = customtkinter.ThemeManager.theme["CTk"]["fg_color"]
        self.frame = {}

        self._max_rows = max_rows
        self._max_columns = max_columns

        self._create_rows()

        self.corner_buttons = {}
        self.draw_table(**kwargs)

    def _create_rows(self):
        for i in range(self._max_rows):
            for j in range(self._max_columns):
                self.frame[i, j] = customtkinter.CTkButton(self.inside_frame)

    def insert(self, row, column, value, **kwargs):
        if kwargs:
            self.data[row, column]["args"].update(kwargs)

        self.frame[row, column].configure(require_redraw=True, text=value, **kwargs)
        if (row, column) in self.corner_buttons.keys():
            self.dynamic_hover(self.corner_buttons[row, column], row, column)

        self.update_data()

    def draw_table(self, **kwargs):
        for i in range(self._max_rows):
            for j in range(self._max_columns):
                self.frame[i, j].grid_forget()

        for i in range(self.rows):
            for j in range(self.columns):
                self.inside_frame.grid_rowconfigure(i, weight=1)
                self.inside_frame.grid_columnconfigure(j, weight=1)
                if self.phase == "horizontal":
                    if i % 2 == 0:
                        fg = self.fg_color
                    else:
                        fg = self.fg_color2
                else:
                    if j % 2 == 0:
                        fg = self.fg_color
                    else:
                        fg = self.fg_color2

                if self.header_color:
                    if self.orient == "horizontal":
                        if i == 0:
                            fg = self.header_color
                    else:
                        if j == 0:
                            fg = self.header_color

                corner_radius = self.corner
                if (self.border_width >= 5) and (self.corner >= 5):
                    tr = self.border_color
                else:
                    tr = ""
                if i == 0 and j == 0:
                    corners = [tr, fg, fg, fg]
                    hover_modify = self.hover

                elif i == self.rows - 1 and j == self.columns - 1:
                    corners = [fg, fg, tr, fg]
                    hover_modify = self.hover

                elif i == self.rows - 1 and j == 0:
                    corners = [fg, fg, fg, tr]
                    hover_modify = self.hover

                elif i == 0 and j == self.columns - 1:
                    corners = [fg, tr, fg, fg]
                    hover_modify = self.hover

                else:
                    corners = [fg, fg, fg, fg]
                    corner_radius = 0
                    hover_modify = False

                if i == 0:
                    pady = (0, self.pady)
                else:
                    pady = self.pady

                if j == 0:
                    padx = (0, self.padx)
                else:
                    padx = self.padx

                if i == self.rows - 1:
                    pady = (self.pady, 0)

                if j == self.columns - 1:
                    padx = (self.padx, 0)

                if self.values:
                    try:
                        if self.orient == "horizontal":
                            value = self.values[i][j]
                        else:
                            value = self.values[j][i]
                    except IndexError:
                        value = " "
                else:
                    value = " "

                if value == "":
                    value = " "

                if (i, j) in self.data.keys():
                    if self.data[i, j]["args"]:
                        args = self.data[i, j]["args"]
                    else:
                        args = copy.deepcopy(kwargs)
                else:
                    args = copy.deepcopy(kwargs)

                self.data[i, j] = {"row": i, "column": j, "value": value, "args": args}

                args = self.data[i, j]["args"]

                if "text_color" not in args:
                    args["text_color"] = self.text_color
                if "height" not in args:
                    args["height"] = self.height
                if "width" not in args:
                    args["width"] = self.width
                if "fg_color" not in args:
                    args["fg_color"] = fg
                if args["fg_color"] != fg:
                    args["fg_color"] = fg
                if "corner_radius" in args:
                    del args["corner_radius"]
                if "border_color" in args:
                    del args["border_color"]
                if "border_width" in args:
                    del args["border_width"]
                if "color_phase" in args:
                    del args["color_phase"]
                if "orientation" in args:
                    del args["orientation"]

                if "anchor" not in args:
                    args["anchor"] = self.anchor
                if "hover_color" not in args:
                    args["hover_color"] = self.hover_color
                if "hover" not in args:
                    args["hover"] = self.hover
                if "justify" in args:
                    anchor = args["justify"]
                    if anchor == "center":
                        anchor = "c"
                    elif anchor == "left":
                        anchor = "w"
                    elif anchor == "right":
                        anchor = "e"
                    args.update({"anchor": anchor})
                    del args["justify"]
                if value is None:
                    value = " "

                self.frame[i, j].configure(self.inside_frame, background_corner_colors=corners,
                                           # font=self.font,
                                           corner_radius=corner_radius,
                                           text=value,
                                           border_width=0,
                                           command=(lambda e=self.data[i, j]: self.command(e)) if self.command else None, **args)

                self.frame[i, j].grid(column=j, row=i, padx=padx, pady=pady, sticky="nsew")
                if self.frame[i, j]._text_label is not None:
                    self.frame[i, j]._text_label.config(wraplength=self.wraplength)

                if hover_modify:
                    self.dynamic_hover(self.frame[i, j], i, j)

                self.rowconfigure(i, weight=1)
                self.columnconfigure(j, weight=1)
        for x in self.frame:
            for y in self.binded_objects:
                self.frame[x].bind(*y)

    def add_row(self, values, index=None, **kwargs):
        if index is None:
            index = len(self.values)

        try:
            self.values.insert(index, values)
            self.rows += 1
        except IndexError:
            pass

        self.draw_table(**kwargs)
        self.update_data()

    def delete_row(self, index=None):
        if len(self.values) == 1:
            return

        if index is None or index >= len(self.values):
            index = len(self.values) - 1

        self.values.pop(index)
        self.rows -= 1
        self.draw_table()
        self.update_data()

    def delete_rows(self, indices=None):
        if indices is None:
            indices = []

        if len(indices) == 0:
            return

        self.values = [v for i, v in enumerate(self.values) if i not in indices]

        for i in indices:
            for j in range(self.columns):
                self.data[i, j]["args"] = ""

        self.rows -= len(set(indices))

        self.draw_table()
        self.update_data()

    def update_data(self):
        for i in self.data:
            self.data[i]["value"] = self.frame[i].cget("text")

        self.values = []
        for i in range(self.rows):
            row_data = []
            for j in range(self.columns):
                row_data.append(self.data[i, j]["value"])
            self.values.append(row_data)

    def dynamic_hover(self, frame, i, j):
        self.corner_buttons[i, j] = frame
        fg = self.data[i, j]["args"]["fg_color"]
        hv = self.data[i, j]["args"]["hover_color"]
        if (self.border_width >= 5) and (self.corner >= 5):
            tr = self.border_color
        else:
            tr = ""
        if i == 0 and j == 0:
            corners = [tr, fg, fg, fg]
            hover_corners = [tr, hv, hv, hv]
        elif i == self.rows - 1 and j == self.columns - 1:
            corners = [fg, fg, tr, fg]
            hover_corners = [hv, hv, tr, hv]
        elif i == self.rows - 1 and j == 0:
            corners = [fg, fg, fg, tr]
            hover_corners = [hv, hv, hv, tr]
        elif i == 0 and j == self.columns - 1:
            corners = [fg, tr, fg, fg]
            hover_corners = [hv, tr, hv, hv]
        else:
            return

        frame.configure(background_corner_colors=corners, fg_color=fg)
        frame.bind("<Enter>", lambda e, x=i, y=j, color=hover_corners, fg=hv:
        self.frame[x, y].configure(background_corner_colors=color, fg_color=fg))
        frame.bind("<Leave>", lambda e, x=i, y=j, color=corners, fgg=fg:
        self.frame[x, y].configure(background_corner_colors=color, fg_color=fgg))

    def get(self, row=None, column=None):
        """ get the required cell """
        if row is not None and column is not None:
            return self.data[row, column]["value"]
        else:
            return self.values

    def configure(self, **kwargs):
        """ configure table widget attributes"""

        if "colors" in kwargs:
            self.colors = kwargs.pop("colors")
            self.fg_color = self.colors[0]
            self.fg_color2 = self.colors[1]
        if "fg_color" in kwargs:
            self.colors = (kwargs["fg_color"], kwargs.pop("fg_color"))
            self.fg_color = self.colors[0]
            self.fg_color2 = self.colors[1]
        if "bg_color" in kwargs:
            super().configure(bg_color=kwargs["bg_color"])
            self.inside_frame.configure(fg_color=kwargs["bg_color"])
        if "header_color" in kwargs:
            self.header_color = kwargs.pop("header_color")
        if "rows" in kwargs:
            self.rows = kwargs.pop("rows")
        if "columns" in kwargs:
            self.columns = kwargs.pop("columns")
        if "values" in kwargs:
            self.values = kwargs.pop("values")
        if "padx" in kwargs:
            self.padx = kwargs.pop("padx")
        if "pady" in kwargs:
            self.pady = kwargs.pop("pady")
        if "wraplength" in kwargs:
            self.wraplength = kwargs.pop("wraplength")

        for i in range(self.rows):
            for j in range(self.columns):
                self.data[i, j]["args"].update(kwargs)

        if "hover_color" in kwargs:
            self.hover_color = kwargs.pop("hover_color")
        if "text_color" in kwargs:
            self.text_color = kwargs.pop("text_color")
        if "border_width" in kwargs:
            self.border_width = kwargs.pop("border_width")
            super().configure(border_width=self.border_width)
            self.inside_frame.pack(expand=True, fill="both", padx=self.border_width, pady=self.border_width)
        if "border_color" in kwargs:
            self.border_color = kwargs.pop("border_color")
            super().configure(border_color=self.border_color)
        if "hover" in kwargs:
            self.hover = kwargs.pop("hover")
        if "anchor" in kwargs:
            self.anchor = kwargs.pop("anchor")
        if "corner_radius" in kwargs:
            self.corner = kwargs.pop("corner_radius")
            super().configure(corner_radius=self.corner)
        if "color_phase" in kwargs:
            self.phase = kwargs.pop("color_phase")
        if "justify" in kwargs:
            self.justify = kwargs.pop("justify")
        if "orientation" in kwargs:
            self.orient = kwargs.pop("orientation")
        if "width" in kwargs:
            self.width = kwargs.pop("width")
        if "height" in kwargs:
            self.height = kwargs.pop("height")

        self.update_values(self.values, **kwargs)

    def cget(self, param):
        if param == "width":
            return self.frame[0, 0].winfo_reqwidth()
        if param == "height":
            return self.frame[0, 0].winfo_reqheight()
        if param == "colors":
            return (self.fg_color, self.fg_color2)
        if param == "hover_color":
            return self.hover_color
        if param == "text_color":
            return self.text_color
        if param == "border_width":
            return self.border_width
        if param == "border_color":
            return self.border_color
        if param == "hover":
            return self.hover
        if param == "anchor":
            return self.anchor
        if param == "wraplength":
            return self.wraplength
        if param == "padx":
            return self.padx
        if param == "pady":
            return self.pady
        if param == "header_color":
            return self.header_color
        if param == "row":
            return self.rows
        if param == "column":
            return self.columns
        if param == "values":
            return self.values
        if param == "color_phase":
            return self.phase
        if param == "justify":
            return self.justify
        if param == "orientation":
            return self.orient
        return super().cget(param)

    def bind(self, sequence: str = None, command=None, add=True):
        """ bind all cells """
        self.binded_objects.append([sequence, command, add])

        super().bind(sequence, command, add)
        for i in self.frame:
            self.frame[i].bind(sequence, command, add)
        self.inside_frame.bind(sequence, command, add)

    def unbind(self, sequence: str = None, funcid: str = None):
        for i in self.binded_objects:
            if sequence in i:
                self.binded_objects.remove(i)

        super().unbind(sequence, funcid)
        for i in self.frame:
            self.frame[i].unbind(sequence, funcid)
        self.inside_frame.unbind(sequence, funcid)

    def update_values(self, values, **kwargs):
        self.values = values
        self.draw_table(**kwargs)
        self.update_data()
