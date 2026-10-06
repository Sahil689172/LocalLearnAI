import torch
import soundfile as sf

from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL_PATH = r"C:\Users\hp\.cache\huggingface\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca"

device = "cpu"

print("Loading model...")

model = ParlerTTSForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    local_files_only=True
).to(device)

model.eval()

print("Model loaded.")

# IMPORTANT:
# Official Indic-Parler arrangement:
# tokenizer = actual speech text
# description_tokenizer = speaker/style description

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

description_tokenizer = AutoTokenizer.from_pretrained(
    model.config.text_encoder._name_or_path
)

print("Speech tokenizer:", type(tokenizer).__name__)
print("Description tokenizer:", type(description_tokenizer).__name__)

prompt = "Binary search is an efficient algorithm for finding an element in a sorted array."

description = (
    "A male speaker speaks clearly in an Indian English accent "
    "at a moderate speed with a calm educational tone. "
    "The recording is very clear with no background noise."
)

# Actual speech text
prompt_inputs = tokenizer(
    prompt,
    return_tensors="pt",
    padding=True
)

prompt_input_ids = prompt_inputs.input_ids.to(device)
prompt_attention_mask = prompt_inputs.attention_mask.to(device)

# Speaker/style description
description_inputs = description_tokenizer(
    description,
    return_tensors="pt",
    padding=True
)

input_ids = description_inputs.input_ids.to(device)
attention_mask = description_inputs.attention_mask.to(device)

print("Generating...")

with torch.no_grad():
    generation = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        prompt_input_ids=prompt_input_ids,
        prompt_attention_mask=prompt_attention_mask,
    )

audio = generation.cpu().numpy().squeeze()

sf.write(
    "indic_parler_official_test.wav",
    audio,
    model.config.sampling_rate
)

print("DONE")
print("Sampling rate:", model.config.sampling_rate)
print("Audio samples:", len(audio))
print("Saved: indic_parler_official_test.wav")