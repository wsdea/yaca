import os

from jinja2 import Environment, StrictUndefined

from .read_files import read_file


class PromptLoader:
    def __init__(self, prompt_folder=None):
        """
        Initializes the PromptLoader.

        Args:
            prompt_folder (str, optional): Directory containing prompt templates.
                Defaults to the directory of this file.
        """
        self.prompt_folder = prompt_folder or os.path.dirname(__file__)

    def load_prompt(self, name: str):
        """
        Loads a prompt template file into ``self.template_str``.
        The ``name`` may be given with or without the ``.txt`` suffix.
        """
        name = name.removesuffix(".txt") + ".txt"
        file_path = os.path.join(self.prompt_folder, name)
        try:
            self.template_str = read_file(file_path)
        except FileNotFoundError:
            raise Exception(f"Unknown prompt file {name}")

    def __call__(self, prompt, **kwargs):
        prompt = self.load_prompt(prompt)
        env = Environment(undefined=StrictUndefined)
        template = env.from_string(self.template_str)
        try:
            return template.render(**kwargs)
        except Exception as e:
            raise ValueError(f"Error rendering prompt: {e}")
