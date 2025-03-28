# Retrieval Augmented Generation for Health Education

### Abstract

The integration of large language models (LLMs) in medical education remains controversial due to concerns regarding the accuracy and reliability of generated information. The risk of disseminating incorrect information presents a barrier to their widespread adoption among students. Advanced technologies, including AI-driven chatbots, have the potential to accelerate student mastery of medical content by providing accessible, interactive learning resources. Thus, there is a critical need for the development of trustworthy, AI-based educational tools in this space. This project aims to develop an educational Medical Q&A Assistant that provides evidence-based medical knowledge, ensuring reliable learning for healthcare professionals. Our methodology involves collecting and preprocessing data from reputable medical resources, including public health guidelines, peer-reviewed research, and textbooks and encyclopedias. These resources will be pulled directly from the curriculum of a medical school class as a proof of concept. To ensure transparency and mitigate misinformation, the Q&A chatbot will include a disclaimer stating that the information is current as of a specific date and is intended as an educational tool for healthcare professionals. Sources will be cited on all responses. Ideally this RAG LLM can be used as a template for creating program specific LLMs.

## Developers

### Set Up

- Create a folder for the project locally and create a venv

- Start by pulling the code into your local repo and change into the remote main branch.

- Place raw data within the "data" folder.

- Install dependencies

  - Through pip
    ```
    pip install -r requirements.txt
    ```

- Run pipeline with the following

  ```
  python pipline.py
  ```

  - Note the above will run with cleaning all the data. Once you do this once, you probably don't want to do that again. So you can do this:

  ```
  python pipeline.py --clean_data=False
  ```

  - The same goes for vectorizing you can avoid doing that like this (if you've done it already it will be saved to the vectorized_data folder in a json file)

  ```
  python pipeline.py --clean_data=False --vectorize_data=False
  ```
