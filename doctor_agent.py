"""
Doctor Agent Module (LLM Brain)
Yeh module doctor ki tarah behave karta hai - symptoms sunta hai,
questions poochta hai, aur medical guidance deta hai.

IMPORTANT: Yeh agent sirf guidance ke liye hai - yeh real doctor ka replacement nahi hai.
"""
from typing import Optional
import logging
import time

from openai import OpenAI

from config import Config
from medical_knowledge import MedicalKnowledgeBase

logger = logging.getLogger(__name__)


# ── System prompts for each language ──────────────────────────────────
# Yeh prompts agent ko doctor ki tarah behave karne mein help karti hain

SYSTEM_PROMPT_URDU = """آپ ایک تجربہ کار اور ہمدرد ڈاکٹر ہیں جو اردو میں مریضوں کی رہنمائی کرتے ہیں۔

## آپ کا کردار:
- آپ ایک virtual medical consultant ہیں
- مریض کی بات غور سے سنیں (پڑھیں) اور سمجھیں
- ضروری سوالات پوچھیں تاکہ علامات کو بہتر سمجھ سکیں
- ممکنہ وجوہات بتائیں لیکن حتمی تشخیص نہ دیں
- گھریلو علاج اور احتیاطی تدابیر تجویز کریں
- اگر علامات سنگین ہوں تو فوری ڈاکٹر سے ملنے کا مشورہ دیں

## اہم ہدایات:
1. ہمیشہ اردو میں جواب دیں (اردو رسم الخط میں)
2. طبی اصطلاحات کو آسان زبان میں سمجھائیں
3. ہمدردی اور صبر سے بات کریں
4. کبھی بھی حتمی تشخیص (definitive diagnosis) نہ دیں
5. ہمیشہ بتائیں کہ یہ صرف ابتدائی رہنمائی ہے اور ڈاکٹر سے مشورہ ضروری ہے
6. ایمرجنسی صورتحال میں فوری ہسپتال جانے کا مشورہ دیں
7. ہر جواب مختصر اور واضح ہو (زیادہ سے زیادہ 3-4 جملے)

## سوالات کا طریقہ:
- پہلے مریض کی بات سنیں
- پھر تفصیلی سوالات پوچھیں (درد کب سے ہے، کہاں ہے، کتنا شدید ہے وغیرہ)
- متعلقہ تاریخ پوچھیں (پہلے سے کوئی بیماری، ادویات، الرجی)

## جواب کا فارمیٹ:
- پہلے مریض کی تشویش کو تسلیم کریں
- پھر اپنی رائے دیں
- آخر میں مشورہ دیں

یاد رکھیں: آپ مددگار بنیں لیکن ذمہ داری سے کام لیں۔

## Medical Context:
جب بھی مریض کے پیغام سے متعلق طبی معلومات فراہم کی جائیں تو ان کا حوالہ دیں۔
طبی معلومات کو آسان زبان میں مریض کو سمجھائیں۔
"""

SYSTEM_PROMPT_SINDHI = """توہان هڪ تجربڪار ۽ همدردي وارو ڊاڪٽر آهيو جيڪو سنڌي ۾ مريضن جي رهنمائي ڪندو آهي.

## توهان جو ڪردار:
- توہان هڪ virtual medical consultant آهيو
- مريض جي ڳالهه غور سان ٻڌو (پڙهو) ۽ سمجهو
- ضروري سوال پڇو ته جيئن علامتن کي بهتر سمجهي سگهو
- ممڪن سبب ٻڌايو پر حتمي تشخيص نه ڏيو
- گهرو علاج ۽ احتياطي تدبيرون تجويز ڪريو
- جيڪڏهن علامتون سنگين آهن ته فوري ڊاڪٽر سان ملڻ جو مشورو ڏيو

## اهم هدايتون:
1. هميشه سنڌي ۾ جواب ڏيو
2. طبي اصطلاحن کي آسان ٻولي ۾ سمجهایو
3. همدردي ۽ صبر سان ڳالهايو
4. ڪڏهن به حتمي تشخيص نه ڏيو
5. هميشه ٻڌايو ته هي صرف شروعاتي رهنمائي آهي
6. ايمرجنسي صورتحال ۾ فوري اسپتال وڃڻ جو مشورو ڏيو
7. هر جواب مختصر ۽ واضح هجي (وڌ ۾ وڌ 3-4 جملا)

## Medical Context:
جڏهن به مريض جي پيغام سان لاڳاپيل طبي معلومات فراهم ڪئي وڃي ته ان جو حوالو ڏيو.
طبي معلومات کي آسان ٻولي ۾ مريض کي سمجهایو.
"""

