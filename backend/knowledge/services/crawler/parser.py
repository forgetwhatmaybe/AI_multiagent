
from typing import Dict, Any
from utils.text_utils import TextUtils
class HtmlParser:
    def parse_html_to_markdown(self,knowledge_no:int,html_data:Dict[str,Any]) -> str:
        """
        Parses HTML content and converts it to Markdown format.
        :param knowledge_no: The knowledge number associated with the HTML content.
        :param html_data: The HTML content to be parsed.
        :return: The converted Markdown content.
        """
        # Implement the logic to convert HTML to Markdown here
        # You can use libraries like BeautifulSoup or markdownify for this purpose
        
        if not html_data or 'content' not in html_data:
            raise ValueError("Invalid HTML data provided for parsing.")
        
        
        items=[f'# 知识库 {knowledge_no}\n']
        
        html_data_title = html_data.get('title','暂无标题')
        
        items.append(f'## 标题\n{html_data_title.strip()}\n')
        
        html_data_digest = html_data.get('digest','暂无摘要')
        if html_data_digest and html_data_digest.strip() != '暂无摘要':
            items.append(f'## 问题描述\n{html_data_digest.strip()}\n')
        
        
        first_topic_name = html_data.get('firstTopicName','暂无一级主题')
        sub_topic_name = html_data.get('subTopicName','暂无二级主题')
        question_category_name = html_data.get('questionCategoryName','暂无问题分类')
        
        categories = []
        
        if first_topic_name and first_topic_name.strip() != '暂无一级主题':
            categories.append(f'主分类\n{first_topic_name.strip()}')
            
        if sub_topic_name and sub_topic_name.strip() != '暂无二级主题':
            categories.append(f'子分类\n{sub_topic_name.strip()}')
        
        if question_category_name and question_category_name.strip() != '暂无问题分类':
            categories.append(f'问题分类\n{question_category_name.strip()}')
            
            
        if categories:
            items.append('## 分类\n' + '\n'.join(categories) + '\n')
            
            
        html_data_key_words = html_data.get('keywords','暂无关键词')
        key_words_list = []
        if html_data_key_words and html_data_key_words.strip() != '暂无关键词':
            for key_word in html_data_key_words.split(","):
                if isinstance(key_word, str) and key_word.strip():
                    key_words_list.append(key_word.strip())
        if key_words_list:
            items.append(f'## 关键词\n{", ".join(key_words_list)}\n')
            
            
        medata_data=[]
        html_data_create_time = html_data.get('createTime','暂无创建时间')
        html_data_version_no = html_data.get('versionNo','暂无版本号')
        
        if html_data_create_time and html_data_create_time.strip() != '暂无创建时间':
            medata_data.append(f'创建时间: {html_data_create_time.strip()}')
        if html_data_version_no and html_data_version_no.strip() != '暂无版本号':
            medata_data.append(f'版本: {html_data_version_no.strip()}')
        if medata_data:
            items.append('## 元数据\n' + '\n'.join(medata_data) + '\n')
            
        html_data_content = html_data.get('content','暂无内容')
        if html_data_content and html_data_content.strip() != '暂无内容':
            
            md_content = TextUtils.html_to_markdown(html_data_content)
            
            items.append(f"## 解决方案\n{md_content}\n")
            
        items.append(f'<!-- 文档主题: {html_data_title.strip()}(知识库编号: {knowledge_no}) -->\n')
            
        return '\n'.join(items)