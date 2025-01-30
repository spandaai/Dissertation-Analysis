# Fine-Tuning with Unsloth - Dissertation Analysis

## 1. Overview
This directory contains scripts and datasets for fine-tuning large language models using Unsloth. The fine-tuning process leverages LoRA (Low-Rank Adaptation) to enable efficient training with minimal computational resources.

## 2. Directory Structure
```
train/
│── training-scripts/   # Contains fine-tuning scripts
│── training-dataset/   # Contains datasets used for training
│── README.md           # Documentation on usage
```

## 3. Installation & Setup

### 3.1 System Requirements
- Python 3.9+
- PyTorch 2.0+
- CUDA 11.8+ (For GPU users)
- BitsAndBytes for 4-bit quantization

### 3.2 Installing Dependencies
Run the following command to install Unsloth and its dependencies:
```sh
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```
For GPU users:
```sh
pip install "unsloth[cu118] @ git+https://github.com/unslothai/unsloth.git"
```
For CPU-only users:
```sh
pip install "unsloth[huggingface] @ git+https://github.com/unslothai/unsloth.git"
```

## 4. Running the Fine-Tuning Script

### 4.1 Command-line Arguments
To start fine-tuning, navigate to `training-scripts/` and run:
```sh
python unsloth-cli.py \
    --model_name "unsloth/llama-3.2-1b-Instruct" \
    --max_seq_length 512 \
    --dtype fp16 \
    --load_in_4bit \
    --r 32 \
    --lora_alpha 32 \
    --lora_dropout 0.1 \
    --bias "none" \
    --use_gradient_checkpointing True \
    --random_state 3407 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --warmup_steps 10 \
    --max_steps 500 \
    --learning_rate 2e-5 \
    --logging_steps 5 \
    --optim adamw_8bit \
    --lr_scheduler_type "linear" \
    --weight_decay 0.01 \
    --seed 3407 \
    --output_dir "outputs" \
    --report_to "tensorboard" \
    --save_model \
    --save_path "model"
```

## 5. Running on Different Environments

### 5.1 Running on a Single GPU
```sh
CUDA_VISIBLE_DEVICES=0 python unsloth-cli.py --model_name ...
```

### 5.2 Running on Multiple GPUs
Using PyTorch distributed training:
```sh
torchrun --nproc_per_node=2 unsloth-cli.py --model_name ...
```

### 5.3 Running on CPU-Only Mode
For CPU-only training (not recommended for large models):
```sh
python unsloth-cli.py --model_name ... --dtype bf16
```

## 6. Troubleshooting

- **Out of Memory (OOM) Errors?** Reduce `--per_device_train_batch_size`, enable `--use_gradient_checkpointing`, or use `--load_in_4bit`.
- **Dataset Issues?** Ensure dataset format is correct (JSON, CSV, Hugging Face dataset).
- **Slow Training?** Optimize using `--optim adamw_8bit` and ensure GPU acceleration is enabled.


