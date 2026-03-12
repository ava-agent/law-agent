import json
import os
from typing import Dict, List, Optional


class KnowledgeBase:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.laws: Dict[str, Dict] = {}
        self.processes: Dict[str, Dict] = {}
        self.platforms: List[Dict] = []
        self.doc_templates: Dict[str, Dict] = {}
        self._load_all(knowledge_dir)

    def _load_all(self, base_dir: str):
        self._load_dir(os.path.join(base_dir, "laws"), self.laws)
        self._load_dir(os.path.join(base_dir, "processes"), self.processes)
        self._load_dir(os.path.join(base_dir, "templates"), self.doc_templates)

        platforms_file = os.path.join(base_dir, "platforms", "platforms.json")
        if os.path.exists(platforms_file):
            with open(platforms_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.platforms = data.get("platforms", [])

    def _load_dir(self, dir_path: str, target: Dict):
        if not os.path.isdir(dir_path):
            return
        for filename in os.listdir(dir_path):
            if filename.endswith(".json"):
                key = filename.replace(".json", "")
                with open(os.path.join(dir_path, filename), "r", encoding="utf-8") as f:
                    target[key] = json.load(f)

    def get_relevant_laws(self, case_type: Optional[str]) -> List[Dict]:
        if not case_type:
            return []
        results = []
        for law_data in self.laws.values():
            relevant_articles = [
                article
                for article in law_data.get("articles", [])
                if case_type in article.get("applicable_cases", [])
            ]
            if relevant_articles:
                results.append(
                    {
                        "law_name": law_data.get("law_name", ""),
                        "articles": relevant_articles,
                    }
                )
        return results

    def get_process(self, process_name: str) -> Optional[Dict]:
        return self.processes.get(process_name)

    def get_all_processes(self, case_type: Optional[str]) -> List[Dict]:
        if not case_type:
            return list(self.processes.values())
        return [
            p
            for p in self.processes.values()
            if case_type in p.get("applicable_cases", [])
        ]

    def get_platforms(self, case_type: Optional[str]) -> List[Dict]:
        if not case_type:
            return self.platforms
        return [
            p
            for p in self.platforms
            if case_type in p.get("scope", [])
        ]

    def get_doc_template(self, doc_type: str) -> Optional[Dict]:
        return self.doc_templates.get(doc_type)

    def get_law_text_for_prompt(self, case_type: Optional[str]) -> str:
        laws = self.get_relevant_laws(case_type)
        if not laws:
            return "暂无相关法条信息。"
        parts = []
        for law in laws:
            parts.append(f"【{law['law_name']}】")
            for a in law["articles"]:
                parts.append(f"  {a['number']} {a.get('title', '')}: {a['content']}")
        return "\n".join(parts)
