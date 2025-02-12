



# BestBuy Product Review Assistant

This is a Retrieval-Augmented Generation (RAG) chatbot that helps users query and get insights about BestBuy products and their reviews. The system uses two custom datasets containing product information and customer reviews to provide informed responses to user queries.

## 🚀 Features

- Interactive chat interface
- Real-time product and review information retrieval
- Context-aware responses based on previous conversation
- Support for detailed product queries and review analysis

## 📊 Datasets

This application uses two custom datasets hosted on Hugging Face:

1. **BestBuy Reviews Dataset** (`ValerianFourel/bestbuy-reviews`)
   - Contains customer reviews and ratings
   - Includes review text, ratings, helpful votes, and verification status

2. **BestBuy Products Dataset** (`ValerianFourel/bestbuy-products`)
   - Contains product information
   - Includes product names, models, prices, and other details

## 🛠️ Technical Stack

- **Framework**: Gradio
- **Language Models**: LLaMA-3.1-8B-Instruct
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS
- **Text Processing**: LangChain

## 💻 Requirements
I'll help you create a comprehensive README.md file for your BestBuy RAG Chat Space:


Markdown
# BestBuy Product Review Assistant

This is a Retrieval-Augmented Generation (RAG) chatbot that helps users query and get insights about BestBuy products and their reviews. The system uses two custom datasets containing product information and customer reviews to provide informed responses to user queries.

## 🚀 Features

- Interactive chat interface
- Real-time product and review information retrieval
- Context-aware responses based on previous conversation
- Support for detailed product queries and review analysis

## 📊 Datasets

This application uses two custom datasets hosted on Hugging Face:

1. **BestBuy Reviews Dataset** (`ValerianFourel/bestbuy-reviews`)
   - Contains customer reviews and ratings
   - Includes review text, ratings, helpful votes, and verification status

2. **BestBuy Products Dataset** (`ValerianFourel/bestbuy-products`)
   - Contains product information
   - Includes product names, models, prices, and other details

## 🛠️ Technical Stack

- **Framework**: Gradio
- **Language Models**: LLaMA-3.1-8B-Instruct
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS
- **Text Processing**: LangChain

## 💻 Requirements
txt
gradio
torch
transformers
langchain
faiss-cpu
pandas
datasets
sentence-transformers


## 🤝 Usage

Simply type your question about BestBuy products or reviews in the text input box. The assistant will provide relevant information based on the available data. You can ask about:

- Product details
- Customer reviews
- Ratings and recommendations
- Product comparisons
- Common issues or praise points

## 🔒 Environment Variables

The following environment variables are required:
- `HF_TOKEN`: Your Hugging Face API token for accessing models
- `CUDA_VISIBLE_DEVICES`: GPU configuration (default: "0")

## 📝 Example Queries

- "What are the most common complaints about [product]?"
- "What features do customers like most about [product]?"
- "How does [product A] compare to [product B] in terms of customer satisfaction?"
- "What's the average rating for [product]?"

## ⚠️ Limitations

- Responses are based on available review data only
- Processing time may vary based on query complexity
- Limited to BestBuy product catalog and reviews in the dataset

## 🤗 Credits

Built with [Hugging Face](https://huggingface.co/) technologies and hosted on Hugging Face Spaces


Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
