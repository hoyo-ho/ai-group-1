# -*- coding: utf-8 -*-
"""
Stack Overflow Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class StackoverflowExtractor(BaseExtractor):
    """Stack Overflow question/answer extractor"""
    
    priority = 75
    supported_domains = [
        "stackoverflow.com",
        "stackexchange.com",
        "askubuntu.com",
        "superuser.com",
        "serverfault.com"
    ]
    
    # Minimum content length threshold
    MIN_CONTENT_LENGTH = 100
    
    def _clean_content(self, content: str) -> str:
        """Clean content by removing excessive newlines and carriage returns"""
        if not content:
            return ""
        # First: normalize line endings - convert \r\n and \r to \n
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # Second: replace multiple consecutive newlines with single newline
        content = re.sub(r'\n+', '\n', content)
        # Strip leading/trailing whitespace
        return content.strip()
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if it's a question page (/questions/ or /q/)
        if "/questions/" in url or "/q/" in url:
            return self._extract_question(url, soup, html)
        elif "/users/" in url:
            return self._extract_user(url, soup)
        elif "/tags/" in url:
            return self._extract_tag(url, soup)
        else:
            return self._extract_generic(url, soup, html)
    
    def _extract_question(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract question page"""
        # Extract title
        title = self._extract_title(soup)
        
        # Extract question content (will be cleaned later)
        content = self._extract_question_content(soup)
        content = self._clean_content(content)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publish time
        publish_time = self._extract_publish_time(soup)
        
        # Extract votes
        votes = self._extract_votes(soup)
        
        # Extract answers
        answers = self._extract_answers(soup)
        
        # Extract tags
        tags = self._extract_tags(soup)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "votes": votes,
            "answers": answers,
            "tags": tags,
            "meta": meta,
            "type": "question"
        }
    
    def _extract_user(self, url: str, soup: BeautifulSoup) -> Dict:
        """Extract user profile"""
        # Title (username)
        title = self._extract_title(soup)
        
        # Extract user info
        meta = self._extract_user_meta(soup)
        
        # About
        about = ""
        about_div = soup.find("div", class_=re.compile(r"about|profile"))
        if about_div:
            about = about_div.get_text(separator="\n", strip=True)
        
        return {
            "url": url,
            "title": title,
            "content": about[:1000],
            "meta": meta,
            "type": "user"
        }
    
    def _extract_tag(self, url: str, soup: BeautifulSoup) -> Dict:
        """Extract tag page"""
        title = self._extract_title(soup)
        
        # Description
        desc = ""
        desc_elem = soup.find("div", class_=re.compile(r"description|tag-excerpt"))
        if desc_elem:
            desc = desc_elem.get_text(separator="\n", strip=True)
        
        # Try meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and not desc:
            desc = meta_desc.get("content", "")
        
        return {
            "url": url,
            "title": title,
            "content": desc,
            "type": "tag"
        }
    
    def _extract_generic(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract generic page"""
        title = self._extract_title(soup)
        
        return {
            "url": url,
            "title": title,
            "content": "",
            "type": "generic"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try title tag
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove " - Stack Overflow" suffix
            return title_text.replace(" - Stack Overflow", "").replace(" - Stack Exchange", "").strip()
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_question_content(self, soup: BeautifulSoup) -> str:
        # Try post question layout
        question_div = soup.find("div", class_=re.compile(r"question|post-layout"))
        if question_div:
            # Try s-post-summary
            summary = question_div.find("div", class_=re.compile(r"s-post-summary--body"))
            if summary:
                return summary.get_text(separator="\n", strip=True)
            
            # Try post-text
            post_text = question_div.find("div", class_=re.compile(r"post-text|postcell"))
            if post_text:
                return post_text.get_text(separator="\n", strip=True)
        
        # Try direct post-text
        post_text = soup.find("div", class_=re.compile(r"post-text"))
        if post_text:
            return post_text.get_text(separator="\n", strip=True)
        
        # Try content class
        content_div = soup.find("div", class_=re.compile(r"content|question-body"))
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        
        # Try meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            return meta_desc.get("content", "")
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Try user card
        user_card = soup.find("div", class_=re.compile(r"user-card|post-signature"))
        if user_card:
            name_link = user_card.find("a", class_=re.compile(r"user-name"))
            if name_link:
                return name_link.get_text(strip=True)
            
            # Try span user-name
            name_span = user_card.find("span", class_=re.compile(r"user-name"))
            if name_span:
                return name_span.get_text(strip=True)
        
        # Try link with user class
        user_link = soup.find("a", class_=re.compile(r"user"))
        if user_link:
            return user_link.get_text(strip=True)
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        # Try time element
        time_elem = soup.find("time")
        if time_elem:
            return time_elem.get("datetime", "") or time_elem.get_text(strip=True)
        
        # Try span with date class
        date_span = soup.find("span", class_=re.compile(r"date|time|publish"))
        if date_span:
            return date_span.get_text(strip=True)
        
        # Try relative time
        rel_time = soup.find("span", class_=re.compile(r"relativetime"))
        if rel_time:
            return rel_time.get("title", "") or rel_time.get_text(strip=True)
        
        return ""
    
    def _extract_votes(self, soup: BeautifulSoup) -> Dict:
        votes = {}
        
        # Try vote count
        vote_div = soup.find("div", class_=re.compile(r"vote-count"))
        if vote_div:
            votes["count"] = vote_div.get_text(strip=True)
        
        # Try score
        score_span = soup.find("span", class_=re.compile(r"score|vote-score"))
        if score_span:
            votes["score"] = score_span.get_text(strip=True)
        
        # Try to find vote up/down counts
        for span in soup.find_all("span", class_=re.compile(r"count")):
            if "up" in span.get("title", "").lower():
                votes["upvotes"] = span.get_text(strip=True)
            elif "down" in span.get("title", "").lower():
                votes["downvotes"] = span.get_text(strip=True)
        
        return votes
    
    def _extract_answers(self, soup: BeautifulSoup) -> List[Dict]:
        answers = []
        
        # Find answer items
        answer_divs = soup.find_all("div", id=re.compile(r"answer-"))
        
        for div in answer_divs[:10]:  # Top 10 answers
            answer = {}
            
            # Extract answer ID
            answer_id = div.get("id", "")
            if answer_id:
                answer["id"] = answer_id.replace("answer-", "")
            
            # Content with cleaning
            content_div = div.find("div", class_=re.compile(r"post-text|answer-body"))
            if content_div:
                raw_content = content_div.get_text(separator="\n", strip=True)[:1000]
                answer["content"] = self._clean_content(raw_content)
            
            # Author
            sig = div.find("div", class_=re.compile(r"user-card|post-signature"))
            if sig:
                name_link = sig.find("a", class_=re.compile(r"user-name"))
                if name_link:
                    answer["author"] = name_link.get_text(strip=True)
            
            # Votes
            vote_div = div.find("div", class_=re.compile(r"vote-count"))
            if vote_div:
                answer["votes"] = vote_div.get_text(strip=True)
            
            # Is accepted?
            accepted = div.find("div", class_=re.compile(r"accepted-answer"))
            if accepted or div.find("span", class_=re.compile(r"checkmark")):
                answer["accepted"] = True
            
            if answer.get("content"):
                answers.append(answer)
        
        return answers
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        tags = []
        
        # Try post tags
        tag_div = soup.find("div", class_=re.compile(r"post-taglist|tags"))
        if tag_div:
            for a in tag_div.find_all("a"):
                tag_text = a.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        
        return list(set(tags))
    
    def _extract_meta(self, soup: BeautifulSoup) -> Dict:
        meta = {}
        
        # Description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            meta["description"] = desc.get("content", "")
        
        # Try view count
        views = soup.find("div", class_=re.compile(r"views"))
        if views:
            meta["views"] = views.get_text(strip=True)
        
        # Last activity
        activity = soup.find("span", class_=re.compile(r"activity|modified"))
        if activity:
            meta["last_activity"] = activity.get_text(strip=True)
        
        return meta
    
    def _extract_user_meta(self, soup: BeautifulSoup) -> Dict:
        meta = {}
        
        # Reputation
        rep = soup.find("span", class_=re.compile(r"reputation|score"))
        if rep:
            meta["reputation"] = rep.get_text(strip=True)
        
        # Location
        location = soup.find("span", class_=re.compile(r"location"))
        if location:
            meta["location"] = location.get_text(strip=True)
        
        # Member since
        since = soup.find("span", class_=re.compile(r"member|joined"))
        if since:
            meta["member_since"] = since.get_text(strip=True)
        
        return meta
