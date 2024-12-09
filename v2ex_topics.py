import requests
from bs4 import BeautifulSoup
import sys
import os

class V2exCLI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.topics = []  # 存储主题列表
        
    def clear_screen(self):
        """清空屏幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_topics(self):
        """显示主题列表"""
        self.clear_screen()
        print('\n主题列表:\n')
        for index, topic in enumerate(self.topics, 1):
            print(f'[{index}] 标题: {topic["title"]} {topic["reply"]}')
            print(f'    链接: {topic["url"]}')
            print('-' * 80)
    
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
            if topic_content:
                self.clear_screen()  # 清屏后显示详情
                print('\n' + '=' * 80)
                print(f"标题: {topic['title']}")
                print('-' * 80)
                print(topic_content.text.strip())
                print('=' * 80)
                
                # 等待用户输入 b 返回
                while True:
                    user_input = input('\n输入 b 返回主题列表: ').strip().lower()
                    if user_input == 'b':
                        # 返回主题列表时重新显示
                        self.display_topics()
                        return
            else:
                print('未找到主题内容')
                
        except requests.RequestException as e:
            print(f'获取主题详情失败: {e}')
        except Exception as e:
            print(f'解析主题详情失败: {e}')

    def run(self):
        self.clear_screen()  # 启动时清屏
        print('正在获取 V2EX 主题列表...\n')
        if not self.get_topics():
            return
        
        while True:
            try:
                user_input = input('\n输入主题编号查看详情，输入 / 进入命令模式，输入 q 退出: ').strip()
                
                if user_input.lower() == 'q':
                    self.clear_screen()  # 退出时清屏
                    break
                elif user_input == '/':
                    command = input('命令模式 > ').strip()
                    if command.lower() == 'refresh':
                        self.clear_screen()  # 刷新前清屏
                        print('\n刷新主题列表...\n')
                        self.get_topics()
                    elif command.lower() == 'help':
                        self.clear_screen()  # 显示帮助前清屏
                        print('\n可用命令:')
                        print('refresh - 刷新主题列表')
                        print('help    - 显示帮助信息')
                        print('exit    - 退出命令模式\n')
                    elif command.lower() == 'exit':
                        self.display_topics()  # 退出命令模式时重新显示主题列表
                        continue
                    else:
                        print('未知命令，输入 help 查看可用命令')
                else:
                    try:
                        topic_index = int(user_input)
                        self.get_topic_detail(topic_index)
                    except ValueError:
                        print('请输入有效的主题编号!')
                        
            except KeyboardInterrupt:
                self.clear_screen()  # Ctrl+C 退出时清屏
                break
            except Exception as e:
                print(f'发生错误: {e}')

if __name__ == '__main__':
    cli = V2exCLI()
    cli.run() 