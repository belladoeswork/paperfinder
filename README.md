# PaperFinder

PaperFinder is an application that allows you to search, find and interact with scientific papers from the arXiv repository. With a user-friendly interface, you can easily browse search results, view detailed information about each paper, generate summaries, and engage in discussions about the paper.


## Features

- Search for Papers: Enter a query to retrieve papers from the arXiv repository.
- View Paper Details: Click on a paper to see detailed information, including authors, publication date, abstract, citations, and PDF link.
- Generate Summaries: Automatically generate a concise summary of the paper using OpenAI.
- View Citations: Generate citations in various formats (APA, MLA, Chicago, etc.) and copy them easily.
- Read PDF: View the PDF of the paper directly within the app.
- Chat About the Paper: Ask questions and get responses based on the paper content.

## Demo

https://github.com/user-attachments/assets/5e0669b3-6b1d-413a-ad16-bb5aa7cabbe3

https://github.com/user-attachments/assets/5e71898d-5f7a-4f01-93c0-451d76409326


## Installation

1. Clone the repository:
```bash
git clone https://github.com/belladoeswork/paperfinder.git
cd paperfinder

```
2. Install required packages
```bash
pip install -r requirements.txt

```
3. Set-up environment variables
```bash
ASTRA_DB_APPLICATION_TOKEN="your_key"
ASTRA_DB_API_ENDPOINT="your_key"
OPENAI_API_KEY="your_key"

```
4. Run the Streamlit app
```bash
streamlit run app.py

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
