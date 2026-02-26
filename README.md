# Manim Code Anim

代码输入动画效果，基于 Manim 库实现的代码块动画效果。

## 项目简介

`manim-code-anim` 是一个基于 Manim 的扩展库，用于在 Manim 动画中创建带有语法高亮的代码块动画。该库基于 [CasualCodersProjects/manim-code-blocks](https://github.com/CasualCodersProjects/manim-code-blocks) 库进行修改和扩展。

### 主要功能

- 支持多种编程语言的语法高亮
- 代码逐字显示动画效果
- 支持中文显示
- 可自定义字体和主题

## 安装

### 依赖项

- Python 3.12+
- Manim 0.20.0+
- tokenize-all-code 1.0.18+

### 安装方法

#### 方法一：使用 pip 安装（推荐）

```bash
# 直接从 PyPI 安装
pip install manim-code-anim
```

#### 方法二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/manim-code-anim.git
cd manim-code-anim

# 安装依赖
pip install -e .
```

项目已发布到 [PyPI](https://pypi.org/project/manim-code-anim/)，可以直接使用 pip 安装。

## 使用示例

### 基本使用

```python
from manim import *
from manim_code_anim.code_anim import CodeAnim, Python

class CodeAnimation(Scene):
    def construct(self):
        # 创建一个Python代码块
        code = CodeAnim(
            text='print("Hello World!")',
            language=Python
        )

        # 播放创建动画
        self.play(*code.create())
        self.wait(2)

        # 播放销毁动画
        self.play(*code.uncreate())
        self.wait()

if __name__ == "__main__":
    scene = CodeAnimation()
    scene.render()
```

### 多行代码

```python
from manim import *
from manim_code_anim.code_anim import CodeAnim, Python

class MultiLineCode(Scene):
    def construct(self):
        python_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
'''

        code = CodeAnim(
            text=python_code,
            language=Python
        )

        self.play(*code.create())
        self.wait(3)
        self.play(*code.uncreate())
        self.wait()
```

### 支持中文

```python
from manim import *
from manim_code_anim.code_anim import CodeAnim, Python

class ChineseCode(Scene):
    def construct(self):
        code = CodeAnim(
            text='''
# 这是中文注释
print("你好，世界！")  # 中文注释
''',
            language=Python
        )

        self.play(*code.create())
        self.wait(2)
        self.play(*code.uncreate())
        self.wait()
```

### 自定义字体

```python
from manim import *
from manim_code_anim.code_anim import CodeAnim, Python

class CustomFontCode(Scene):
    def construct(self):
        code = CodeAnim(
            text='print("Hello, 世界！")',
            language=Python,
            font="Courier New",        # 英文代码字体
            chinese_font="SimHei"      # 中文字体
        )

        self.play(*code.create())
        self.wait(2)
        self.play(*code.uncreate())
        self.wait()
```

### 支持的编程语言

- C
- C++
- C#
- Fortran
- Go
- Haskell
- Java
- JavaScript
- Lua
- Python
- Ruby
- Rust
- SQL
- TypeScript

## API 参考

### CodeAnim 类

```python
CodeAnim(
    text: str,  # 要显示的代码文本
    language: ProgrammingLanguage | None = None,  # 编程语言
    theme: Theme = OneDark,  # 语法高亮主题
    font: str = "FiraCode Nerd Font Mono",  # 英文代码字体
    chinese_font: str = "Microsoft YaHei",  # 中文字体
    **kwargs: object  # 传递给VGroup的其他参数
)
```

### 方法

- `create(**kwargs)`: 返回创建代码块的动画元组
- `uncreate(**kwargs)`: 返回销毁代码块的动画元组

## 基于的库

本项目基于 [CasualCodersProjects/manim-code-blocks](https://github.com/CasualCodersProjects/manim-code-blocks) 库，进行了以下修改：

- 添加了中文支持
- 优化了字体处理
- 修复了一些bug
- 完善了文档

## 许可证

[MIT License](LICENSE)