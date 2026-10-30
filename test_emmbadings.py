import ollama


from app.llm import client, OPENAI_MODEL
MODEL_NAME = "embeddinggemma"

texts = [
    "الذكاء الاصطناعي يساعد الحواسيب على أداء مهام ذكية.",
    "تتعلم نماذج التعلم الآلي الأنماط من البيانات.",
    "الطبخ يحتاج إلى اختيار المكونات المناسبة.",
]

response = ollama.embed(
    model=MODEL_NAME,
    input=texts,
)

embeddings = response["embeddings"]

print("Number of texts:", len(texts))
print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))
print("First 5 values:", embeddings[0][:5])