import base64
from io import BytesIO
from typing import Dict

import googleapiclient
import matplotlib.pyplot as plt
import requests  # type: ignore
from google_images_search import GoogleImagesSearch
from llama_index.core.schema import Document, ImageDocument
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from PIL import Image

from ..utils.logger import setup_coloredlogs

logger = setup_coloredlogs(__name__)


class ImageSearchToolSpec(BaseToolSpec):
    """Google Image Search tool spec."""

    # you can provide API key and CX using arguments,
    # or you can set environment variables:
    # GCS_DEVELOPER_KEY, GCS_CX
    gis = GoogleImagesSearch(
        "AIzaSyB2yCoBmdwDBuPh3sRQLN4rVBlRVkYjJGg", "82c3bd6e8d6644a57"
    )
    spec_functions = ["image_search"]

    def __init__(self, search_params: Dict, search_kwargs: Dict | None = None):
        self._search_params = search_params
        self._search_kwargs = search_kwargs or {}

    def image_search(self, query: str):
        self._search_params["q"] = query
        try:
            self.gis.search(search_params=self._search_params, **self._search_kwargs)
        except googleapiclient.errors.HttpError as e:
            logger.info(e)
            return Document(text=f"Error: {e}")

        results = self.gis.results()

        # image_nodes = [
        #     ImageNode(image_url=result.url, metadata={"description": query})
        #     for result in results
        # ]
        image_nodes = []
        for result in results:
            url = result.url
            try:
                response = requests.get(url=url)
                img = Image.open(BytesIO(response.content))
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue())
                image_nodes.append(
                    ImageDocument(
                        image=img_b64, image_url=url, metadata={"description": query}
                    )
                )
            except OSError:
                print(f"Error: Could not open or display the image from {url}")

        return image_nodes


if __name__ == "__main__":
    # query = 'List of presidents of the United States from 2000'
    query = "Who is Elon Musk?"
    search_params = {
        # 'q': query,
        "num": 5,
        "fileType": "jpg|gif|png|bmp|svg|webp|ico",
        "rights": "cc_publicdomain|cc_attribute|cc_sharealike"
        "|cc_noncommercial|cc_nonderived",
        "safe": "off",
    }
    engine = ImageSearchToolSpec(search_params)

    # # this will only search for images:
    # gis.search(search_params=_search_params)

    # # this will search and download:
    # gis.search(search_params=_search_params, path_to_dir='/path/')

    # # this will search, download and resize:
    # gis.search(
    #     search_params=_search_params,
    #     path_to_dir='/path/', width=500, height=500
    # )

    urls = []
    # search first, then download and resize afterwards:
    results = engine.search(query=query)
    for image in results:
        print(type(image))
        url = image.image_url  # image direct url
        urls.append(url)

    print(urls)
    fig, axes = plt.subplots(1, 5, figsize=(20, 4))

    for ax, url in zip(axes, urls, strict=False):
        response = requests.get(url)
        try:
            img = Image.open(BytesIO(response.content))
        except OSError:
            print(f"Error: Could not open or display the image from {url}")
        # img = Image.open(BytesIO(response.content))
        ax.imshow(img)
        ax.axis("off")

    plt.show()
