import json
import logging
import os
import re
from typing import Optional
import requests
from dotenv import load_dotenv

from src.domain.entities.decision import ActionDecision, ActionType
from src.domain.ports.llm import ILLMClient

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)


class CloudLLMClient(ILLMClient):
    """Client for OpenRouter Cloud LLM (e.g. deepseek/deepseek-v4-flash-0731)

    Enforces structured JSON schema decisions and natural, human-like Vietnamese persona.
    """

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "deepseek/deepseek-v4-flash-0731"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_sec: float = 15.0,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENROUTER_BASE_URL", self.DEFAULT_BASE_URL)
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self.timeout_sec = timeout_sec


    def is_configured(self) -> bool:
        """Returns True if API key is present."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def evaluate_and_generate(
        self,
        context_text: str,
        action_type: ActionType,
        thread_context: Optional[str] = None,
    ) -> ActionDecision:
        """Evaluates post/comment context and generates response via OpenRouter LLM."""
        if not self.is_configured():
            logger.warning("OpenRouter API key is not configured. Returning default SKIP decision.")
            return ActionDecision(
                should_act=False,
                reason="No OpenRouter API key provided",
                action_type=ActionType.SKIP,
            )

        if not context_text or not context_text.strip():
            return ActionDecision(
                should_act=False,
                reason="Context text is empty",
                action_type=ActionType.SKIP,
            )

        system_prompt = (
            "Bạn là một người dùng mạng xã hội Facebook tại Việt Nam (thân thiện, hóm hỉnh, tự nhiên, lịch sự).\n"
            "BẮT BUỘC SỬ DỤNG 100% TIẾNG VIỆT TỰ NHIÊN TRONG MỌI TRƯỜNG HỢP. "
            "TUYỆT ĐỐI KHÔNG DÙNG CHỮ HÁN/TIẾNG TRUNG HOẶC TIẾNG ANH (kể cả với địa danh như Hồ Tây, Hà Nội).\n"
            "Nhiệm vụ của bạn là đọc nội dung bài viết hoặc bình luận, sau đó:\n"
            "1. Quyết định xem có nên tương tác không (`should_act`: true hoặc false):\n"
            "   - KHÔNG tương tác (`false`) nếu nội dung là: cờ bạc, cá cược, lô đề, quảng cáo bán hàng/khóa học lộ liễu, "
            "lừa đảo, kéo nhóm kiếm tiền, chính trị nhạy cảm/tiêu cực gay gắt, hoặc chữ vô nghĩa/không đủ ngữ cảnh.\n"
            "   - NÊN tương tác (`true`) nếu nội dung chia sẻ trải nghiệm đời sống thường ngày, công nghệ, thảo luận thú vị, hài hước, tích cực.\n"
            "2. Nếu tương tác (`should_act: true`):\n"
            "   - Viết nội dung bằng tiếng Việt ngắn gọn (1 đến 2 câu), tự nhiên như người thật đang lướt mạng xã hội.\n"
            "   - TUYỆT ĐỐI TRÁNH các câu sáo rỗng khuôn mẫu của bot như 'Cảm ơn tác giả đã chia sẻ bài viết rất bổ ích', "
            "'Bài viết rất hay và ý nghĩa'. Hãy bình luận dí dỏm, đồng cảm hoặc nhận xét cụ thể vào chi tiết trong bài.\n"
            "3. BẮT BUỘC chỉ trả về định dạng JSON thuần túy (không kèm markdown ngoài JSON):\n"
            "{\n"
            '  "should_act": true,\n'
            '  "reason": "lý do ngắn gọn bằng tiếng Việt",\n'
            '  "text": "nội dung bình luận hoặc phản hồi bằng tiếng Việt"\n'
            "}"
        )

        if action_type == ActionType.COMMENT:
            user_prompt = (
                "[HÀNH ĐỘNG: BÌNH LUẬN BÀI VIẾT FEED (FLOW A)]\n"
                f"Nội dung bài viết:\n\"\"\"\n{context_text.strip()}\n\"\"\"\n"
                "Hãy đánh giá và trả về quyết định JSON hoàn toàn bằng tiếng Việt."
            )
        else:
            user_prompt = (
                "[HÀNH ĐỘNG: TRẢ LỜI BÌNH LUẬN THREAD (FLOW B)]\n"
                f"Ngữ cảnh bài viết / bình luận gốc:\n\"\"\"\n{(thread_context or 'Không rõ').strip()}\n\"\"\"\n"
                f"Bình luận cần trả lời:\n\"\"\"\n{context_text.strip()}\n\"\"\"\n"
                "Hãy đánh giá và trả về quyết định JSON hoàn toàn bằng tiếng Việt."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/anhluong447/Nelboz",
            "X-Title": "Facebook AutoBot",
        }

        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
            "reasoning": {"effort": "none"},
        }

        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_sec,
            )

            if resp.status_code != 200:
                logger.error("OpenRouter API returned error %d: %s", resp.status_code, resp.text[:200])
                return ActionDecision(
                    should_act=False,
                    reason=f"OpenRouter HTTP error {resp.status_code}",
                    action_type=ActionType.SKIP,
                )

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ActionDecision(
                    should_act=False,
                    reason="Empty choices from OpenRouter",
                    action_type=ActionType.SKIP,
                )

            msg = choices[0].get("message", {})
            raw_content = msg.get("content") or ""
            if not raw_content and msg.get("reasoning_content"):
                raw_content = msg.get("reasoning_content") or ""

            return self._parse_json_decision(raw_content.strip(), action_type)

        except requests.Timeout:
            logger.warning("OpenRouter API timed out after %.1f seconds.", self.timeout_sec)
            return ActionDecision(
                should_act=False,
                reason="OpenRouter API timeout",
                action_type=ActionType.SKIP,
            )
        except Exception as e:
            logger.error("Error communicating with OpenRouter: %s", e)
            return ActionDecision(
                should_act=False,
                reason=f"OpenRouter client exception: {str(e)}",
                action_type=ActionType.SKIP,
            )

    def _parse_json_decision(self, raw_content: str, target_action: ActionType) -> ActionDecision:
        """Extracts and validates JSON decision from model response with multi-layer fallback."""
        clean_text = raw_content.strip()

        # Remove markdown code block if present
        if "```" in clean_text:
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r"```\s*$", "", clean_text, flags=re.MULTILINE).strip()

        # First attempt: direct json.loads
        try:
            parsed = json.loads(clean_text)
            should_act = bool(parsed.get("should_act", False))
            reason = str(parsed.get("reason", "No reason provided"))
            text = str(parsed.get("text", "")).strip()

            final_action = target_action if should_act else ActionType.SKIP
            return ActionDecision(
                should_act=should_act,
                text=text if should_act else "",
                action_type=final_action,
                reason=reason,
                confidence=0.95,
            )
        except json.JSONDecodeError:
            pass

        # Second attempt: find first JSON block
        match = re.search(r"(\{[^{}]*\"should_act\"[^{}]*\})", clean_text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                should_act = bool(parsed.get("should_act", False))
                reason = str(parsed.get("reason", "No reason provided"))
                text = str(parsed.get("text", "")).strip()

                final_action = target_action if should_act else ActionType.SKIP
                return ActionDecision(
                    should_act=should_act,
                    text=text if should_act else "",
                    action_type=final_action,
                    reason=reason,
                    confidence=0.95,
                )
            except json.JSONDecodeError:
                pass

        # Third attempt: resilient regex extraction for truncated or slightly malformed JSON
        should_act_match = re.search(r'"should_act"\s*:\s*(true|false)', clean_text, re.IGNORECASE)
        if should_act_match:
            should_act = should_act_match.group(1).lower() == "true"
            reason_match = re.search(r'"reason"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', clean_text)
            text_match = re.search(r'"text"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', clean_text)

            reason = reason_match.group(1) if reason_match else "Extracted via regex fallback"
            text = text_match.group(1) if text_match else ""

            final_action = target_action if should_act else ActionType.SKIP
            return ActionDecision(
                should_act=should_act,
                text=text if should_act else "",
                action_type=final_action,
                reason=reason,
                confidence=0.90,
            )

        logger.warning("Failed to parse LLM JSON decision: (Raw: %s)", raw_content[:200])
        return ActionDecision(
            should_act=False,
            reason="Malformed JSON response from LLM",
            action_type=ActionType.SKIP,
        )
