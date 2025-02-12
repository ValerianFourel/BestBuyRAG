import os
import torch
import pandas as pd
from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class BestBuyRAGChat:
    def __init__(self):
        self.qa_chain = None
        self.chat_history = []

    def prepare_data(self):
        try:
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

            reviews_df = reviews_dataset['train'].to_pandas()
            products_df = products_dataset['train'].to_pandas()

            merged_df = pd.merge(
                reviews_df,
                products_df[['name', 'price', 'brand', 'category']],
                left_on='product_name',
                right_on='name',
                how='left'
            )

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

    def respond(self, message):
        if self.qa_chain is None:
            return "System is still initializing. Please wait a moment and try again."

        try:
            formatted_query = self.format_query(message, self.chat_history)
            response = self.qa_chain.invoke({
                "query": formatted_query,
                "context": "This is a phone recommendation system. Focus on providing relevant phone suggestions based on the user's requirements for functionality, price, or brand."
            })

            result = response['result']
            source_docs = response.get('source_documents', [])

            if source_docs:
                result += "\n\nBased on reviews and product information from multiple sources."

            self.chat_history.append((message, result))
            return result
        except Exception as e:
            return f"Error: {str(e)}"

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
            return_source_documents=True
        )
        print("System initialized and ready!")

    def setup_llm(self):
        try:
            token = os.environ.get("HF_TOKEN")
            if not token:
                raise ValueError("HF_TOKEN environment variable is not set")

            print("Loading model and tokenizer...")
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
            pipe = pipeline(
                task="text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=4096,
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
            raise

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

def extract_text(input_string):
    try:
        # Check if "Helpful Answer:" exists in the string
        if "Helpful Answer:" in input_string:
            start = input_string.find("Helpful Answer:") + len("Helpful Answer:")

            # Check if "Unhelpful" exists after "Helpful Answer:"
            if "Unhelpful" in input_string[start:]:
                end = input_string.find("Unhelpful")
                return input_string[start:end].strip()
            else:
                # If only "Helpful Answer:" exists, return everything after it
                return input_string[start:].strip()
        else:
            # If neither marker exists, return original string
            return input_string.strip()

    except Exception as e:
        return f"Error: {str(e)}"



def main():
    # Create and initialize the chat system
    chat_system = BestBuyRAGChat()
    chat_system.initialize_system()

    print("\nWelcome to BestBuy Product Review Assistant!")
    print("Type 'quit' or 'exit' to end the conversation.\n")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        if user_input:
            response = chat_system.respond(user_input)
            reduced_answer = extract_text(response) # we simply the answer to only get the most relevant
            print("\nAssistant:", reduced_answer)

if __name__ == "__main__":
    main()
