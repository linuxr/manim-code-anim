import re as regex
from abc import ABC as abstract
from typing import Callable
import numpy as np
import tokenize_all
from manim import (
    DOWN,
    LEFT,
    UP,
    BackgroundRectangle,
    FadeIn,
    FadeOut,
    MarkupText,
    Unwrite,
    VGroup,
    Write,
    Rectangle,
)
from .language_colors import language_colors


class Theme:
    """用于语法高亮 `CodeAnim` 的主题。"""

    colors: dict[str, list[str | Callable]]
    """
    该主题的颜色，以字典形式表示。字典的键是十六进制颜色（如 `"#FFFFFF"`），值是应该使用该颜色着色的令牌类型列表（如 `["keyword", "operation"]`）。
    """

    group_matchers: list[str]

    def __init__(
        self, colors: dict[str, list[str | Callable]], group_matchers: list[str]
    ):
        """
        使用指定的 `colors` 创建新的 `Theme`。请参阅 `colors` 字段以了解规范。
        """
        self.colors = colors
        self.group_matchers = group_matchers

    def color_for(self, token: tokenize_all.Token) -> str:
        """返回根据此主题为给定令牌指定的颜色，如果未指定则返回 `"#FFFFFF"`。"""
        for key, value in self.colors.items():
            if token.type in value:
                return key
        return "#FFFFFF"


OneDark = Theme(
    colors={
        "#C678DD": ["keyword", "directive"],  # 紫色
        "#61AFEF": ["function"],  # 蓝色
        "#E06C75": ["identifier"],  # 红色
        "#98C379": ["string"],  # 绿色
        "#56B6C2": ["symbol"],  # 青色
        "#D19A66": ["number", "keyword literal"],  # 橙色
        "#E5C07B": ["class name"],  # 黄色
        "#888888": ["comment"],  # 灰色
    },
    group_matchers=["#D19A66", "#C678DD", "#56B6C2"],  # 橙色  # 紫色  # 青色
)
"""来自 `Atom` 文本编辑器的 'One Dark' 主题。"""


class ProgrammingLanguage(abstract):
    """用于渲染 `CodeAnim` 的编程语言。"""

    name: str
    """编程语言的名称。名称显示在代码块上方的标题卡片上。"""

    color: str
    """
    编程语言的颜色。颜色用于在代码块上方的标题卡片中显示名称。默认情况下，对于支持的语言使用官方 GitHub 语言颜色，请参阅 https://github.com/ozh/github-colors/blob/master/colors.json。
    """

    language: tokenize_all.TokenizableLanguage
    """
    语言的 `TokenizableLanguage`。
    """

    def __init__(self, name: str, tokenize_name: str | None = None):
        self.name = name
        self.language = getattr(tokenize_all, tokenize_name if tokenize_name else name)
        self.color = language_colors[name]["color"]
        if self.color is None:
            print(f"Warning: no color found for {name}")
        if self.language is None:
            print(f"Warning: no tokenization found for {name}")


