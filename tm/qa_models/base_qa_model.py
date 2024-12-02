import random
from typing import Callable
import diskcache
import numpy as np
import sentence_transformers
import torch
import json

from .utils import make_options, check_contain


class QAModelInstance:
    def qa(self, data, prompt):
        "(Abstract method) abstract QA method"

    def batch_qa(self, data, prompt):
        "(Abstract method) abstract batch QA method"


class QAModel():
    def __init__(
        self,
        model_name: str,
        prompt_func: Callable,
        choice_format='letter',
        enable_choice_search: bool = False,
        cache_path: str = None,
    ):
        self.model = None
        self.model_name = model_name
        self.prompt_func = prompt_func
        self.format = choice_format
        self.cache_path = cache_path

        if self.cache_path is not None:
            print(
                f"[IMPORTANT] model cache is enabled, cache path: {cache_path}")
        else:
            print("[IMPORTANT] model cache is disabled")

        self.enable_choice_search = enable_choice_search
        # if enable_choice_search:
        # use SBERT to find the closest choice
        self.sentence_transformer = sentence_transformers.SentenceTransformer(
            "all-mpnet-base-v2", device='cpu')

    @torch.no_grad()
    def choice_search(self, free_form_answer, choices):
        query_embedding = self.sentence_transformer.encode([free_form_answer])
        choices_embedding = self.sentence_transformer.encode(choices)
        top_choice_index = np.argmax(
            np.dot(choices_embedding, query_embedding.T))
        return choices[top_choice_index]

    def _data_to_str(self, data):
        """ abstract method """

    @torch.no_grad()
    def _qa(self, data, prompt, batched=False):
        if self.cache_path is None:
            if batched:
                return self.model.batch_qa(data, prompt)
            else:
                return self.model.qa(data, prompt)
        else:
            with diskcache.Cache(self.cache_path, size_limit=10 * (2 ** 30)) as cache:
                key = json.dumps([self._data_to_str(data), prompt])
                response = cache.get(key, None)
                if response is None:
                    if batched:
                        response = self.model.batch_qa(data, prompt)
                    else:
                        response = self.model.qa(data, prompt)
                    cache.set(key, response)
                return response

    # TODO: Need update for direct QA
    @torch.no_grad()
    def qa(self, data, question, prompt_func=None):
        # prompt = prompt_func(question) if prompt_func else self.prompt_func(question)
        prompt = question
        return self._qa(data, prompt)

    def _limit_answer(self, free_form_answer, choices, prefix1, prefix2, options):
        # Limit the answer to the choices
        if free_form_answer in choices:
            multiple_choice_answer = free_form_answer
        elif free_form_answer in options:
            multiple_choice_answer = choices[options.index(free_form_answer)]
        elif free_form_answer in prefix1:
            multiple_choice_answer = choices[prefix1.index(free_form_answer)]
        elif free_form_answer in prefix2:
            multiple_choice_answer = choices[prefix2.index(free_form_answer)]
        elif self.enable_choice_search:
            multiple_choice_answer = self.choice_search(
                free_form_answer, choices)
        else:
            multiple_choice_answer = ""
            for to_check in [choices, options, prefix1, prefix2]:
                idx = check_contain(free_form_answer, to_check)
                if idx != -1:
                    multiple_choice_answer = choices[idx]
                    break
        return multiple_choice_answer

    @torch.no_grad()
    def multiple_choice_qa(self, data, question, choices, prompt_func=None, answer=None):
        # Get VQA model's answer
        prefix1, prefix2, options = make_options(choices, self.format)
        prompt = prompt_func(question, options) if prompt_func else self.prompt_func(
            question, options)
        free_form_answer = self._qa(data, prompt)
        free_form_answer = free_form_answer.strip()

        # Limit the answer to the choices
        multiple_choice_answer = self._limit_answer(
            free_form_answer, choices, prefix1, prefix2, options)

        result = {
            "free_form_answer": free_form_answer,
            "multiple_choice_answer": multiple_choice_answer,
            "choices": choices.copy(),
        }

        if answer is not None:
            result["accuracy"] = int(answer == multiple_choice_answer)
        return result

    @torch.no_grad()
    def multiple_choice_qa_random_ordering(self, data, question, choices, prompt_func=None, answer=None, n_trials=3):
        results = {}
        accuracy = 0
        for i in range(n_trials):
            choices_i = choices.copy()
            random.shuffle(choices_i)
            results[i] = self.multiple_choice_qa(
                data, question, choices_i, prompt_func, answer)
            accuracy += results[i]["accuracy"]
        results["accuracy"] = accuracy / n_trials
        return results