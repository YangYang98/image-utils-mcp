from typing import List, Any, Optional, Dict

from ..bean.BaseModel import ToolParameter
from .BaseTool import BaseTool
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import sys
import math


def get_chinese_font(font_size=24, bold=False):
    """
    获取可用的中文字体，优先使用系统字体
    """
    # 常见的中文字体路径（跨平台）
    font_paths = []

    # Windows字体路径
    if sys.platform.startswith('win'):
        windows_font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
        if bold:
            font_paths.extend([
                os.path.join(windows_font_dir, 'msyhbd.ttc'),  # 微软雅黑粗体
                os.path.join(windows_font_dir, 'simhei.ttf'),  # 黑体
                os.path.join(windows_font_dir, 'simsun.ttc'),  # 宋体
                os.path.join(windows_font_dir, 'msyh.ttc'),  # 微软雅黑
                os.path.join(windows_font_dir, 'Deng.ttf'),  # 等线
            ])
        else:
            font_paths.extend([
                os.path.join(windows_font_dir, 'simhei.ttf'),  # 黑体
                os.path.join(windows_font_dir, 'simsun.ttc'),  # 宋体
                os.path.join(windows_font_dir, 'msyh.ttc'),  # 微软雅黑
                os.path.join(windows_font_dir, 'msyhbd.ttc'),  # 微软雅黑粗体
                os.path.join(windows_font_dir, 'Deng.ttf'),  # 等线
            ])

    # macOS字体路径
    elif sys.platform == 'darwin':
        mac_font_dir = '/System/Library/Fonts'
        if bold:
            font_paths.extend([
                os.path.join(mac_font_dir, 'PingFang.ttc'),  # 苹方
                os.path.join(mac_font_dir, 'STHeiti Medium.ttc'),  # 黑体中号
                os.path.join(mac_font_dir, 'STHeiti Light.ttc'),  # 黑体
                '/Library/Fonts/Arial Unicode.ttf',  # Arial Unicode
            ])
        else:
            font_paths.extend([
                os.path.join(mac_font_dir, 'PingFang.ttc'),  # 苹方
                os.path.join(mac_font_dir, 'STHeiti Light.ttc'),  # 黑体
                os.path.join(mac_font_dir, 'STHeiti Medium.ttc'),  # 黑体中号
                '/Library/Fonts/Arial Unicode.ttf',  # Arial Unicode
            ])

    # Linux字体路径
    else:
        linux_font_dirs = [
            '/usr/share/fonts/truetype/droid',
            '/usr/share/fonts/truetype/noto',
            '/usr/share/fonts/truetype/wqy',
            '/usr/share/fonts/opentype/noto',
        ]
        for font_dir in linux_font_dirs:
            if os.path.exists(font_dir):
                font_paths.extend([
                    os.path.join(font_dir, 'DroidSansFallbackFull.ttf'),
                    os.path.join(font_dir, 'NotoSansCJK-Regular.ttc'),
                    os.path.join(font_dir, 'wqy-microhei.ttc'),
                ])

    # 通用字体（如果系统中存在）
    common_fonts = [
        'simhei.ttf',
        'simsun.ttc',
        'msyh.ttc',
        'arialuni.ttf',
        'Arial Unicode.ttf',
    ]

    # 添加当前目录下的字体
    for font in common_fonts:
        if os.path.exists(font):
            font_paths.append(font)

    # 尝试加载字体
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
        except:
            continue

    # 如果找不到任何中文字体，尝试使用默认字体
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except:
        return ImageFont.load_default()


def split_text_into_pages(content, chars_per_line=25, lines_per_page=25):
    """
    将长文本分割成多个页面

    参数:
    - content: 原始文本内容
    - chars_per_line: 每行字符数
    - lines_per_page: 每页行数

    返回:
    - 页面列表，每个页面是一个字符串列表
    """
    # 分割原始文本行
    original_lines = content.split('\n')
    pages = []
    current_page = []
    current_line_count = 0

    for line in original_lines:
        if not line.strip():
            # 空行，直接添加到当前页面
            if current_line_count < lines_per_page:
                current_page.append("")  # 空行
                current_line_count += 1
            else:
                # 当前页已满，开始新页面
                pages.append(current_page)
                current_page = [""]  # 新页面以空行开始
                current_line_count = 1
            continue

        # 处理非空行，需要换行
        # 将长行按字符数分割
        for i in range(0, len(line), chars_per_line):
            segment = line[i:i + chars_per_line]

            if current_line_count >= lines_per_page:
                # 当前页已满，开始新页面
                pages.append(current_page)
                current_page = []
                current_line_count = 0

            current_page.append(segment)
            current_line_count += 1

    # 添加最后一页
    if current_page:
        pages.append(current_page)

    return pages


