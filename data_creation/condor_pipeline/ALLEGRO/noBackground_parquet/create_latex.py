from pathlib import Path

# Folder containing your images
IMAGE_FOLDER = Path("../ALLEGRO/noBackground_parquet/output/comparison_out_sim_edm4hep_8_out_sim_edm4hep_12")

# Output LaTeX file
OUTPUT_FILE = Path("presentation.tex")

# Image extensions to include
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".pdf", ".eps", ".svg"
}


def escape_latex(text):
    """Escape characters that have special meaning in LaTeX."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    return "".join(replacements.get(char, char) for char in text)


# Start LaTeX document
latex = r"""\documentclass[aspectratio=169]{beamer}

\usepackage{graphicx}
\usepackage[T1]{fontenc}

\begin{document}
"""

# Find images
images = sorted(
    p for p in IMAGE_FOLDER.iterdir()
    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
)

# Create one slide per image
for image in images:
    # Filename without extension
    filename = image.stem

    # Escape special LaTeX characters for the caption
    caption = escape_latex(filename)

    # Path used by LaTeX
    image_path = image.as_posix()

    latex += rf"""
\begin{{frame}}
    \centering

    \includegraphics[
        width=0.9\textwidth,
        height=0.75\textheight,
        keepaspectratio
    ]{{{image_path}}}

    \vspace{{0.3cm}}

    {{\large\textbf{{{caption}}}}}

\end{{frame}}
"""

# Finish document
latex += r"""
\end{document}
"""

# Write the .tex file
OUTPUT_FILE.write_text(latex, encoding="utf-8")

print(f"Created: {OUTPUT_FILE}")
print(f"Number of images: {len(images)}")