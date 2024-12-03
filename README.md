<h2 align="center"> <a href="">🎁Template Matters🎁</a></h2>

## 🔔News
  
 **🔥[2024-12-04]: Code released!**

## What's TemplateMatters ?
We propose a programmatic instruction template generator, aimed at enhancing the understanding of the critical role instruction templates play in large Multimodal Language Model (MLM) evaluation and training.

## Install
You can easily download the repo and set up the environments via:
```
git clone https://github.com/shijian2001/TemplateMatters
cd ./TemplateMatters

pip install -r requirements.txt
```

## Instruction Template Generator
We provide three easy-to-use interfaces: `QuestionTemplateGenerator`, `ChoiceTemplateGenerator`, `VQATemplateGenerator`. You can easily use them to generate diverse instruction templates as follows：
```python
from tm.template_generator import VQATemplateGenerator, generate_templates_set

print(VQATemplateGenerator().num_all_potential_templates)
# 3939857075

## Randomly generate template
print(VQATemplateGenerator().generate())
# The question about the provided picture asks for an response: {question}
# Available options are listed below and you should pick the best answer:
# {choices}

## Generate a specified number of non-repeating templates
vqa_templates_set = generate_templates_set(VQATemplateGenerator, num_templates=1000)
print(len(vqa_templates_set))
# 1000
```

## Evaluation

### Dataset
We support the following datasets: 
- `SingleImageQADataset`: BLINK, MMBench, SeedBench, Task-Me-Anything, MMMU

We offer a unified interface to load and process VQA datasets in a standard format. You can load a VQA dataset easily as follows:
```python
from tm.qa_datasets import SingleImageQADataset

tma = SingleImageQADataset("tma-subset").get_dataset()
tma
# Dataset({
#     features: ['id', 'image', 'question', 'choices', 'answer'],
#     num_rows: 100
# })
```

**The subsets used in our paper are available [here](https://huggingface.co/collections/shijianS01/templatematters-dataset-674f22fed0110c9d450624d2).**

### Model
We support the following models: 
- `ImageQAModel`: llavav1.5-7b, llavav1.5-13b, llavav1.6-7b, llavav1.6-13b, qwenvl-chat, qwenvl, idefics2-8b, internvl-chat-v1.5-24b

You can use our unified VQA interface for inference:

```python
from tm.qa_models import ImageQAModel, build_prompt_func
from tm.qa_datasets import SingleImageQADataset
import torch

vqa_model = ImageQAModel("llavav1.5-7b", enable_choice_search=True, torch_device=0, precision=torch.bfloat16)
tma = SingleImageQADataset("tma-subset").get_dataset()
test = tma[0]

result = vqa_model.multiple_choice_qa(
    image=test["image"],
    question=test["question"],
    choices=test["choices"],
    answer=test["answer"],
    prompt_func=build_prompt_func("Question: {question}\nSelect from the following choices: {choices}")
)
result

## Example Result
# {'prompt': 'Question: How many textile mat are there in the image?\nSelect from the following choices: (A) 8 (B) 5 (C) 4 (D) 1',
#  'free_form_answer': 'D',
#  'multiple_choice_answer': '1',
#  'answer': '4',
#  'accuracy': 0}
```

### Instruction Templates for Evaluation
The two instruction template sets used in our paper are available below:

[Simple](https://github.com/shijian2001/TemplateMatters/blob/main/templates/simple_templates.json): three commonly used simple templates

[Complex](https://github.com/shijian2001/TemplateMatters/blob/main/templates/complex_templates.json): 100 instruction templates randomly generated by our template generator

## Training

### Traing Resources
We trained five 7B and five 13B models based on LLaVA-1.5 resources. Follow [here](https://github.com/haotian-liu/LLaVA?tab=readme-ov-file#visual-instruction-tuning) to prepare your data and training scripts.

### Training Templates
You can prepare your training instruction templates like follows:

```python
from tm.template_generator import QuestionTemplateGenerator, generate_templates_set, assign_templates

# Generate 15000 templates and assign to all data
training_templates = assign_templates(
    num_data=665000, 
    templates_set=generate_templates_set(
        QuestionTemplateGenerator, 
        num_templates=15000
    )
)
print(len(training_templates))
# 665000
```
Then you should add the templates to the instruction part of your insturction-tuning dataset.

### Checkpoints
**The 10 model checkpoints involved in our paper can be found [here](https://huggingface.co/collections/shijianS01/templatematters-model-674dd4469a2382bb17bb3460).**

We also support these models, you can simply load the model as follows:
```python
from tm.qa_models import ImageQAModel
import torch

## 7b models
# llavav1.5-7b-100-templated, llavav1.5-7b-1k-templated, llavav1.5-7b-5k-templated, llavav1.5-7b-10k-templated, llavav1.5-7b-15k-templated

## 13b models
# llavav1.5-13b-100-templated, llavav1.5-13b-1k-templated, llavav1.5-13b-5k-templated, llavav1.5-13b-10k-templated, llavav1.5-13b-15k-templated

template_tuned_model = ImageQAModel("llavav1.5-7b-100-templated", enable_choice_search=True, torch_device=0, precision=torch.bfloat16)
```

### Evaluating the template-tuned models
We tested our tuned models on 100 generator-created templates ([Complex](https://github.com/shijian2001/TemplateMatters/blob/main/templates/complex_templates.json)), 3 common used templates ([Simple](https://github.com/shijian2001/TemplateMatters/blob/main/templates/simple_templates.json)), and 25 handwritten held-out templates available [here](https://github.com/shijian2001/TemplateMatters/blob/main/templates/heldout_templates.json).

## Contact
- Shijian Wang: shijian@seu.edu.cn