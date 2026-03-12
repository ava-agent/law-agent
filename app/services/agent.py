import json
import re
import uuid
from typing import Dict, List, Optional, Generator

from app.models.enums import ConversationPhase, CASE_TYPE_LABELS, DOCUMENT_TYPE_LABELS
from app.models.schemas import SessionState
from app.prompts.consultation import ALL_REQUIRED_FIELDS, FIELD_LABELS, MIN_FIELDS_FOR_SUMMARY
from app.prompts.system_prompts import (
    MAIN_SYSTEM_PROMPT,
    GREETING_PROMPT,
    SITUATION_ANALYSIS_PROMPT,
    CASE_SUMMARY_PROMPT,
    GUIDANCE_PROMPT,
    DOCUMENT_PREPARATION_PROMPT,
    FOLLOW_UP_PROMPT,
)
from app.services.knowledge import KnowledgeBase
from app.services.llm import LLMService


class AgentService:
    def __init__(self, llm: LLMService, knowledge: KnowledgeBase):
        self.llm = llm
        self.knowledge = knowledge
        self.sessions: Dict[str, SessionState] = {}

    def create_session(self, case_type: Optional[str] = None):
        session_id = uuid.uuid4().hex[:12]
        session = SessionState(session_id)
        if case_type:
            session.case_info["case_type"] = case_type
            session.case_type = case_type
            session.collected_fields.add("case_type")

        self.sessions[session_id] = session

        welcome = self._generate_welcome(session)
        session.messages.append({"role": "assistant", "content": welcome})
        session.phase = ConversationPhase.SITUATION_ANALYSIS
        return session_id, welcome

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self.sessions.get(session_id)

    def _generate_welcome(self, session: SessionState) -> str:
        messages = [
            {"role": "system", "content": MAIN_SYSTEM_PROMPT},
            {"role": "user", "content": GREETING_PROMPT},
        ]
        return self.llm.chat(messages)

    def process_message(self, session_id: str, user_msg: str) -> Generator:
        session = self.sessions.get(session_id)
        if not session:
            yield {"type": "text", "content": "会话不存在，请刷新页面重新开始。"}
            return

        session.messages.append({"role": "user", "content": user_msg})

        if session.phase == ConversationPhase.SITUATION_ANALYSIS:
            yield from self._handle_situation_analysis(session, user_msg)
        elif session.phase == ConversationPhase.CASE_SUMMARY:
            yield from self._handle_case_summary(session, user_msg)
        elif session.phase == ConversationPhase.GUIDANCE:
            yield from self._handle_guidance(session, user_msg)
        elif session.phase == ConversationPhase.DOCUMENT_PREPARATION:
            yield from self._handle_document_preparation(session, user_msg)
        elif session.phase == ConversationPhase.FOLLOW_UP:
            yield from self._handle_followup(session, user_msg)
        else:
            yield from self._handle_situation_analysis(session, user_msg)

    def _handle_situation_analysis(self, session: SessionState, user_msg: str):
        collected_info = json.dumps(session.case_info, ensure_ascii=False, indent=2) if session.case_info else "{}"
        missing_fields = [f for f in ALL_REQUIRED_FIELDS if f not in session.collected_fields]
        missing = [f"- {FIELD_LABELS.get(f, f)}" for f in missing_fields]
        missing_text = "\n".join(missing) if missing else "全部已收集"

        phase_prompt = SITUATION_ANALYSIS_PROMPT.format(
            collected_info=collected_info,
            missing_fields=missing_text,
        )

        messages = self._build_messages(session, phase_prompt)
        full_response = ""

        for chunk in self.llm.stream_chat(messages):
            full_response += chunk

        cleaned, extracted = self._extract_json_block(full_response)
        if extracted:
            session.case_info.update(extracted)
            session.collected_fields.update(extracted.keys())
            if "case_type" in extracted:
                session.case_type = extracted["case_type"]

        session.messages.append({"role": "assistant", "content": cleaned})

        yield {"type": "text", "content": cleaned}

        if session.case_info:
            yield {
                "type": "case_info",
                "content": json.dumps(self._format_case_info(session), ensure_ascii=False),
            }

        if MIN_FIELDS_FOR_SUMMARY.issubset(session.collected_fields):
            session.phase = ConversationPhase.CASE_SUMMARY
            yield from self._auto_generate_summary(session)

    def _auto_generate_summary(self, session: SessionState):
        case_info_text = json.dumps(session.case_info, ensure_ascii=False, indent=2)
        relevant_laws = self.knowledge.get_law_text_for_prompt(session.case_type)

        phase_prompt = CASE_SUMMARY_PROMPT.format(
            case_info=case_info_text,
            relevant_laws=relevant_laws,
        )

        messages = [
            {"role": "system", "content": MAIN_SYSTEM_PROMPT},
            {"role": "user", "content": phase_prompt},
        ]

        full_response = ""
        for chunk in self.llm.stream_chat(messages):
            full_response += chunk

        session.messages.append({"role": "assistant", "content": full_response})
        yield {"type": "text", "content": "\n\n---\n\n" + full_response}

    def _handle_case_summary(self, session: SessionState, user_msg: str):
        lower_msg = user_msg.lower()
        confirmed = any(w in lower_msg for w in ["确认", "对的", "没问题", "正确", "是的", "ok", "好的", "没错", "对"])
        need_modify = any(w in lower_msg for w in ["修改", "不对", "错了", "不是", "改一下", "有误"])

        if need_modify:
            session.phase = ConversationPhase.SITUATION_ANALYSIS
            messages = self._build_messages(session, "用户表示信息有误需要修改，请友好地询问哪些信息需要更正。")
            full_response = ""
            for chunk in self.llm.stream_chat(messages):
                full_response += chunk
            session.messages.append({"role": "assistant", "content": full_response})
            yield {"type": "text", "content": full_response}
        elif confirmed:
            session.phase = ConversationPhase.GUIDANCE
            yield from self._generate_guidance(session)
        else:
            messages = self._build_messages(session, "请确认案件信息是否正确，或告知需要修改的部分。")
            full_response = ""
            for chunk in self.llm.stream_chat(messages):
                full_response += chunk
            session.messages.append({"role": "assistant", "content": full_response})
            yield {"type": "text", "content": full_response}

    def _generate_guidance(self, session: SessionState):
        case_info_text = json.dumps(session.case_info, ensure_ascii=False, indent=2)
        relevant_laws = self.knowledge.get_law_text_for_prompt(session.case_type)
        platforms = self.knowledge.get_platforms(session.case_type)
        platforms_text = json.dumps(platforms, ensure_ascii=False, indent=2)

        phase_prompt = GUIDANCE_PROMPT.format(
            case_info=case_info_text,
            relevant_laws=relevant_laws,
            recommended_platforms=platforms_text,
        )

        messages = [
            {"role": "system", "content": MAIN_SYSTEM_PROMPT},
            {"role": "user", "content": phase_prompt},
        ]

        full_response = ""
        for chunk in self.llm.stream_chat(messages):
            full_response += chunk

        session.messages.append({"role": "assistant", "content": full_response})
        yield {"type": "text", "content": full_response}

        actions = [
            {"label": "生成投诉书", "action": "generate_doc", "doc_type": "complaint_letter"},
            {"label": "生成举报信", "action": "generate_doc", "doc_type": "report_letter"},
            {"label": "生成协商函", "action": "generate_doc", "doc_type": "demand_letter"},
            {"label": "生成民事起诉状", "action": "generate_doc", "doc_type": "civil_lawsuit"},
            {"label": "查看投诉平台详细流程", "action": "show_platforms"},
        ]
        yield {"type": "action", "content": json.dumps(actions, ensure_ascii=False)}

    def _handle_guidance(self, session: SessionState, user_msg: str):
        doc_keywords = {
            "投诉书": "complaint_letter",
            "举报信": "report_letter",
            "协商函": "demand_letter",
            "律师函": "demand_letter",
            "起诉状": "civil_lawsuit",
            "起诉书": "civil_lawsuit",
            "证据清单": "evidence_checklist",
            "索赔函": "claim_letter",
        }

        for keyword, doc_type in doc_keywords.items():
            if keyword in user_msg:
                session.phase = ConversationPhase.DOCUMENT_PREPARATION
                session.case_info["_pending_doc_type"] = doc_type
                yield from self._handle_document_preparation(session, user_msg)
                return

        if any(w in user_msg for w in ["平台", "投诉渠道", "去哪", "怎么投诉", "流程"]):
            yield from self._show_platform_details(session)
            return

        messages = self._build_messages(
            session,
            FOLLOW_UP_PROMPT.format(
                case_info=json.dumps(session.case_info, ensure_ascii=False),
                generated_docs=", ".join(session.generated_documents) if session.generated_documents else "暂无",
            ),
        )
        full_response = ""
        for chunk in self.llm.stream_chat(messages):
            full_response += chunk
        session.messages.append({"role": "assistant", "content": full_response})
        yield {"type": "text", "content": full_response}

    def _handle_document_preparation(self, session: SessionState, user_msg: str):
        doc_type = session.case_info.get("_pending_doc_type", "complaint_letter")
        doc_label = DOCUMENT_TYPE_LABELS.get(doc_type, doc_type)

        from app.prompts.document_prompts import DOC_REQUIRED_FIELDS, DOC_FIELD_LABELS

        required = DOC_REQUIRED_FIELDS.get(doc_type, [])
        missing = [f for f in required if f not in session.case_info]
        missing_labels = [f"{DOC_FIELD_LABELS.get(f, f)}" for f in missing]

        if missing_labels:
            missing_text = "、".join(missing_labels)
            phase_prompt = DOCUMENT_PREPARATION_PROMPT.format(
                doc_type_label=doc_label,
                case_info=json.dumps(session.case_info, ensure_ascii=False, indent=2),
                missing_doc_fields=missing_text,
            )
            messages = self._build_messages(session, phase_prompt)
            full_response = ""
            for chunk in self.llm.stream_chat(messages):
                full_response += chunk

            cleaned, extracted = self._extract_json_block(full_response)
            if extracted:
                session.case_info.update(extracted)
                session.collected_fields.update(extracted.keys())

            session.messages.append({"role": "assistant", "content": cleaned})
            yield {"type": "text", "content": cleaned}
        else:
            yield {
                "type": "text",
                "content": f"信息已收集完毕，正在为您生成【{doc_label}】...",
            }
            yield {
                "type": "action",
                "content": json.dumps(
                    [{"label": f"生成{doc_label}", "action": "generate_doc", "doc_type": doc_type, "ready": True}],
                    ensure_ascii=False,
                ),
            }
            session.phase = ConversationPhase.FOLLOW_UP

    def _handle_followup(self, session: SessionState, user_msg: str):
        doc_keywords = {
            "投诉书": "complaint_letter",
            "举报信": "report_letter",
            "协商函": "demand_letter",
            "起诉状": "civil_lawsuit",
            "证据清单": "evidence_checklist",
            "索赔函": "claim_letter",
        }
        for keyword, doc_type in doc_keywords.items():
            if keyword in user_msg:
                session.case_info["_pending_doc_type"] = doc_type
                session.phase = ConversationPhase.DOCUMENT_PREPARATION
                yield from self._handle_document_preparation(session, user_msg)
                return

        messages = self._build_messages(
            session,
            FOLLOW_UP_PROMPT.format(
                case_info=json.dumps(session.case_info, ensure_ascii=False),
                generated_docs=", ".join(session.generated_documents) if session.generated_documents else "暂无",
            ),
        )
        full_response = ""
        for chunk in self.llm.stream_chat(messages):
            full_response += chunk
        session.messages.append({"role": "assistant", "content": full_response})
        yield {"type": "text", "content": full_response}

    def _show_platform_details(self, session: SessionState):
        processes = self.knowledge.get_all_processes(session.case_type)
        if not processes:
            yield {"type": "text", "content": "暂无相关投诉流程信息。"}
            return

        parts = ["以下是推荐的投诉平台和详细流程：\n"]
        for p in processes:
            parts.append(f"## {p.get('full_name', p.get('platform', ''))}")
            if p.get("url"):
                parts.append(f"网址：{p['url']}")
            if p.get("channels"):
                parts.append(f"渠道：{'、'.join(p['channels'])}")
            parts.append("")
            for step in p.get("steps", []):
                parts.append(f"**步骤{step['step']}：{step['title']}**")
                parts.append(step["description"])
                if step.get("tips"):
                    for tip in step["tips"]:
                        parts.append(f"  - {tip}")
                parts.append("")
            if p.get("processing_time"):
                parts.append(f"处理时限：{p['processing_time']}")
            if p.get("cost"):
                parts.append(f"费用：{p['cost']}")
            parts.append("\n---\n")

        result = "\n".join(parts)
        session.messages.append({"role": "assistant", "content": result})
        yield {"type": "text", "content": result}

    def _build_messages(self, session: SessionState, phase_prompt: str) -> List[Dict]:
        messages = [{"role": "system", "content": MAIN_SYSTEM_PROMPT + "\n\n" + phase_prompt}]
        recent = session.messages[-10:]
        messages.extend(recent)
        return messages

    def _extract_json_block(self, text: str):
        pattern = r"<!--EXTRACTED_JSON\s*(.*?)\s*-->"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            cleaned = re.sub(pattern, "", text, flags=re.DOTALL).strip()
            try:
                data = json.loads(json_str)
                return cleaned, data
            except json.JSONDecodeError:
                return cleaned, {}
        return text, {}

    def _format_case_info(self, session: SessionState) -> Dict:
        info = {}
        for key, value in session.case_info.items():
            if key.startswith("_"):
                continue
            label = FIELD_LABELS.get(key)
            if label:
                if key == "case_type":
                    value = CASE_TYPE_LABELS.get(value, value)
                info[label] = value
            else:
                info[key] = value
        return info
