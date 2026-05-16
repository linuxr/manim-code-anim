import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from manim import Scene, config, BLUE, YELLOW, GREEN, Create, FadeOut

from src.manim_code_anim.code_anim import CodeAnim, JavaScript, Python, Rust


class TestCodeAnim(Scene):
    """测试CodeAnim的基本功能"""

    def construct(self) -> None:
        self.test_basic_usage()
        self.test_multiple_lines()
        self.test_different_languages()
        self.test_highlight()

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
    // 这是一个中文注释
    let message = "Hello World! 世界";
    println!("{}", message);
}
"""

        rust_anim = CodeAnim(text=rust_code, language=Rust)
        self.play(*rust_anim.create())
        self.wait(2)
        self.play(*rust_anim.uncreate())
        self.wait()

    def test_highlight(self):
        """测试高亮行"""
        # 定义一些示例代码
        code_text = """def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# 测试函数
result = fibonacci(10)
print(f"斐波那契数列第10项是: {result}")"""

        # 创建CodeAnim对象
        code = CodeAnim(code_text, language=Python)

        # 播放创建代码的动画
        self.play(*code.create())
        self.wait(1)

        # 高亮第1行（函数定义） - 用蓝色
        highlight1 = code.highlight_lines(BLUE, [1])
        self.play(Create(highlight1))
        self.wait(1)

        # 高亮第2-4行（递归逻辑） - 用黄色，同时移除之前的蓝色高亮
        highlight2 = code.highlight_lines(YELLOW, [2, 3, 4])
        self.play(FadeOut(highlight1), Create(highlight2))
        self.wait(1)

        # 高亮第6行（注释）和第7-8行（测试代码）- 用绿色
        highlight3 = code.highlight_lines(GREEN, [6, 7, 8])
        self.play(FadeOut(highlight2), Create(highlight3))
        self.wait(1)


if __name__ == "__main__":
    # 运行测试场景
    config.frame_rate = 10
    scene = TestCodeAnim()
    scene.render(preview=True)
