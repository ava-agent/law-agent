from typing import Dict, List

from app.services.knowledge import KnowledgeBase


class PlatformRecommender:
    def __init__(self, knowledge: KnowledgeBase):
        self.knowledge = knowledge

    def recommend(self, case_info: Dict) -> List[Dict]:
        case_type = case_info.get("case_type")
        amount_str = str(case_info.get("purchase_amount", "0"))
        amount = self._parse_amount(amount_str)
        is_online = self._is_online(case_info.get("purchase_channel", ""))
        previous_comm = str(case_info.get("previous_communication", ""))
        merchant_unresponsive = any(
            w in previous_comm
            for w in ["不理", "拒绝", "没回", "不回复", "不处理", "不管"]
        )

        platforms = self.knowledge.get_platforms(case_type)
        scored = []

        for p in platforms:
            score = 0
            reasons = []
            conditions = p.get("priority_conditions", {})

            if conditions.get("always_recommend"):
                score += 50
                reasons.append("消费纠纷首选渠道")

            boost_conditions = conditions.get("boost_when", [])
            for cond in boost_conditions:
                if cond == "is_online_purchase" and is_online:
                    score += 20
                    reasons.append("适合线上购物纠纷")
                elif cond == "large_brand" and is_online:
                    score += 10
                    reasons.append("舆论曝光对品牌有压力")
                elif cond == "amount_over_5000" and amount > 5000:
                    score += 15
                    reasons.append("金额较大，适合走法律途径")
                elif cond == "other_channels_failed" and merchant_unresponsive:
                    score += 10
                    reasons.append("其他渠道未解决时的最终手段")
                elif cond == "clear_evidence":
                    score += 5
                elif cond == "unsure_which_department":
                    score += 10
                    reasons.append("可转接多个政府部门")
                elif cond == "willing_to_mediate":
                    score += 10
                    reasons.append("免费调解服务")

            if not reasons:
                reasons = p.get("strengths", [])[:2]

            suitability = "alternative"
            if score >= 40:
                suitability = "highly_recommended"
            elif score >= 20:
                suitability = "recommended"

            process = self.knowledge.get_process(
                f"complaint_{p['id']}" if p["id"] != "court" else "court_filing"
            )
            steps_summary = ""
            if process:
                steps = process.get("steps", [])[:3]
                steps_summary = " → ".join(s["title"] for s in steps)
                if process.get("processing_time"):
                    steps_summary += f"（{process['processing_time']}）"

            scored.append(
                {
                    "name": p.get("name", ""),
                    "full_name": p.get("full_name", ""),
                    "url": p.get("url", ""),
                    "reason": "；".join(reasons),
                    "suitability": suitability,
                    "steps_summary": steps_summary,
                    "score": score,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        for item in scored:
            del item["score"]

        return scored

    def _parse_amount(self, amount_str: str) -> float:
        amount_str = amount_str.replace("元", "").replace("¥", "").replace(",", "").replace("，", "").strip()
        try:
            return float(amount_str)
        except (ValueError, TypeError):
            return 0.0

    def _is_online(self, channel: str) -> bool:
        online_keywords = [
            "淘宝", "天猫", "京东", "拼多多", "抖音", "快手",
            "线上", "网上", "网购", "电商", "app", "小程序",
            "美团", "饿了么", "闲鱼",
        ]
        return any(k in channel.lower() for k in online_keywords)
