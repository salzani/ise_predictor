import yaml
import torch
from typing import Optional, List, Any 
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM
from transformers import BitsAndBytesConfig

class GemmaLLM(LLM):
    model_path: str
    model: Optional[Any] = None
    tokenizer: Optional[Any] = None
    bnb_config: Optional[Any] = None
    temperature: float = 0.2
    max_new_tokens: int = 500

    def __init__(self, model_path: str, **kwargs):
        super().__init__(model_path=model_path, **kwargs)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.bnb_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=self.bnb_config,
            device_map="auto"
        )

    @property
    def _llm_type(self) -> str:
        return "gemma-esg"

    def _call(self, prompt: str, stop: Optional[List[str]]=None, **kwargs) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        current_max_tokens = kwargs.get('max_new_tokens', self.max_new_tokens)
        current_temp = kwargs.get('temperature', self.temperature)

        default_do_sample = True if current_temp > 0.0 else False
        current_do_sample = kwargs.get('do_sample', default_do_sample)

        output = self.model.generate(
            **inputs,
            max_new_tokens=current_max_tokens, 
            temperature=current_temp,           
            do_sample=current_do_sample,       
            pad_token_id=self.tokenizer.eos_token_id,
        )

        generated_tokens = output[0][inputs["input_ids"].shape[-1]:]
        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True
        )

        return response.strip()

class ISEOrchestrator:

    def __init__(self, model_path: str, prompts_path: str):
        self.llm = GemmaLLM(model_path=model_path)
        self.prompts = self._load_prompts(prompts_path)

        guard_template_str = self.prompts["guard_prompt"] + "\n\nQuestion: {question}\nAnswer:"
        self.guard_prompt_template = PromptTemplate(
            input_variables=["question"],
            template=guard_template_str
        )

        self.main_prompt_template = PromptTemplate(
            input_variables=["question"],
            template=(
                "{system_prompt}\n\n" 
                "### User Question:\n"
                "{question}\n\n"
                "### Assistant Response:\n"
            ),
            partial_variables={"system_prompt": self.prompts["system_prompt"]}
        )

    def _load_prompts(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_response(self, question: str) -> str:
        guard_chain = self.guard_prompt_template | self.llm

        guard_output = guard_chain.invoke(
            {"question": question},
            config={
                "max_new_tokens": 5,
                "temperature": 0.0
            }
        ).strip().upper()
        if "BLOCKED" in guard_output:
            return self.prompts["rejection_message"]

        main_chain = self.main_prompt_template | self.llm
  
        response = main_chain.invoke(
            {"question": question}
        )
        
        return response