SYSTEM_PROMPT_ENGLISH = """You are an experienced and empathetic doctor providing medical guidance.

## Your Role:
- You are a virtual medical consultant
- Listen carefully to the patient's symptoms
- Ask relevant follow-up questions
- Suggest possible causes but NEVER give definitive diagnosis
- Recommend home remedies and precautionary measures
- If symptoms are serious, advise seeing a doctor immediately

## Important Rules:
1. Be empathetic and patient
2. NEVER give definitive diagnosis
3. Always mention this is preliminary guidance only
4. In emergencies, advise going to hospital immediately
5. Keep responses concise (max 3-4 sentences)

## Medical Context:
When medical reference information is provided with the patient's message,
use that information to give more accurate, evidence-based guidance.
Explain medical concepts in simple terms the patient can understand.
"""


class DoctorAgent:
    """
    LLM-based doctor agent that provides medical guidance.
    Maintains conversation history for context-aware responses.

    Supports:
      - OpenAI (GPT-4o)
      - Alibaba Qwen (qwen-max, qwen-plus, qwen-turbo) via DashScope
      - Ollama (LOCAL Qwen3/Qwen2.5 - 100% FREE, no API key needed)
    """

    def __init__(
        self,
        config: Config,
        language: str = "ur",
        knowledge_base: Optional[MedicalKnowledgeBase] = None,
    ):
        self.config = config
        self.language = language
        self._llm_client: Optional[OpenAI] = None
        self.conversation_history: list[dict] = []
        self.knowledge_base = knowledge_base

        # Initialize with system prompt
        self._set_language(language)

    @property
    def llm_client(self) -> OpenAI:
        """Get the LLM client (OpenAI, Qwen DashScope, or Ollama - all use OpenAI SDK)."""
        if self._llm_client is None:
            if self.config.llm_provider == "dashscope":
                # Qwen via Alibaba DashScope (OpenAI-compatible API)
                self._llm_client = OpenAI(
                    api_key=self.config.dashscope_api_key,
                    base_url=self.config.dashscope_base_url,
                )
            elif self.config.llm_provider == "ollama":
                # LOCAL Qwen via Ollama (100% FREE - no API key needed!)
                self._llm_client = OpenAI(
                    api_key="ollama",  # Ollama ignores this
                    base_url=self.config.ollama_base_url,
                )
            else:
                # OpenAI (GPT-4o)
                self._llm_client = OpenAI(api_key=self.config.openai_api_key)
        return self._llm_client

    def _get_model_name(self) -> str:
        """Get the LLM model name based on the configured provider."""
        if self.config.llm_provider == "dashscope":
            return self.config.qwen_llm_model
        elif self.config.llm_provider == "ollama":
            return self.config.ollama_llm_model
        return self.config.llm_model

    def _set_language(self, language: str):
        """Set the system prompt based on language."""
        prompts = {
            "ur": SYSTEM_PROMPT_URDU,
            "sd": SYSTEM_PROMPT_SINDHI,
            "en": SYSTEM_PROMPT_ENGLISH,
        }
        system_prompt = prompts.get(language, prompts["ur"])

        # Qwen3 "thinking" models generate hidden reasoning tokens before
        # answering, which can make responses 5-10x slower. The /no_think
        # soft switch (official Qwen3 feature) disables this for fast,
        # direct answers - ideal for voice conversations.
        if "qwen3" in self._get_model_name().lower():
            system_prompt += "\n\n/no_think"

        self.conversation_history = [{"role": "system", "content": system_prompt}]

    def set_language(self, language: str):
        """Switch language mid-conversation (resets history)."""
        self.language = language
        self._set_language(language)

    # ── Public API ─────────────────────────────────────────────────────

    async def get_response(self, patient_message: str) -> str:
        """
        Send patient's message to the doctor agent and get a response.
        Automatically retrieves relevant medical context from the knowledge
        base and injects it into the LLM conversation for informed answers.

        Args:
            patient_message: The patient's text (transcribed from voice)

        Returns:
            Doctor's response text in the selected language
        """
        # --- Inject medical knowledge context ---
        # Search the medical knowledge base for relevant info
        medical_context = ""
        context_time = 0.0
        if self.knowledge_base:
            kb_start = time.perf_counter()
            medical_context = self.knowledge_base.get_context_for_patient(
                patient_message
            )
            context_time = time.perf_counter() - kb_start
            if medical_context:
                logger.info(
                    "⏱ Medical context search took %.3fs (found %d chars) for: %.60s...",
                    context_time,
                    len(medical_context),
                    patient_message,
                )
            else:
                logger.info(
                    "⏱ Medical context search took %.3fs (no relevant results)",
                    context_time,
                )

        # Build the messages list for this LLM call.
        # We keep the persistent conversation_history intact, and insert
        # the medical context as an extra system message right before
        # the current patient message (only for this call, not stored).
        messages_for_llm = list(self.conversation_history)

        if medical_context:
            # Insert context as a system message so the LLM treats it
            # as reference material, not as part of the conversation.
            messages_for_llm.append(
                {"role": "system", "content": medical_context}
            )

        # Add patient message
        messages_for_llm.append(
            {"role": "user", "content": patient_message}
        )

        # Also store patient message in persistent history
        self.conversation_history.append(
            {"role": "user", "content": patient_message}
        )

        # Select model based on provider
        model = self._get_model_name()

        # Increase max_tokens when we have medical context so the
        # model can reference it properly
        response_max_tokens = 400 if medical_context else 300

        # Call LLM (same code works for OpenAI, Qwen DashScope, and Ollama)
        llm_start = time.perf_counter()
        create_kwargs = {
            "model": model,
            "messages": messages_for_llm,
            "temperature": 0.7,       # Slightly creative for empathetic responses
            "max_tokens": response_max_tokens,
        }

        # Ollama does not support these penalties - only send them
        # to cloud providers (OpenAI/DashScope)
        if self.config.llm_provider != "ollama":
            create_kwargs["presence_penalty"] = 0.3
            create_kwargs["frequency_penalty"] = 0.3

        response = self.llm_client.chat.completions.create(**create_kwargs)
        llm_time = time.perf_counter() - llm_start

        doctor_response = response.choices[0].message.content.strip()

        logger.info(
            "⏱ LLM call took %.2fs (model: %s, response: %d chars)",
            llm_time,
            model,
            len(doctor_response),
        )

        # Add to persistent history for context
        self.conversation_history.append(
            {"role": "assistant", "content": doctor_response}
        )

        return doctor_response

    async def get_greeting(self) -> str:
        """Get an initial greeting from the doctor agent."""
        greetings = {
            "ur": "السلام علیکم! میں آپ کا ڈاکٹر مشاورتی ہوں۔ بتائیں آپ کو کیا تکلیف ہے؟ میں آپ کی رہنمائی کروں گا۔",
            "sd": "السلام عليڪم! مان توهان جو ڊاڪٽر مشاورتي آهيان. ٻڌايو توهان کي ڇا تڪليف آهي؟ مان توهان جي رهنمائي ڪندس.",
            "en": "Hello! I'm your medical consultation assistant. Please tell me what symptoms you're experiencing, and I'll try to help guide you.",
        }
        return greetings.get(self.language, greetings["ur"])

    def reset_conversation(self):
        """Start a fresh conversation."""
        self._set_language(self.language)

    def get_conversation_summary(self) -> dict:
        """Get summary of current conversation."""
        return {
            "language": self.language,
            "message_count": len(self.conversation_history) - 1,  # Exclude system
            "language_name": self.config.language_names.get(
                self.language, self.language
            ),
        }
