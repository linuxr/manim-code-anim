from abc import ABC as abstract
from typing import Callable

from manim import (
    BackgroundRectangle,
    DOWN,
    FadeIn,
    FadeOut,
    LEFT,
    MarkupText,
    Rectangle,
    UP,
    Unwrite,
    VGroup,
    Write,
)
import numpy as np
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.token import Token as PygmentsToken
from pygments.util import ClassNotFound

from .language_colors import language_colors


# 创建 Token 类以兼容旧的 tokenize_all API
class Token:
    """兼容 tokenize_all.Token 的包装类"""

    def __init__(
        self,
        type: str,
        value: str,
        start: int = 0,
        line_number: int = 1,
        line_start: int = 0,
    ):
        self.type = type
        self.value = value
        self.start = start
        self.line_number = line_number
        self.line_start = line_start

    def __str__(self):
        return f"Token[ type = {self.type}, value = {repr(self.value)}, start = {self.start}, line_number = {self.line_number}, line_start = {self.line_start} ]"


# Pygments token 类型到 tokenize_all 风格的映射
PYGMENTS_TO_OLD_STYLE = {
    PygmentsToken.Keyword: "keyword",
    PygmentsToken.Keyword.Constant: "keyword literal",
    PygmentsToken.Keyword.Declaration: "keyword",
    PygmentsToken.Keyword.Namespace: "keyword",
    PygmentsToken.Keyword.Pseudo: "keyword literal",
    PygmentsToken.Keyword.Reserved: "keyword",
    PygmentsToken.Keyword.Type: "keyword",
    PygmentsToken.Name: "identifier",
    PygmentsToken.Name.Builtin: "identifier",
    PygmentsToken.Name.Class: "class name",
    PygmentsToken.Name.Function: "function",
    PygmentsToken.Name.Decorator: "function",
    PygmentsToken.Name.Variable: "identifier",
    PygmentsToken.Name.Constant: "constant",
    PygmentsToken.Name.Attribute: "identifier",
    PygmentsToken.Name.Label: "identifier",
    PygmentsToken.Name.Namespace: "identifier",
    PygmentsToken.Name.Tag: "identifier",
    PygmentsToken.Literal.String: "string",
    PygmentsToken.Literal.String.Double: "string",
    PygmentsToken.Literal.String.Single: "string",
    PygmentsToken.Literal.String.Doc: "string",
    PygmentsToken.Literal.String.Backtick: "string",
    PygmentsToken.Literal.String.Char: "string",
    PygmentsToken.Literal.String.Escape: "string",
    PygmentsToken.Literal.String.Heredoc: "string",
    PygmentsToken.Literal.String.Interpol: "string",
    PygmentsToken.Literal.String.Other: "string",
    PygmentsToken.Literal.String.Regex: "string",
    PygmentsToken.Literal.String.Symbol: "string",
    PygmentsToken.Literal.Number: "number",
    PygmentsToken.Literal.Number.Float: "number",
    PygmentsToken.Literal.Number.Hex: "number",
    PygmentsToken.Literal.Number.Integer: "number",
    PygmentsToken.Literal.Number.Oct: "number",
    PygmentsToken.Literal.Number.Bin: "number",
    PygmentsToken.Operator: "symbol",
    PygmentsToken.Operator.Word: "keyword",
    PygmentsToken.Punctuation: "symbol",
    PygmentsToken.Comment: "comment",
    PygmentsToken.Comment.Single: "comment",
    PygmentsToken.Comment.Multiline: "comment",
    PygmentsToken.Comment.Preproc: "directive",
    PygmentsToken.Comment.PreprocFile: "directive",
    PygmentsToken.Comment.Hashbang: "comment",
    PygmentsToken.Comment.Special: "comment",
    PygmentsToken.Text.Whitespace: "whitespace",
    PygmentsToken.Text: "whitespace",
    PygmentsToken.Error: "identifier",
    PygmentsToken.Other: "whitespace",
}


def _map_pygments_token(pygments_token) -> str:
    """将 Pygments token 映射为旧的 tokenize_all 风格字符串"""
    # 尝试精确匹配
    if pygments_token in PYGMENTS_TO_OLD_STYLE:
        return PYGMENTS_TO_OLD_STYLE[pygments_token]

    # 尝试父级匹配
    parent = pygments_token.parent
    while parent and parent != PygmentsToken:
        if parent in PYGMENTS_TO_OLD_STYLE:
            return PYGMENTS_TO_OLD_STYLE[parent]
        parent = parent.parent

    # 默认返回 identifier
    return "identifier"