def create_smart_multi_page_story(title, content, max_pages=None,
                                  output_file_path_prefix=os.path.abspath(os.sep), width=800, height=1200):
    """
    智能分页创建多页黑底白字故事图片

    参数:
    - title: 标题
    - content: 内容
    - max_pages: 最大页数限制（None表示无限制）
    - output_prefix: 输出文件前缀
    - width: 图片宽度
    - height: 图片高度
    """
    # 获取字体以计算行高等参数
    title_font = get_chinese_font(36, bold=True)  # 加粗标题字体
    content_font = get_chinese_font(27)

    # 创建临时图片用于计算文本大小
    temp_image = Image.new('RGB', (width, height), 'black')
    temp_draw = ImageDraw.Draw(temp_image)

    # 计算可用高度
    title_height = 120  # 标题区域高度
    page_num_height = 50  # 页码区域高度
    border_margin = 20  # 边框边距

    available_height = height - title_height - page_num_height - border_margin

    # 计算行高
    try:
        line_height = 35  # 固定行高
    except:
        line_height = 40  # 备用行高

    # 计算每页可容纳的行数
    lines_per_page = available_height // line_height

    print(f"页面配置:")
    print(f"  - 图片尺寸: {width}x{height}")
    print(f"  - 可用高度: {available_height}像素")
    print(f"  - 行高: {line_height}像素")
    print(f"  - 每页可容纳行数: {lines_per_page}")

    # 自动计算每行字符数
    try:
        # 测试字符宽度
        test_char = "中"  # 中文字符
        char_width = temp_draw.textlength(test_char, font=content_font) if hasattr(temp_draw, 'textlength') else 24
        chars_per_line = (width - 120) // int(char_width)  # 左右各留60像素边距
    except:
        chars_per_line = 25  # 默认值

    print(f"  - 每行字符数: {chars_per_line}")

    # 分割文本
    pages = split_text_into_pages(content, chars_per_line, lines_per_page)

    # 限制最大页数
    if max_pages and len(pages) > max_pages:
        print(f"警告: 文本过长，将被截断到{max_pages}页")
        pages = pages[:max_pages]

    total_pages = len(pages)

    print(f"\n生成进度:")

    # 生成每一页
    image_paths = []

    # 修改文件名格式，加入当前时间信息
    from datetime import datetime
    now = datetime.now()
    output_dir = os.path.dirname(output_file_path_prefix)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, page_lines in enumerate(pages, 1):

        file_name = f"{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}_{i:02d}.png"
        # 优化路径拼接逻辑，处理output_file_path_prefix末尾是否有斜杠的情况
        if output_file_path_prefix.endswith('/') or output_file_path_prefix.endswith('\\'):
            output_path = f"{output_file_path_prefix}{file_name}"
        else:
            # 判断使用哪种路径分隔符
            if '/' in output_file_path_prefix or '\\' not in output_file_path_prefix:
                separator = '/'
            else:
                separator = '\\'
            output_path = f"{output_file_path_prefix}{separator}{file_name}"

        # 创建图片
        image = Image.new('RGB', (width, height), 'black')
        draw = ImageDraw.Draw(image)

        # 绘制标题
        try:
            left, top, right, bottom = draw.textbbox((0, 0), title, font=title_font)
            title_width = right - left
        except:
            title_width = len(title) * 36 // 2

        title_x = 60  # (width - title_width) // 2
        draw.text((title_x, 50), title, font=title_font, fill='white')

        # 绘制分割线
        # draw.line([(50, 120), (width - 50, 120)], fill='lightgray', width=2)

        # 绘制内容
        margin = 60
        y_position = 150

        for line in page_lines:
            draw.text((margin, y_position), line, font=content_font, fill='white')
            y_position += line_height

        # 绘制页码
        page_text = f"第 {i} / {total_pages} 页"
        page_font = get_chinese_font(18)

        try:
            left, top, right, bottom = draw.textbbox((0, 0), page_text, font=page_font)
            page_width = right - left
        except:
            page_width = len(page_text) * 18

        page_x = width - page_width - 60
        page_y = height - 50
        draw.text((page_x, page_y), page_text, font=page_font, fill='lightgray')

        # 添加边框
        # draw.rectangle([(30, 30), (width - 30, height - 30)], outline='darkgray', width=2)

        # 保存图片
        image.save(output_path)
        image_paths.append(output_path)
        print(f"  ✓ 已生成第 {i}/{total_pages} 页: {output_path}")

    print(f"\n完成! 共生成 {total_pages} 页图片")
    return image_paths


class Text2ImageTool(BaseTool):

    def __init__(self):
        super().__init__()
        self.description = "文字转图片"

    def _get_parameters(self) -> Dict[str, ToolParameter]:
        return {
            "title": ToolParameter(
                type="string",
                description="标题"
            ),
            "content": ToolParameter(
                type="string",
                description="正文"
            ),
            "image_type": ToolParameter(
                type="string",
                description="图片类型",
                enum=["BlackBgWhiteText"],
                default="BlackBgWhiteText"
            )
        }

    def _get_required_parameters(self) -> List[str]:
        return ["title", "content", "image_type"]

    async def execute(self, title: str, content: str, image_type: str) -> Dict[str, Any]:
        image_paths = []
        try:
            if image_type == "BlackBgWhiteText":
                image_paths = create_smart_multi_page_story(title, content)
            else:
                # raise ValueError(f"未知操作: {image_type}")
                image_paths = create_smart_multi_page_story(title, content)
                print(f"未知操作:{image_type}, 默认使用: BlackBgWhiteText")

            return {
                "type": "text",
                "text": f"生成图片成功，共生成: {len(image_paths)} 张",
                "result": f"{image_paths}"
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"生成图片失败: {str(e)}"
            }