class CodeAnim(VGroup):
    """
    代码块。默认情况下，代码块呈现为 `MarkupText` 对象，后面带有 `BackgroundRectangles`。此外，在代码块上方的左侧会显示一个包含语言名称和颜色的标题。语法高亮通过从 `microsoft/vscode` 提取 `.tmLanguage.json` 文件来使用 `TextMates` 完成。请参阅 https://github.com/microsoft/vscode/tree/main/extensions。
    """

    code: MarkupText
    """构成代码块的主要 `MarkupText` 对象。相当于在 `[1]` 处索引。"""

    title: MarkupText
    """
    构成代码块顶部语言名称标题的标题 `MarkupText` 对象。相当于在 `[3]` 处索引。
    """

    code_background: BackgroundRectangle
    """代码块标记对象的 `BackgroundRectangle`。相当于在 `[0]` 处索引。"""

    title_background: BackgroundRectangle
    """
    列出代码块上方语言名称的 `title` 对象的 `BackgroundRectangle`。相当于在 `[2]` 处索引。
    """

    lines: list[str]  # 保存原始代码行
    original_text: str  # 保存原始输入文本

    def __init__(
        self,
        text: str,
        language: ProgrammingLanguage,
        theme: Theme = OneDark,
        font: str = "FiraCode Nerd Font Mono",
        chinese_font: str = "Microsoft YaHei",
        title_font_size: int = 48,
        code_font_size: int = 45,
        **kwargs: object,
    ):
        """
        创建新的 `CodeAnim`。
        ### 参数
        - `text [str]`:
            - 要渲染的源代码。
        - `language [ProgrammingLanguage]`:
            - 渲染代码时使用的编程语言。语言决定代码块标题的文本和颜色，以及代码块的语法高亮。
        - `theme [Theme]`:
            - 用于高亮代码的主题。默认为 `OneDark`。
        - `font [str]`:
            - 用于渲染代码的字体。默认为 `Consolas`。
        - `chinese_font [str]`:
            - 用于渲染中文字符的字体。默认为 `Microsoft YaHei`（微软雅黑）。
        - `**kwargs [Any]`:
            - 传递给 `VGroup` 的其他参数。
        """
        self.original_text = text
        self.lines = text.split("\n")
        group_count = 0
        finished: list[str] = []

        for line in self.lines:
            tokens = language.language.tokenize(line)
            for token in tokens:
                if token.type.startswith("left"):
                    # 只转义HTML/XML特殊字符
                    escaped_value = self._escape_html_chars(token.value)
                    finished.append(
                        '<span foreground="'
                        + theme.group_matchers[group_count % len(theme.group_matchers)]
                        + '">'
                        + escaped_value
                        + "</span>"
                    )
                    group_count += 1
                elif token.type.startswith("right"):
                    group_count -= 1
                    # 只转义HTML/XML特殊字符
                    escaped_value = self._escape_html_chars(token.value)
                    finished.append(
                        '<span foreground="'
                        + theme.group_matchers[group_count % len(theme.group_matchers)]
                        + '">'
                        + escaped_value
                        + "</span>"
                    )
                elif token.type == "whitespace":
                    # 只转义HTML/XML特殊字符
                    finished.append(self._escape_html_chars(token.value))
                else:
                    # 只转义HTML/XML特殊字符
                    safe_value = self._escape_html_chars(token.value)
                    # 检测整个safe_value是否包含中文
                    has_chinese = any(
                        "\u4e00" <= char <= "\u9fff" for char in safe_value
                    )
                    font_to_use = chinese_font if has_chinese else font
                    finished.append(
                        '<span foreground="'
                        + theme.color_for(token=token)
                        + '" '
                        + 'font_family="'
                        + font_to_use
                        + '">'
                        + safe_value
                        + "</span>"
                    )
            finished.append("\n")  # 使用真正的换行符

        # 移除最后多余的换行符
        finished_text = "".join(finished).rstrip("\n")

        # 创建代码文本对象
        markup = MarkupText(
            finished_text,
            font=font,
            font_size=code_font_size,
            z_index=3,
            tab_width=4,  # 设置制表符宽度
        )
        markup.scale(0.4)
        background_rect = BackgroundRectangle(
            markup, color="#282C34", buff=0.2, fill_opacity=1
        )

        # 检测语言名称是否包含中文
        lang_has_chinese = any("\u4e00" <= char <= "\u9fff" for char in language.name)
        lang_font = chinese_font if lang_has_chinese else font
        lang_name = MarkupText(
            language.name, font=lang_font, font_size=title_font_size, z_index=3
        )
        lang_name.next_to(background_rect, UP)
        lang_name.set_color(language.color)
        lang_name.scale(0.3, about_point=lang_name.get_corner(DOWN + LEFT))

        lang_background = BackgroundRectangle(
            lang_name, color="#282C34", buff=0.15, fill_opacity=1
        )

        pos = background_rect.get_corner(UP + LEFT) + np.array(
            [lang_background.width / 2, lang_background.height / 2 - 0.005, 0]
        )
        VGroup(lang_name, lang_background).move_to(pos)

        self.title = lang_name
        self.title_background = lang_background
        super().__init__(background_rect, markup, lang_background, lang_name, **kwargs)
        self.code = markup
        self.code_background = background_rect

    def _escape_html_chars(self, text: str) -> str:
        """转义HTML/XML特殊字符，但保留其他字符原样"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text

    def highlight_lines(self, color, lines: list[int]):
        """
        高亮指定的代码行

        参数:
        - color [ManimColor]: 高亮使用的颜色
        - lines [list[int]]: 需要高亮的行号列表（从1开始计数）
        """
        # 确保行号有效（从1开始，转换为0索引）
        valid_lines = [line - 1 for line in lines if 1 <= line <= len(self.lines)]

        highlighted_rects = VGroup()

        if not valid_lines or len(self.lines) == 0:
            return highlighted_rects

        # 计算每行的大致高度
        line_height = self.code.height / len(self.lines) if len(self.lines) > 0 else 0.3

        for line_idx in valid_lines:
            # 创建一个矩形作为高亮背景
            rect_width = self.code.width  # 代码宽度
            rect_height = line_height * 0.8  # 稍小于行高

            # 计算矩形的位置
            # 获取代码框的左边界
            left_edge = self.code.get_left()[0] + (self.code.width - rect_width) / 2

            # 计算行的垂直位置
            # 代码是从上到下排列的，第一行在最上面
            y_pos = self.code.get_top()[1] - (line_idx + 0.5) * line_height

            highlight_rect = Rectangle(
                width=rect_width,
                height=rect_height,
                color=color,
                fill_color=color,
                fill_opacity=0.3,
                stroke_opacity=0,
            )

            # 定位矩形
            highlight_rect.move_to(
                [left_edge + rect_width / 2, y_pos, 0]  # x位置  # y位置  # z位置
            )

            highlighted_rects.add(highlight_rect)

        return highlighted_rects

    def create(self, **kwargs) -> tuple[FadeIn, Write, FadeIn, Write]:
        """
        返回用于创建代码块的动画元组。使用方式如下：

        ```
        python = CodeAnim('print("Hello World!")', language = Python)
        self.play(*python.create())
        ```
        默认情况下，动画将对 `background` 和 `title_background` 使用 `FadeIn`，对 `code` 和 `title` 使用 `AddTextLetterByLetter`。
        """
        return (
            FadeIn(self.code_background, **kwargs),
            Write(self.code, **kwargs),
            FadeIn(self.title_background, **kwargs),
            Write(self.title, **kwargs),
        )

    def uncreate(self, **kwargs):
        """
        返回用于取消创建代码块的动画元组。使用方式如下：
        ```
        python = CodeAnim('print("Hello World!")', language = Python)
        self.play(*python.uncreate())
        ```
        默认情况下，动画将对 `background` 和 `title_background` 使用 `FadeOut`，对 `code` 和 `title` 使用 `Uncreate`。
        """
        return (
            FadeOut(self.code_background, **kwargs),
            Unwrite(self.code, **kwargs),
            FadeOut(self.title_background, **kwargs),
            Unwrite(self.title, **kwargs),
        )


C = ProgrammingLanguage("C")
"""`C` 编程语言，用于在 `CodeAnim` 中渲染 `C` 代码"""

Cpp = ProgrammingLanguage("C++", tokenize_name="Cpp")
"""`C++` 编程语言，用于在 `CodeAnim` 中渲染 `C++` 代码。"""

CSharp = ProgrammingLanguage("C#", tokenize_name="CSharp")
"""`C#` 编程语言，用于在 `CodeAnim` 中渲染 `C#` 代码。"""

Fortran = ProgrammingLanguage("Fortran")
"""`Fortran` 编程语言，用于在 `CodeAnim` 中渲染 Fortran 代码。"""

Go = ProgrammingLanguage("Go")
"""`Go` 编程语言，用于在 `CodeAnim` 中渲染 `Go` 代码。"""

Haskell = ProgrammingLanguage("Haskell")
"""`Haskell` 编程语言，用于在 `CodeAnim` 中渲染 `Haskell` 代码。"""

Java = ProgrammingLanguage("Java")
"""`Java` 编程语言，用于在 `CodeAnim` 中渲染 `Java` 代码。"""

JavaScript = ProgrammingLanguage("JavaScript")
"""`JavaScript` 编程语言，用于在 `CodeAnim` 中渲染 `JavaScript` 代码。"""

Lua = ProgrammingLanguage("Lua")
"""`Lua` 编程语言，用于在 `CodeAnim` 中渲染 `Lua` 代码。 """

Python = ProgrammingLanguage("Python")
"""`Python` 编程语言，用于在 `CodeAnim` 中渲染 `Python` 代码。"""

Ruby = ProgrammingLanguage("Ruby")
"""`Ruby` 编程语言，用于在 `CodeAnim` 中渲染 `Ruby` 代码。"""

Rust = ProgrammingLanguage("Rust")
"""`Rust` 编程语言，用于在 `CodeAnim` 中渲染 `Rust` 代码。"""

SQL = ProgrammingLanguage("SQL")
"""`SQL` 编程语言，用于在 `CodeAnim` 中渲染 `SQL` 代码。"""

TypeScript = ProgrammingLanguage("TypeScript")
"""`TypeScript` 编程语言，用于在 `CodeAnim` 中渲染 `TypeScript` 代码"""
