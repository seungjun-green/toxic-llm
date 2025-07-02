from transformers import StoppingCriteria, StoppingCriteriaList
import torch

class StopOnKeywords(StoppingCriteria):
    def __init__(self, tokenizer, keywords, initial_input_len):
        self.tokenizer = tokenizer
        self.keywords = keywords
        self.initial_input_len = initial_input_len  # Save the prompt length

    def __call__(self, input_ids, scores, **kwargs):
        # Only decode the *new* tokens (excluding the original prompt)
        generated_ids = input_ids[0][self.initial_input_len:]
        generated_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        return any(keyword in generated_text for keyword in self.keywords)
    
    
def sample_gen(tokenizer, rl_model, prompt, max_length, no_repeat_ngram_size):
    with torch.no_grad():
        encoding = tokenizer(prompt, max_length=max_length, truncation=True, padding="max_length", return_tensors="pt").to('cuda')
        input_length = encoding.input_ids.shape[1]

        stopping_criteria = StoppingCriteriaList([
            StopOnKeywords(tokenizer, keywords=["User:", "Assistant:"], initial_input_len=input_length)
        ])

        generated_ids = rl_model.generate(
            input_ids=encoding.input_ids,
            attention_mask=encoding.attention_mask,
            max_new_tokens=max_length,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
            stopping_criteria=stopping_criteria,
            no_repeat_ngram_size=no_repeat_ngram_size,
            use_cache=False
        )
        
        generated_only_ids = generated_ids[:, input_length:]
        generated_texts = tokenizer.batch_decode(generated_only_ids, skip_special_tokens=True)
    
    print("\n" + "-" * 50)
    print(f"{prompt}{generated_texts[0]}")
    print("-" * 50)