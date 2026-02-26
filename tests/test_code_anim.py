import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from manim import *
from src.manim_code_anim.code_anim import CodeAnim, Python, JavaScript, Rust


class TestCodeAnim(Scene):
    """测试CodeBlock的基本功能"""

    def construct(self) -> None:
        self.test_basic_usage()
        self.test_multiple_lines()
        self.test_different_languages()
        self.test_no_language()

    def test_basic_usage(self):
        """测试基本使用方法"""
        # 创建一个简单的Python代码动画
        code = CodeAnim(text='print("Hello World!")', language=Python)
        self.play(*code.create())
        self.wait(2)
        self.play(*code.uncreate())
        self.wait()

    def test_multiple_lines(self):
        """测试多行代码"""
        python_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""

        code = CodeAnim(text=python_code, language=Python)
        self.play(*code.create())
        self.wait(2)
        self.play(*code.uncreate())
        self.wait()

    def test_different_languages(self):
        """测试不同编程语言"""
        # 测试JavaScript
        js_code = """
function greet(name) {
    return "Hello, " + name + "!";
}

console.log(greet("World"));
"""

        js_anim = CodeAnim(text=js_code, language=JavaScript)
        self.play(*js_anim.create())
        self.wait(2)
        self.play(*js_anim.uncreate())
        self.wait()

        # 测试Rust
        rust_code = """
fn main() {
    let message = "Hello World!";
    println!("{}", message);
}
"""

        rust_anim = CodeAnim(text=rust_code, language=Rust)
        self.play(*rust_anim.create())
        self.wait(2)
        self.play(*rust_anim.uncreate())
        self.wait()

    def test_no_language(self):
        """测试不指定语言的情况"""
        code = CodeAnim(text="This is some plain text without syntax highlighting")
        self.play(*code.create())
        self.wait(2)
        self.play(*code.uncreate())
        self.wait()


if __name__ == "__main__":
    # 运行测试场景
    scene = TestCodeAnim()
    scene.render(preview=True)
