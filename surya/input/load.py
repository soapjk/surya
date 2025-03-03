import PIL

from surya.input.processing import open_pdf, get_page_images
from surya.settings import settings
import os
import filetype
from PIL import Image
import json



def get_name_from_path(path):
    splited_names = list(os.path.basename(path).split("."))
    splited_names = splited_names[:-1]
    return "_".join(splited_names)


def load_pdf(pdf_path, max_pages=None, start_page=None, dpi=settings.IMAGE_DPI, load_text_lines=False, flatten_pdf=settings.FLATTEN_PDF):
    doc = open_pdf(pdf_path)
    last_page = len(doc)


    if start_page:
        assert start_page < last_page and start_page >= 0, f"Start page must be between 0 and {last_page}"
    else:
        start_page = 0

    if max_pages:
        assert max_pages >= 0, f"Max pages must be greater than 0"
        last_page = min(start_page + max_pages, last_page)

    page_indices = list(range(start_page, last_page))
    images = get_page_images(doc, page_indices, dpi=dpi)
    text_lines = [None] * len(page_indices)
    if load_text_lines:
        from surya.input.pdflines import get_page_text_lines # Putting import here because pypdfium2 causes warnings if its not the top import
        text_lines = get_page_text_lines(
            pdf_path,
            page_indices,
            [i.size for i in images],
            flatten_pdf=flatten_pdf
        )
    doc.close()
    names = [get_name_from_path(pdf_path) for _ in page_indices]
    return images, names, text_lines


def load_image(image_path):
    image = Image.open(image_path).convert("RGB")
    name = get_name_from_path(image_path)
    return [image], [name], [None]


def load_from_file(input_path, max_pages=None, start_page=None, dpi=settings.IMAGE_DPI, load_text_lines=False, flatten_pdf=settings.FLATTEN_PDF):
    input_type = filetype.guess(input_path)
    if input_type and input_type.extension == "pdf":
        return load_pdf(input_path, max_pages, start_page, dpi=dpi, load_text_lines=load_text_lines, flatten_pdf=flatten_pdf)
    else:
        return load_image(input_path)


def load_from_folder(folder_path, max_pages=None, start_page=None, dpi=settings.IMAGE_DPI, load_text_lines=False, flatten_pdf=settings.FLATTEN_PDF):
    image_paths = [os.path.join(folder_path, image_name) for image_name in os.listdir(folder_path) if not image_name.startswith(".")]
    image_paths = [ip for ip in image_paths if not os.path.isdir(ip)]

    images = []
    names = []
    text_lines = []
    for path in image_paths:
        extension = filetype.guess(path)
        if extension and extension.extension == "pdf":
            image, name, text_line = load_pdf(path, max_pages, start_page, dpi=dpi, load_text_lines=load_text_lines, flatten_pdf=flatten_pdf)
            images.extend(image)
            names.extend(name)
            text_lines.extend(text_line)
        else:
            try:
                image, name, text_line = load_image(path)
                images.extend(image)
                names.extend(name)
                text_lines.extend(text_line)
            except PIL.UnidentifiedImageError:
                print(f"Could not load image {path}")
                continue
    return images, names, text_lines


def load_lang_file(lang_path, names):
    with open(lang_path, "r") as f:
        lang_dict = json.load(f)
    return [lang_dict[name].copy() for name in names]
