from manim import *
import tokenize_all

import re as regex
from abc import ABC as abstract
from typing import Callable
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

        if self.color == None:
            print(f"Warning: no color found for {name}")
        if self.language == None:
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

    def __init__(
        self,
        text: str,
        language: ProgrammingLanguage | None = None,
        theme: Theme = OneDark,
        font: str = "FiraCode Nerd Font Mono",
        chinese_font: str = "Microsoft YaHei",
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

        if language:
            lines = text.split("\n")
            group_count = 0
            finished: list[str] = []
            for line in lines:
                tokens = language.language.tokenize(line)
                for token in tokens:
                    if token.type.startswith("left"):
                        finished.append(
                            '<span foreground="'
                            + theme.group_matchers[
                                group_count % len(theme.group_matchers)
                            ]
                            + '">'
                            + token.value
                            + "</span>"
                        )
                        group_count += 1
                    elif token.type.startswith("right"):
                        group_count -= 1
                        finished.append(
                            '<span foreground="'
                            + theme.group_matchers[
                                group_count % len(theme.group_matchers)
                            ]
                            + '">'
                            + token.value
                            + "</span>"
                        )
                    elif token.type == "whitespace":
                        finished.append(token.value)
                    else:
                        safe_value = regex.sub("&", "&amp;", token.value)
                        safe_value = regex.sub("<", "&lt;", safe_value)
                        safe_value = regex.sub(">", "&gt;", safe_value)

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
                finished.append("\r")

            finished_text = "".join(finished)
        else:
            # 检测整个safe_value是否包含中文
            has_chinese = any("\u4e00" <= char <= "\u9fff" for char in text)
            font_to_use = chinese_font if has_chinese else font
            finished_text = (
                '<span foreground="#FFFFFF" font_family="'
                + font_to_use
                + '">'
                + text
                + "</span>"
            )

        markup = MarkupText(finished_text, font=font, z_index=3)
        markup.scale(0.4)
        background_rect = BackgroundRectangle(
            markup, color="#282C34", buff=0.2, fill_opacity=1
        )

        if language:
            # 检测语言名称是否包含中文
            lang_has_chinese = any(
                "\u4e00" <= char <= "\u9fff" for char in language.name
            )
            lang_font = chinese_font if lang_has_chinese else font

            lang_name = MarkupText(language.name, font=lang_font, z_index=3)
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

            super().__init__(
                background_rect, markup, lang_background, lang_name, **kwargs
            )
        else:
            self.title = None
            self.title_background = None
            super().__init__(background_rect, markup, **kwargs)

        self.code = markup
        self.code_background = background_rect

    def create(
        self, **kwargs
    ) -> tuple[FadeIn, AddTextLetterByLetter, FadeIn, AddTextLetterByLetter]:
        """
        返回用于创建代码块的动画元组。使用方式如下：\n
        ```
        python = CodeAnim('print("Hello World!")', language = Python)
        self.play(*python.create())
        ```
        默认情况下，动画将对 `background` 和 `title_background` 使用 `FadeIn`，对 `code` 和 `title` 使用 `AddTextLetterByLetter`。
        """
        if getattr(self, "title", None) and getattr(self, "title_background", None):
            return (
                FadeIn(self.code_background, **kwargs),
                AddTextLetterByLetter(self.code, **kwargs),
                FadeIn(self.title_background, **kwargs),
                AddTextLetterByLetter(self.title, **kwargs),
            )

        return (
            FadeIn(self.code_background, **kwargs),
            AddTextLetterByLetter(self.code, **kwargs),
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
        if getattr(self, "title", None) and getattr(self, "title_background", None):
            return (
                FadeOut(self.code_background, **kwargs),
                Uncreate(self.code, **kwargs),
                FadeOut(self.title_background, **kwargs),
                Uncreate(self.title, **kwargs),
            )

        return (
            FadeOut(self.code_background, **kwargs),
            Uncreate(self.code, **kwargs),
        )


C = ProgrammingLanguage("C")
"""`C` 编程语言，用于在 `CodeBlocks` 中渲染 `C` 代码"""

Cpp = ProgrammingLanguage("C++", tokenize_name="Cpp")
"""`C++` 编程语言，用于在 `CodeBlocks` 中渲染 `C++` 代码。"""

CSharp = ProgrammingLanguage("C#", tokenize_name="CSharp")
"""`C#` 编程语言，用于在 `CodeBlocks` 中渲染 `C#` 代码。"""

Fortran = ProgrammingLanguage("Fortran")
"""`Fortran` 编程语言，用于在 `CodeBlocks` 中渲染 Fortran 代码。"""

Go = ProgrammingLanguage("Go")
"""`Go` 编程语言，用于在 `CodeBlocks` 中渲染 `Go` 代码。"""

Haskell = ProgrammingLanguage("Haskell")
"""`Haskell` 编程语言，用于在 `CodeBlocks` 中渲染 `Haskell` 代码。"""

Java = ProgrammingLanguage("Java")
"""`Java` 编程语言，用于在 `CodeBlocks` 中渲染 `Java` 代码。"""

JavaScript = ProgrammingLanguage("JavaScript")
"""`JavaScript` 编程语言，用于在 `CodeBlocks` 中渲染 `JavaScript` 代码。"""

Lua = ProgrammingLanguage("Lua")
"""`Lua` 编程语言，用于在 `CodeBlocks` 中渲染 `Lua` 代码。 """

Python = ProgrammingLanguage("Python")
"""`Python` 编程语言，用于在 `CodeBlocks` 中渲染 `Python` 代码。"""

Ruby = ProgrammingLanguage("Ruby")
"""`Ruby` 编程语言，用于在 `CodeBlocks` 中渲染 `Ruby` 代码。"""

Rust = ProgrammingLanguage("Rust")
"""`Rust` 编程语言，用于在 `CodeBlocks` 中渲染 `Rust` 代码。"""

SQL = ProgrammingLanguage("SQL")
"""`SQL` 编程语言，用于在 `CodeBlocks` 中渲染 `SQL` 代码。"""

TypeScript = ProgrammingLanguage("TypeScript")
"""`TypeScript` 编程语言，用于在 `CodeBlocks` 中渲染 `TypeScript` 代码"""
