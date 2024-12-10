import requests
from bs4 import BeautifulSoup
import sys
import os
import json
from datetime import datetime
import re

# 根据操作系统选择合适的模块
if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix/Mac
    import tty
    import termios

class V2exCLI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.topics = []  # 存储主题列表
        self.cache_file = 'v2ex_cache.json'  # 缓存文件路径
        self.load_cache()  # 初始化时加载缓存
        self.page_size = 12  # 每页显示的主题数量
        self.current_page = 1  # 当前页码
        
    def save_cache(self):
        """保存主题列表到缓存文件"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'topics': self.topics
        }
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存缓存失败: {e}', file=sys.stderr)

    def load_cache(self):
        """从缓存文件加载主题列表"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.topics = cache_data['topics']
                    print('已从缓存加载主题列表')
                    return True
        except Exception as e:
            print(f'读取缓存失败: {e}', file=sys.stderr)
        return False

    def clear_screen(self):
        """清空屏幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_topics(self):
        """显示主题列表"""
        self.clear_screen()
        print('\n主题列表:\n')
        
        # 计算当前页的起始和结束索引
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_topics = self.topics[start_idx:end_idx]
        
        # 显示当前页的主题
        for idx, topic in enumerate(page_topics, start_idx + 1):
            print(f'[{idx}] 标题: {topic["title"]} {topic["reply"]}')
            print(f'    链接: {topic["url"]}')
            print('-' * 80)
            
        # 显示分页信息
        total_pages = (len(self.topics) + self.page_size - 1) // self.page_size
        print(f'\n当前第 {self.current_page}/{total_pages} 页')
        
    def get_topics(self):
        try:
            # 获取网页内容
            response = requests.get('https://www.v2ex.com/?tab=all', headers=self.headers)
            response.raise_for_status()
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有class为"cell item"的div
            items = soup.find_all('div', class_='cell item')
            
            # 清空之前的主题列表
            self.topics = []
            
            # 遍历并提取信息
            for index, item in enumerate(items, 1):
                topic_link = item.find('a', class_='topic-link')
                reply_count = item.find('a', class_=['count_livid', 'count_orange'])
                reply_text = f'[{reply_count.text} 回复]' if reply_count else '[0 回复]'
                
                if topic_link:
                    title = topic_link.text.strip()
                    url = 'https://www.v2ex.com' + topic_link['href']
                    # 存储主题信息
                    self.topics.append({'title': title, 'url': url, 'reply': reply_text})
            
            # 保存到缓存
            self.save_cache()
            
            # 显示主题列表
            self.display_topics()
                    
        except requests.RequestException as e:
            print(f'获取数据失败: {e}', file=sys.stderr)
            return False
        except Exception as e:
            print(f'解析数据失败: {e}', file=sys.stderr)
            return False
        return True

    def get_topic_detail(self, topic_index):
        try:
            # 检查索引是否有效
            if not (1 <= topic_index <= len(self.topics)):
                print('无效的主题编号!')
                return
            
            topic = self.topics[topic_index - 1]
            response = requests.get(topic['url'], headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取主题内容
            topic_content = soup.find('div', class_='topic_content')
            
            # 获取评论列表
            comments = soup.find_all('div', class_='cell', id=lambda x: x and x.startswith('r_'))
            
            # 构建两层评论结构
            top_comments = []  # 顶层评论
            reply_comments = {}  # 回复的评论，key 是被回复评论的编号
            
            # 分类评论
            for comment in comments:
                no_elem = comment.find('span', class_='no')
                comment_no = no_elem.text if no_elem else '0'
                
                username_elem = comment.find('strong')
                username = username_elem.text if username_elem else '匿名用户'
                
                time_elem = comment.find('span', class_='ago')
                comment_time = time_elem.text if time_elem else '未知时间'
                
                content_elem = comment.find('div', class_='reply_content')
                content = content_elem.text.strip() if content_elem else '无内容'
                
                comment_data = {
                    'no': comment_no,
                    'username': username,
                    'time': comment_time,
                    'content': content
                }
                
                # 检查是否是回复
                if content_elem and '@' in content:
                    # 查找被回复的评论
                    for prev_comment in comments:
                        prev_username = prev_comment.find('strong').text if prev_comment.find('strong') else ''
                        if f'@{prev_username}' in content:
                            prev_no = prev_comment.find('span', class_='no').text
                            if prev_no not in reply_comments:
                                reply_comments[prev_no] = []
                            reply_comments[prev_no].append(comment_data)
                            break
                    else:
                        top_comments.append(comment_data)
                else:
                    top_comments.append(comment_data)
            
            if topic_content:
                self.clear_screen()
                
                # 显示主题内容
                print('\n' + '=' * 160)
                print(f"标题: {topic['title']}")
                print(f"\n{topic_content.text.strip()}\n")
                print('=' * 160)
                
                # 显示评论
                total_comments = len(comments)
                if total_comments > 0:
                    print(f"\n评论列表 (共 {total_comments} 条评论):\n")
                    
                    # 显示顶层评论及其回复
                    for comment in top_comments:
                        # 显示顶层评论
                        print('-' * 80)  # 顶层评论之间的分隔线
                        print(f"#{comment['no']} | 评论者: {comment['username']} | {comment['time']}")
                        content_lines = comment['content'].split('\n')
                        for line in content_lines:
                            print(f"  {line}")
                        
                        # 显示回复（如果有）
                        if comment['no'] in reply_comments:
                            for reply in reply_comments[comment['no']]:
                                # 回复缩进 8 个空格
                                print('     |')
                                print('     |->')
                                print(f"        #{reply['no']} | 评论者: {reply['username']} | {reply['time']}")
                                content_lines = reply['content'].split('\n')
                                for line in content_lines:
                                    print(f"          {line}")
                        print('\n')
                    
                else:
                    print('\n暂无评论')
                    print('=' * 80)

                # 等待用户输入 b 返回
                while True:
                    user_input = input('\n输入 b 返回主题列表: ').strip().lower()
                    if user_input == 'b':
                        self.display_topics()
                        return
            else:
                print('未找到主题内容')
                
        except requests.RequestException as e:
            print(f'获取主题详情失败: {e}')
        except Exception as e:
            print(f'解析主题详情失败: {e}')

    def handle_user_input(self, char):
        """处理用户输入的命令或主题编号"""
        # 处理单字符命令（无需回车的命令）
        if char in ['>', '<']:
            if char == '>':
                # 下一页
                total_pages = (len(self.topics) + self.page_size - 1) // self.page_size
                if self.current_page < total_pages:
                    self.current_page += 1
                    self.display_topics()
                else:
                    print('已经是最后一页了~')
                return True
            elif char == '<':
                # 上一页
                if self.current_page > 1:
                    self.current_page -= 1
                    self.display_topics()
                else:
                    print('已经是第一页了~')
                return True

        # 处理需要回车的命令
        command = ''
        while char != '\r' and char != '\n':
            if char == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            elif char == '\x7f' or char == '\x08':  # Delete or Backspace
                if command:  # 只在有字符时才处理删除
                    command = command[:-1]
                    # 在终端中模拟删除效果
                    sys.stdout.write('\b \b')  # 退格，写空格，再退格
                    sys.stdout.flush()
            else:
                sys.stdout.write(char)
                sys.stdout.flush()
                command += char
            char = self.get_char()
        print()  # 换行
        
        command = command.lower().strip()
        
        # 命令处理
        if command == 'h':
            self.clear_screen()
            print('\n可用命令:')
            print('数字    - 输入主题编号查看详情')
            print('h       - 显示帮助信息')
            print('b       - 返回主题列表')
            print('>       - 查看下一页（无需回车）')
            print('<       - 查看上一页（无需回车）')
            print('r       - 刷新页面')
            print('q       - 退出程序\n')
            print('--------------------------------')
            print('b       - 返回主题列表\n')
        elif command == 'b':
            self.display_topics()
        elif command == 'r':
            self.clear_screen()
            print('\n刷新主题列表...\n')
            if os.path.exists(self.cache_file):
                try:
                    os.remove(self.cache_file)
                    print('已删除缓存文件')
                except Exception as e:
                    print(f'删除缓存文件失败: {e}', file=sys.stderr)
            self.topics.clear()
            self.get_topics()
        elif command == 'q':
            self.clear_screen()
            return False
        elif command:  # 确保命令不为空
            try:
                topic_index = int(command)
                self.get_topic_detail(topic_index)
            except ValueError:
                print('请输入有效的主题编号或命令！输入 h 查看可用命令')
        
        return True

    def get_char(self):
        """获取单个字符输入，如果raw模式失败则回退到基础输入模式"""
        if os.name == 'nt':  # Windows
            return msvcrt.getch().decode('utf-8')
        else:  # Unix/Mac
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            # 尝试使用raw模式
            try:
                tty.setraw(sys.stdin.fileno())
            except (termios.error, tty.error):
                print("\n注意: 高级输入模式不可用，自动切换到基础输入模式(需要回车)")
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return sys.stdin.read(1)


    def run(self):
        self.clear_screen()
        print('正在加载 V2EX 主题列表...\n')
        
        if not self.topics:
            if not self.get_topics():
                return
        else:
            self.display_topics()
        
        print('\n提示：使用 < 和 > 键进行翻页，输入 h + 回车 查看帮助\n')
        
        while True:
            try:
                char = self.get_char()
                if not self.handle_user_input(char):
                    break
                    
            except KeyboardInterrupt:
                self.clear_screen()
                break
            except Exception as e:
                print(f'发生错误: {e}')

if __name__ == '__main__':
    cli = V2exCLI()
    cli.run() 