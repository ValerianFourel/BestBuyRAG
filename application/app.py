import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain.llms import HuggingFacePipeline
import torch
import gradio as gr
from datasets import load_dataset
import os

class BestBuyRAGChat:
    def __init__(self):
        self.qa_chain = None
        self.chat_history = []

    def prepare_data(self):
        try:
            # Load both datasets
            reviews_dataset = load_dataset(
                "ValerianFourel/bestbuy-reviews",
                token=os.environ.get("HF_TOKEN"),
                use_auth_token=True,
                trust_remote_code=True
            )

            products_dataset = load_dataset(
                "ValerianFourel/bestbuy-products",
                token=os.environ.get("HF_TOKEN"),
                use_auth_token=True,
                trust_remote_code=True
            )

            # Convert to pandas DataFrames
            reviews_df = reviews_dataset['train'].to_pandas()
            products_df = products_dataset['train'].to_pandas()

            # Merge datasets on product name
            merged_df = pd.merge(
                reviews_df,
                products_df[['name', 'price', 'brand', 'category']],
                left_on='product_name',
                right_on='name',
                how='left'
            )

            # Create combined text with all relevant information
            merged_df['combined_text'] = merged_df.apply(lambda x: f"""
            Product: {x['product_name']}
            Brand: {x['brand']}
            Price: ${x['price']}
            Category: {x['category']}
            Model: {x['product_model']}
            Rating: {x['rating']}
            Title: {x['review_title']}
            Review: {x['review_text']}
            Verified Purchase: {x['verified_purchase']}
            Helpful Votes: {x['helpful_count']}
            """, axis=1)

            return merged_df['combined_text'].tolist()
        except Exception as e:
            print(f"Error loading datasets: {str(e)}")
            return ["Sample product review text for testing"]

    def format_query(self, query, chat_history):
        context = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in chat_history[-3:]])
        return f"""Based on the provided product information and reviews:

        Previous conversation:
        {context}

        Current question: {query}

        Please provide a specific answer considering:
        - Product specifications and features
        - Price information
        - Brand details
        - User reviews and ratings
        - Any specific requirements mentioned in the question

        Focus on providing relevant information about phones that match the criteria."""

    # ... (rest of the methods remain the same as in your original code)

    def respond(self, message, chat_history):
        if self.qa_chain is None:
            return "System is still initializing. Please wait a moment and try again.", chat_history

        try:
            formatted_query = self.format_query(message, chat_history)
            response = self.qa_chain.invoke({
                "query": formatted_query,
                "context": "This is a phone recommendation system. Focus on providing relevant phone suggestions based on the user's requirements for functionality, price, or brand."
            })

            # Process the response to ensure it's focused on phone recommendations
            result = response['result']
            source_docs = response.get('source_documents', [])

            # Add source information if available
            if source_docs:
                relevant_info = "\n\nBased on reviews and product information from multiple sources."
                result += relevant_info

            chat_history.append((message, result))
            return "", chat_history
        except Exception as e:
            return f"Error: {str(e)}", chat_history
    
    def initialize_system(self):
        print("Initializing RAG system...")
        documents = self.prepare_data()
        texts = self.split_documents(documents)
        vectorstore = self.create_vectorstore(texts)
        llm = self.setup_llm()

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True  # Add this to get source documents in response
        
    )
    def setup_llm(self):
        try:
            # First check if we have the token
            token = os.environ.get("HF_TOKEN")
            if not token:
                raise ValueError("HF_TOKEN environment variable is not set")

            # Import required libraries
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch

            print("Loading model and tokenizer...")
            # Load model with explicit configurations
            model = AutoModelForCausalLM.from_pretrained(
                "meta-llama/Llama-2-7b-chat-hf",
                use_auth_token=token,
                torch_dtype=torch.float16,
                load_in_4bit=True,
                device_map="auto"
            )

            tokenizer = AutoTokenizer.from_pretrained(
                "meta-llama/Llama-2-7b-chat-hf",
                use_auth_token=token
            )

            print("Creating pipeline...")
            # Create the pipeline
            pipe = pipeline(
                task="text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

            print("Creating HuggingFacePipeline...")
            llm = HuggingFacePipeline(pipeline=pipe)

            if llm is None:
                raise ValueError("Failed to create HuggingFacePipeline")

            return llm

        except Exception as e:
            print(f"Critical error in setup_llm: {str(e)}")
            raise  # Re-raise the exception instead of returning None
    def create_vectorstore(self, texts):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        return FAISS.from_documents(texts, embeddings)
        
    def split_documents(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        return text_splitter.create_documents(documents)



def create_demo():
    rag_chat = BestBuyRAGChat()

    with gr.Blocks(css="footer {visibility: hidden}") as demo:
        gr.Markdown("""# BestBuy Product Review Assistant
        Ask questions about BestBuy products and their reviews""")

        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            bubble_full_width=False,
            avatar_images=(None, "assistant.png")
        )

        msg = gr.Textbox(
            show_label=False,
            placeholder="Ask about BestBuy products...",
            container=False
        )

        with gr.Row():
            clear = gr.Button("Clear")

        def clear_history():
            return [], []

        msg.submit(
            rag_chat.respond,
            [msg, chatbot],
            [msg, chatbot]
        )
        clear.click(clear_history, None, [chatbot, msg])

        demo.load(rag_chat.initialize_system)

    return demo

if __name__ == "__main__":
    demo = create_demo()
    # Let Gradio find an available port automatically
    demo.launch(server_name="0.0.0.0")
