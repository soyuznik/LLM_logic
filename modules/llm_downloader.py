import os
import subprocess
import shutil
import time

class OllamaManager:
    def __init__(self, models_dir: str):
        self.models_dir = os.path.abspath(models_dir)
        os.makedirs(self.models_dir, exist_ok=True)

        # Set env var for this process
        os.environ["OLLAMA_MODELS"] = self.models_dir

    def is_ollama_running(self) -> bool:
        try:
            subprocess.run(
                ["ollama", "list"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            raise RuntimeError("Ollama not installed or not in PATH")

    def pull(self, model: str):
        print(f"Pulling {model} into {self.models_dir}")
        subprocess.run(
            ["ollama", "pull", model],
            check=True,
            env=os.environ,
        )

    def list_models(self):
        subprocess.run(["ollama", "list"], check=True)