class PygmentsLanguageAdapter:
    """将 Pygments lexer 适配为 tokenize_all 风格的接口"""

    def __init__(self, lexer_name: str):
        self.lexer_name = lexer_name
        try:
            self.lexer = get_lexer_by_name(lexer_name)
        except ClassNotFound:
            print(f"Warning: no lexer found for {lexer_name}")
            self.lexer = None

    def tokenize(self, code: str) -> list[Token]:
        """使用 Pygments 对代码进行分词，返回兼容旧 API 的 Token 列表"""
        if self.lexer is None:
            return [Token(type="identifier", value=code)]

        tokens = []
        pos = 0
        line_number = 1
        line_start = 0

        for pygments_token_type, value in self.lexer.get_tokens(code):
            # 跳过 ENDMARKER
            if pygments_token_type == PygmentsToken.Text and value == "":
                continue

            token_type = _map_pygments_token(pygments_token_type)

            token = Token(
                type=token_type,
                value=value,
                start=pos,
                line_number=line_number,
                line_start=line_start,
            )
            tokens.append(token)

            # 更新位置信息
            pos += len(value)
            if "\n" in value:
                lines = value.split("\n")
                line_number += len(lines) - 1
                line_start = (
                    len(lines[-1]) if len(lines) > 1 else line_start + len(value)
                )
            else:
                line_start += len(value)

        return tokens


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

    def color_for(self, token: Token) -> str:
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

    language: PygmentsLanguageAdapter
    """
    语言的 `PygmentsLanguageAdapter`。
    """

    def __init__(self, name: str, pygments_name: str | None = None):
        self.name = name
        self.language = PygmentsLanguageAdapter(
            pygments_name if pygments_name else name.lower()
        )
        self.color = language_colors[name]["color"]
        if self.color is None:
            print(f"Warning: no color found for {name}")
        if self.language.lexer is None:
            print(f"Warning: no lexer found for {name}")


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
        line_spacing: float = 0.2,
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
        - `title_font_size [int]`:
            - 标题字体大小。默认为 48。
        - `code_font_size [int]`:
            - 代码字体大小。默认为 45。
        - `line_spacing [float]`:
            - 代码行间距。值越小行间距越紧凑，默认为 0.6。
        - `**kwargs [Any]`:
            - 传递给 `VGroup` 的其他参数。
        """
        self.original_text = text
        self.lines = text.split("\n")
        group_count = 0
        finished: list[str] = []

        # 计算 line_height 值（基于字体大小的倍数）
        # line_height=1.0 是默认值，0.5 会更紧凑
        line_height_value = max(0.3, line_spacing)

        for line in self.lines:
            tokens = language.language.tokenize(line)
            for token in tokens:
                if token.type.startswith("left"):
                    # 只转义HTML/XML特殊字符
                    escaped_value = self._escape_html_chars(token.value)
                    finished.append(
                        '<span foreground="'
                        + theme.group_matchers[group_count % len(theme.group_matchers)]
                        + '" line_height="'
                        + str(line_height_value)
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
                        + '" line_height="'
                        + str(line_height_value)
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
                        + '" line_height="'
                        + str(line_height_value)
                        + '">'
                        + safe_value
                        + "</span>"
                    )
            finished.append(
                '<span line_height="' + str(line_height_value) + '">\n</span>'
            )  # 使用带 line_height 的换行符

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
        text = text.replace("'", "&#39;")
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


C = ProgrammingLanguage("C", pygments_name="c")
"""`C` 编程语言，用于在 `CodeAnim` 中渲染 `C` 代码"""

Cpp = ProgrammingLanguage("C++", pygments_name="cpp")
"""`C++` 编程语言，用于在 `CodeAnim` 中渲染 `C++` 代码。"""

CSharp = ProgrammingLanguage("C#", pygments_name="csharp")
"""`C#` 编程语言，用于在 `CodeAnim` 中渲染 `C#` 代码。"""

Fortran = ProgrammingLanguage("Fortran", pygments_name="fortran")
"""`Fortran` 编程语言，用于在 `CodeAnim` 中渲染 Fortran 代码。"""

Go = ProgrammingLanguage("Go", pygments_name="go")
"""`Go` 编程语言，用于在 `CodeAnim` 中渲染 `Go` 代码。"""

Haskell = ProgrammingLanguage("Haskell", pygments_name="haskell")
"""`Haskell` 编程语言，用于在 `CodeAnim` 中渲染 `Haskell` 代码。"""

Java = ProgrammingLanguage("Java", pygments_name="java")
"""`Java` 编程语言，用于在 `CodeAnim` 中渲染 `Java` 代码。"""

JavaScript = ProgrammingLanguage("JavaScript", pygments_name="javascript")
"""`JavaScript` 编程语言，用于在 `CodeAnim` 中渲染 `JavaScript` 代码。"""

Lua = ProgrammingLanguage("Lua", pygments_name="lua")
"""`Lua` 编程语言，用于在 `CodeAnim` 中渲染 `Lua` 代码。 """

Python = ProgrammingLanguage("Python", pygments_name="python")
"""`Python` 编程语言，用于在 `CodeAnim` 中渲染 `Python` 代码。"""

Ruby = ProgrammingLanguage("Ruby", pygments_name="ruby")
"""`Ruby` 编程语言，用于在 `CodeAnim` 中渲染 `Ruby` 代码。"""

Rust = ProgrammingLanguage("Rust", pygments_name="rust")
"""`Rust` 编程语言，用于在 `CodeAnim` 中渲染 `Rust` 代码。"""

SQL = ProgrammingLanguage("SQL", pygments_name="sql")
"""`SQL` 编程语言，用于在 `CodeAnim` 中渲染 `SQL` 代码。"""

TypeScript = ProgrammingLanguage("TypeScript", pygments_name="typescript")
"""`TypeScript` 编程语言，用于在 `CodeAnim` 中渲染 `TypeScript` 代码"""
