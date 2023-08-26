import re
import traceback
from io import StringIO
import contextlib
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    import matplotlib.pyplot as plt

    PLT_IS_AVAILABLE = True
except ModuleNotFoundError:
    PLT_IS_AVAILABLE = False
    logger.warning(
        "⚠ Warning: 'matplotlib' is not installed. Plotting inside code "
        "blocks won't be available"
    )


def execute_python_code(code_block):
    """
    Executes Python code and captures its output or errors.
    Also saves any plot generated by plt.show().
    """
    output = StringIO()
    error_message = ""

    with contextlib.redirect_stdout(output):
        try:
            exec(code_block, globals())
        except Exception:
            error_message = traceback.format_exc()

    return output.getvalue(), error_message


def compile_pymd(input_file, output_file):
    """
    Compiles the pymd file by executing Python code blocks and
    adding their output or errors (and saved plots) below the respective code blocks.
    """
    try:
        with open(input_file, "r") as f:
            content = f.read()

        python_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
        if not python_blocks:
            logger.warning("⚠ No Python code blocks found in the input file.")
            return

        output_content = content

        if PLT_IS_AVAILABLE:

            def save_plot_and_close(*args, **kwargs):
                nonlocal plot_string
                if plt.gcf()._suptitle is not None:
                    fig_title = plt.gcf()._suptitle.get_text()
                else:
                    fig_title = plt.gca().get_title()
                plot_name = f"{fig_title}.png"
                plot_folder = "plots"
                if not os.path.exists(plot_folder):
                    os.makedirs(plot_folder)
                saved_plot_path = os.path.join(plot_folder, plot_name)
                plt.savefig(saved_plot_path)
                plt.close()
                plot_string += f"\n![{fig_title}]({saved_plot_path})"

            plt.show = save_plot_and_close

        for code_block in python_blocks:
            plot_string = ""
            silent_mode = None
            if "#silent*input" in code_block:
                silent_mode = "input"
            elif "#silent*output" in code_block:
                silent_mode = "output"

            output, error_message = execute_python_code(code_block)
            if any(c.strip() for c in output) or any(c.strip() for c in error_message):
                output_block = f"```\n{output}{error_message}```"
            else:
                output_block = ""

            if silent_mode == "output":
                output_content = output_content.replace(
                    f"```python{code_block}```", f"```python{code_block}```"
                )
            elif silent_mode == "input":
                output_content = output_content.replace(
                    f"```python{code_block}```", f"{output_block}{plot_string}"
                )
            else:
                output_content = output_content.replace(
                    f"```python{code_block}```",
                    f"```python{code_block}```\n{output_block}{plot_string}",
                )

        with open(output_file, "w") as f:
            f.write(output_content)

        logger.info("✔ Compilation successful. Output written to %s", output_file)

    except FileNotFoundError:
        logger.error("✖ Error: Input file not found.")
    except Exception as e:
        logger.error("✖ Error: %s", str(e))
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Compile pymd files")
    parser.add_argument("input_file", help="Input .pymd file")
    args = parser.parse_args()

    input_file = args.input_file
    if not input_file.endswith(".pymd"):
        logger.error("✖ Error: Input file must have the '.pymd' extension.")
    else:
        output_file = input_file.replace(".pymd", ".md")
        compile_pymd(input_file, output_file)


if __name__ == "__main__":
    main()
