import requests
from bs4 import BeautifulSoup
import sys

class V2exCLI:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.topics = []  # 存储主题列表
        
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
                    # 显示主题
                    print(f'[{index}] 标题: {title} {reply_text}')
                    print(f'    链接: {url}')
                    print('-' * 80)
                    
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
                print('\n' + '=' * 80)
                print(f"标题: {topic['title']}")
                print('-' * 80)
                print(topic_content.text.strip())
                print('=' * 80 + '\n')
            else:
                print('未找到主题内容')
                
        except requests.RequestException as e:
            print(f'获取主题详情失败: {e}')
        except Exception as e:
            print(f'解析主题详情失败: {e}')

    def run(self):
        print('正在获取 V2EX 主题列表...\n')
        if not self.get_topics():
            return
        
        while True:
            try:
                user_input = input('\n输入主题编号查看详情，输入 / 进入命令模式，输入 q 退出: ').strip()
                
                if user_input.lower() == 'q':
                    break
                elif user_input == '/':
                    command = input('命令模式 > ').strip()
                    if command.lower() == 'refresh':
                        print('\n刷新主题列表...\n')
                        self.get_topics()
                    elif command.lower() == 'help':
                        print('\n可用命令:')
                        print('refresh - 刷新主题列表')
                        print('help    - 显示帮助信息')
                        print('exit    - 退出命令模式\n')
                    elif command.lower() == 'exit':
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
                break
            except Exception as e:
                print(f'发生错误: {e}')

if __name__ == '__main__':
    cli = V2exCLI()
    cli.run() 