from typing import Any

import typer
from rich import print as rich_print
from rich.rule import Rule

import keyboard  # Import the keyboard library


from ..role import DefaultRoles, SystemRole
from ..utils import run_command
from .chat_handler import ChatHandler
from .default_handler import DefaultHandler

import sgpt.handlers.shared_state

class ReplHandler(ChatHandler):
    def __init__(self, chat_id: str, role: SystemRole) -> None:
        super().__init__(chat_id, role)
        self.is_esc_pressed = False  # Flag to monitor ESC key press


    @classmethod
    def _get_multiline_input(cls) -> str:
        multiline_input = ""
        while (user_input := typer.prompt("...", prompt_suffix="")) != '"""':
            multiline_input += user_input + "\n"
        return multiline_input

    def handle(self, init_prompt: str, **kwargs: Any) -> None:  # type: ignore
        # Function to handle ESC key press
        def on_esc_press(event):
            self.is_esc_pressed = True
            sgpt.handlers.shared_state.stop_generation = True

        esc_hook = keyboard.on_press_key("esc", on_esc_press)

        try:
            while True:
                if self.is_esc_pressed:
                    # Reset flag and exit the loop to return to the REPL prompt
                    self.is_esc_pressed = False
                    break
                # Your existing loop content here
                if self.initiated:
                    rich_print(Rule(title="Chat History", style="bold magenta"))
                    self.show_messages(self.chat_id)
                    rich_print(Rule(style="bold magenta"))

                info_message = (
                    "Entering REPL mode, press Ctrl+C to exit."
                    if not self.role.name == DefaultRoles.SHELL.value
                    else (
                        "Entering shell REPL mode, type [e] to execute commands "
                        "or [d] to describe the commands, press Ctrl+C to exit."
                    )
                )
                typer.secho(info_message, fg="yellow")

                if init_prompt:
                    rich_print(Rule(title="Input", style="bold purple"))
                    typer.echo(init_prompt)
                    rich_print(Rule(style="bold purple"))

                full_completion = ""
                while True:
                    # sgpt.handlers.shared_state.stop_generation = False
                    # Infinite loop until user exits with Ctrl+C.
                    prompt = typer.prompt(">>>", prompt_suffix=" ")
                    if prompt == '"""':
                        prompt = self._get_multiline_input()
                    if prompt == "exit()" or prompt == "exit":
                        raise typer.Exit()
                    if init_prompt:
                        prompt = f"{init_prompt}\n\n\n{prompt}"
                        init_prompt = ""
                    if self.role.name == DefaultRoles.SHELL.value and prompt == "e":
                        typer.echo()
                        run_command(full_completion)
                        typer.echo()
                        rich_print(Rule(style="bold magenta"))
                    elif self.role.name == DefaultRoles.SHELL.value and prompt == "d":
                        DefaultHandler(DefaultRoles.DESCRIBE_SHELL.get_role()).handle(
                            prompt=full_completion, **kwargs
                        )
                    else:
                        full_completion = super().handle(prompt=prompt, **kwargs)
                    sgpt.handlers.shared_state.stop_generation = False
        finally:
            # Correctly remove the hook using the hook object
            keyboard.unhook(esc_hook)
